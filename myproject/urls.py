from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from myapp.views import (
    signup_view,
    login_view,
    logout_view,
    home,
    student_form,
    student_list,
    edit_student,
    delete_confirm,
    delete_student,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Authentication
    path("", login_view, name="root_login"),
    path("signup/", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Dashboard
    path("home/", home, name="home"),

    # Student CRUD
    path("form/", student_form, name="student_form"),
    path("students/", student_list, name="student_list"),
    path("edit/<str:id>/", edit_student, name="edit_student"),
    path("delete-confirm/<str:id>/", delete_confirm, name="delete_confirm"),
    path("delete/<str:id>/", delete_student, name="delete_student"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATICFILES_DIRS[0]
    )