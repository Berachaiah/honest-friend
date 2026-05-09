from django.urls import path, include

urlpatterns = [
    path('', include('task_a.urls', namespace='task_a')),
    path('api/task-a/', include('task_a.urls', namespace='task_a_api')),
    path('api/task-b/', include('task_b.urls')),
]
