from django.urls import path
from . import views

urlpatterns=[
    path("welcome/",view=views.welcome),
    path("register/",view=views.register),
    path("login/",view=views.login),
    path("super_admin_create_admin/",view=views.super_admin_create_admin),
    path("super_admin_view_admins/",view=views.super_admin_view_admins),
    path("super_admin_delete_admin/",view=views.super_admin_delete_admin),
]