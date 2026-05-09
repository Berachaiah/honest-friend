from django.urls import path, include

urlpatterns = [
    path('', include('task_a.urls')),
    path('api/task-a/', include('task_a.urls')),
    path('api/task-b/', include('task_b.urls')),
]
