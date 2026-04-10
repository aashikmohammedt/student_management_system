from django.shortcuts import render, redirect
from django.contrib import messages
from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo.errors import ServerSelectionTimeoutError
from .db import students_collection, users_collection
from werkzeug.security import generate_password_hash, check_password_hash
import re

# =========================================
# CONSTANTS
# =========================================
SESSION_USER_KEY = "username"
GMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@gmail\.com$"

# =========================================
# HELPER FUNCTIONS
# =========================================
def is_logged_in(request):
    return bool(request.session.get(SESSION_USER_KEY))


def get_logged_in_username(request):
    return request.session.get(SESSION_USER_KEY)


def require_login(request):
    if not is_logged_in(request):
        messages.error(request, "Please sign in to continue.")
        return redirect("login")
    return None


def base_context(request, extra=None):
    context = {
        "username": get_logged_in_username(request)
    }
    if extra:
        context.update(extra)
    return context


def serialize_student(student):
    return {
        "id": str(student["_id"]),
        "name": student.get("name", ""),
        "department": student.get("department", ""),
        "age": student.get("age", ""),
        "roll_no": student.get("roll_no", ""),
        "email": student.get("email", ""),
    }


def validate_gmail(email):
    return bool(re.fullmatch(GMAIL_REGEX, email))


def build_student_payload(request):
    return {
        "name": request.POST.get("name", "").strip().title(),
        "department": request.POST.get("department", "").strip(),
        "age": request.POST.get("age", "").strip(),
        "roll_no": request.POST.get("roll_no", "").strip(),
        "email": request.POST.get("email", "").strip().lower(),
    }


def validate_student_data(student_data):
    if not all([
        student_data["name"],
        student_data["department"],
        student_data["age"],
        student_data["roll_no"],
        student_data["email"],
    ]):
        return "All student fields are required."

    if not validate_gmail(student_data["email"]):
        return "Invalid email! Email must end with @gmail.com"

    if not student_data["age"].isdigit():
        return "Age must be a valid number."

    age = int(student_data["age"])
    if age < 15 or age > 100:
        return "Age must be between 15 and 100."

    return None


def handle_db_error(request, fallback_route, custom_message=None):
    messages.error(
        request,
        custom_message or "Database connection issue. Please try again later."
    )
    return redirect(fallback_route)


# =========================================
# SIGN UP VIEW
# =========================================
def signup_view(request):
    if is_logged_in(request):
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        form_data = {
            "username": username,
            "email": email,
        }

        if not username or not email or not password or not confirm_password:
            return render(request, "signup.html", {
                "error": "All fields are required.",
                "form_data": form_data
            })

        if not validate_gmail(email):
            return render(request, "signup.html", {
                "error": "Email must be a valid @gmail.com address.",
                "form_data": form_data
            })

        if len(password) < 6:
            return render(request, "signup.html", {
                "error": "Password must be at least 6 characters.",
                "form_data": form_data
            })

        if password != confirm_password:
            return render(request, "signup.html", {
                "error": "Passwords do not match.",
                "form_data": form_data
            })

        try:
            existing_user = users_collection.find_one({
                "$or": [
                    {"username": username},
                    {"email": email}
                ]
            })

            if existing_user:
                return render(request, "signup.html", {
                    "error": "Username or email already exists.",
                    "form_data": form_data
                })

            hashed_password = generate_password_hash(password)

            users_collection.insert_one({
                "username": username,
                "email": email,
                "password": hashed_password
            })

            messages.success(request, "Account created successfully! Please sign in.")
            return redirect("login")

        except ServerSelectionTimeoutError:
            return handle_db_error(
                request,
                "signup",
                "Database connection issue while creating account."
            )

    return render(request, "signup.html", {"form_data": {}})


# =========================================
# LOGIN VIEW
# =========================================
def login_view(request):
    if is_logged_in(request):
        return redirect("home")

    if request.method == "POST":
        username_or_email = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        try:
            user = users_collection.find_one({
                "$or": [
                    {"username": username_or_email},
                    {"email": username_or_email.lower()}
                ]
            })

            if user and check_password_hash(user["password"], password):
                request.session[SESSION_USER_KEY] = user["username"]
                request.session.set_expiry(3600)
                request.session.modified = True
                messages.success(request, f"Welcome back, {user['username']}!")
                return redirect("home")

            return render(request, "login.html", {
                "error": "Invalid username/email or password"
            })

        except ServerSelectionTimeoutError:
            return handle_db_error(
                request,
                "login",
                "Database connection issue while signing in."
            )

    return render(request, "login.html")


# =========================================
# LOGOUT VIEW
# =========================================
def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


# =========================================
# HOME PAGE
# =========================================
def home(request):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    return render(
        request,
        "home.html",
        base_context(request)
    )


