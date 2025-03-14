from django.urls import path
from . import views


urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/new/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', views.task_update, name='task_update'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    
    # Changes
    # Sharing tasks
    path("tasks/<int:task_id>/share/", views.share_task, name="share_task"),
    path("tasks/<int:task_id>/shared_users/", views.get_shared_users, name="shared_users"),
    path("tasks/<int:task_id>/add_user/", views.add_shared_user, name="add_user"),
    path("tasks/<int:task_id>/remove_user/", views.remove_shared_user, name="remove_user"),
    path("tasks/<int:task_id>/update_status/", views.update_task_status, name="update_status"),
    path("notifications/", views.get_notifications, name="get_notifications"),

    # Missing Route (Added Now)
    path("tasks/shared/", views.get_shared_tasks, name="shared_tasks"),
    
    path("analytics/overview/", views.task_overview, name="task_overview"),
    path("analytics/trends/", views.task_trends, name="task_trends"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("analytics/trends/graph/", views.task_trends_graph, name="task_trends_graph"),
    path("analytics/trends/graph/", views.weekly_task_completion_trends, name="weekly_task_completion_trends"),
    path("analytics/trends/graph/", views.monthly_task_creation_trends, name="monthly_task_creation_trends"),
    path("analytics/trends/graph/", views.task_status_distribution, name="task_status_distribution"),
    path("analytics/trends/graph/", views.overdue_tasks, name="overdue_tasks"),
]
