from django.contrib import admin
from django.urls import path
from myapp.views import (
    login_view,
    logout_view,
    home,
    student_form,
    success_page,
    student_list,
    edit_student,
    delete_student
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', login_view),
    path('login/', login_view),
    path('logout/', logout_view),

    path('home/', home),
    path('form/', student_form),
    path('success/', success_page),
    path('students/', student_list),
    path('edit/<str:id>/', edit_student),
    path('delete/<str:id>/', delete_student),
]