# =========================================
# ADD STUDENT
# =========================================
def student_form(request):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    if request.method == "POST":
        student_data = build_student_payload(request)

        validation_error = validate_student_data(student_data)
        if validation_error:
            return render(
                request,
                "form.html",
                base_context(request, {
                    "error": validation_error,
                    "form_data": student_data
                })
            )

        try:
            existing_student = students_collection.find_one({"roll_no": student_data["roll_no"]})
            if existing_student:
                return render(
                    request,
                    "form.html",
                    base_context(request, {
                        "error": "Roll number already exists. Please use a unique roll number.",
                        "form_data": student_data
                    })
                )

            student_data["age"] = int(student_data["age"])

            students_collection.insert_one(student_data)
            messages.success(request, "Student added successfully!")
            return redirect("student_list")

        except ServerSelectionTimeoutError:
            return handle_db_error(
                request,
                "student_form",
                "Database connection issue while adding student."
            )


    return render(request, "form.html", base_context(request, {"form_data": {}}))


# =========================================
# STUDENT LIST
# =========================================
def student_list(request):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    search_query = request.GET.get("search", "").strip()

    try:
        if search_query:
            safe_query = re.escape(search_query)
            students_cursor = students_collection.find({
                "name": {
                    "$regex": safe_query,
                    "$options": "i"
                }
            }).sort("name", 1)
        else:
            students_cursor = students_collection.find().sort("name", 1)

        students_data = [serialize_student(student) for student in students_cursor]

        return render(
            request,
            "list.html",
            base_context(request, {
                "students": students_data,
                "search_query": search_query
            })
        )

    except ServerSelectionTimeoutError:
        return handle_db_error(
            request,
            "home",
            "Database connection issue while loading student records."
        )


# =========================================
# EDIT STUDENT
# =========================================
def edit_student(request, id):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    try:
        student = students_collection.find_one({"_id": ObjectId(id)})

        if not student:
            messages.error(request, "Student record not found.")
            return redirect("student_list")

        if request.method == "POST":
            updated_data = build_student_payload(request)

            validation_error = validate_student_data(updated_data)
            if validation_error:
                return render(
                    request,
                    "edit.html",
                    base_context(request, {
                        "error": validation_error,
                        "student": {
                            "id": id,
                            **updated_data
                        }
                    })
                )

            existing_student = students_collection.find_one({
                "roll_no": updated_data["roll_no"],
                "_id": {"$ne": ObjectId(id)}
            })

            if existing_student:
                return render(
                    request,
                    "edit.html",
                    base_context(request, {
                        "error": "Roll number already exists. Please use a unique roll number.",
                        "student": {
                            "id": id,
                            **updated_data
                        }
                    })
                )

            updated_data["age"] = int(updated_data["age"])

            students_collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": updated_data}
            )

            messages.success(request, "Student updated successfully!")
            return redirect("student_list")

        return render(
            request,
            "edit.html",
            base_context(request, {
                "student": serialize_student(student)
            })
        )

    except ServerSelectionTimeoutError:
        return handle_db_error(
            request,
            "student_list",
            "Database connection issue while editing student."
        )
    except InvalidId:
        messages.error(request, "Invalid student ID.")
        return redirect("student_list")
    except Exception:
        messages.error(request, "Unexpected error while editing student.")
        return redirect("student_list")


# =========================================
# DELETE CONFIRM PAGE
# =========================================
def delete_confirm(request, id):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    try:
        student = students_collection.find_one({"_id": ObjectId(id)})

        if not student:
            messages.error(request, "Student record not found.")
            return redirect("student_list")

        return render(
            request,
            "delete_confirm.html",
            base_context(request, {
                "student": serialize_student(student)
            })
        )

    except ServerSelectionTimeoutError:
        return handle_db_error(
            request,
            "student_list",
            "Database connection issue while loading delete confirmation."
        )
    except InvalidId:
        messages.error(request, "Invalid student ID.")
        return redirect("student_list")
    except Exception:
        messages.error(request, "Unexpected error while loading delete confirmation.")
        return redirect("student_list")


# =========================================
# DELETE STUDENT (POST ONLY)
# =========================================
def delete_student(request, id):
    auth_redirect = require_login(request)
    if auth_redirect:
        return auth_redirect

    if request.method != "POST":
        messages.error(request, "Invalid delete request.")
        return redirect("student_list")

    try:
        result = students_collection.delete_one({"_id": ObjectId(id)})

        if result.deleted_count == 0:
            messages.error(request, "Student record not found.")
            return redirect("student_list")

        messages.success(request, "Student deleted successfully!")
        return redirect("student_list")

    except ServerSelectionTimeoutError:
        return handle_db_error(
            request,
            "student_list",
            "Database connection issue while deleting student."
        )
    except InvalidId:
        messages.error(request, "Invalid student ID.")
        return redirect("student_list")
    except Exception:
        messages.error(request, "Unexpected error while deleting student.")
        return redirect("student_list")