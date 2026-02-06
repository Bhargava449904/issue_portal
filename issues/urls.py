from django.urls import path
from . import views

urlpatterns=[
    path("hello/",view=views.hello),
    path("create_issue/",view=views.create_issue),
    path("view_my_issues/",view=views.view_my_issues),
    path("user_get_issues/",view=views.user_get_issues),
    path("admin_view_all_issues/",view=views.admin_view_all_issues),
    path("admin_update_issue_status/<int:issue_id>/",view=views.admin_update_issue_status),
    path("admin_delete_issue/<int:issue_id>",view=views.admin_delete_issue),
    
]