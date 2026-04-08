from django.shortcuts import render, redirect
from django.http import HttpResponse
from bson.objectid import ObjectId
from pymongo.errors import ServerSelectionTimeoutError
from .db import collection
import re


# -------------------------
# LOGIN VIEW
# -------------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Simple demo login
        if username == 'admin' and password == 'admin123':
            request.session['username'] = username
            return redirect('/home/')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})

    return render(request, 'login.html')


# -------------------------
# LOGOUT VIEW
# -------------------------
def logout_view(request):
    request.session.flush()
    return redirect('/login/')


# -------------------------
# HOME PAGE (PROTECTED)
# -------------------------
def home(request):
    username = request.session.get('username')

    if not username:
        return redirect('/login/')

    return render(request, 'home.html', {
        'username': username,
        'login_message': 'Login successful!'
    })


# -------------------------
# ADD STUDENT (PROTECTED)
# -------------------------
def student_form(request):
    if not request.session.get('username'):
        return redirect('/login/')

    if request.method == 'POST':
        name = request.POST.get('name')
        department = request.POST.get('department')
        age = request.POST.get('age')
        roll_no = request.POST.get('roll_no')
        email = request.POST.get('email')
        if not re.fullmatch(r"^[a-z0-9]+@gmail\.com$",email):
            return HttpResponse("Invalid email! Email must end with @gmail.com")
        
        data = {
            "name": name,
            "department": department,
            "age": age,
            "roll_no": roll_no,
            "email": email
        }

        try:
            collection.insert_one(data)
            return redirect('/success/')
        except ServerSelectionTimeoutError:
            return HttpResponse("MongoDB is not running. Please start MongoDB server and try again.")

    return render(request, 'form.html')


# -------------------------
# SUCCESS PAGE (PROTECTED)
# -------------------------
def success_page(request):
    if not request.session.get('username'):
        return redirect('/login/')

    return render(request, 'success.html')


# -------------------------
# STUDENT LIST (PROTECTED)
# -------------------------
def student_list(request):
    if not request.session.get('username'):
        return redirect('/login/')

    try:
        students_data = []

        for student in collection.find():
            students_data.append({
                'id': str(student['_id']),
                'name': student.get('name'),
                'department': student.get('department'),
                'age': student.get('age'),
                'roll_no': student.get('roll_no'),
                'email': student.get('email')

            })

        return render(request, 'list.html', {'students': students_data})

    except ServerSelectionTimeoutError:
        return HttpResponse("MongoDB is not running. Please start MongoDB server to view student records.")


# -------------------------
# EDIT STUDENT (PROTECTED)
# -------------------------
def edit_student(request, id):
    if not request.session.get('username'):
        return redirect('/login/')

    try:
        student = collection.find_one({"_id": ObjectId(id)})

        if request.method == 'POST':
            name = request.POST.get('name')
            department = request.POST.get('department')
            age = request.POST.get('age')
            roll_no = request.POST.get('roll_no')
            email = request.POST.get('email')
            if not re.fullmatch(r"^[a-z0-9]+@gmail\.com$",email):
                return HttpResponse("Invalid email! Email must end with @gmail.com")


            collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": {"name": name, "age": age, "department": department, "roll_no": roll_no, "email": email}}
            )

            return redirect('/students/')

        student_data = {
            'id': str(student['_id']),
            'name': student.get('name'),
            'department': student.get('department'),
            'age': student.get('age'),
            'roll_no': student.get('roll_no'),
            'email': student.get('email')
            
        }

        return render(request, 'edit.html', {'student': student_data})

    except ServerSelectionTimeoutError:
        return HttpResponse("MongoDB is not running. Please start MongoDB server to edit student records.")


# -------------------------
# DELETE STUDENT (PROTECTED)
# -------------------------
def delete_student(request, id):
    if not request.session.get('username'):
        return redirect('/login/')

    try:
        collection.delete_one({"_id": ObjectId(id)})
        return redirect('/students/')
    except ServerSelectionTimeoutError:
        return HttpResponse("MongoDB is not running. Please start MongoDB server to delete student records.")