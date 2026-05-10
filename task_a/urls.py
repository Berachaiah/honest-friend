from django.urls import path
from . import views

app_name = 'task_a'

urlpatterns = [
    path('', views.index, name='index'),
    path('generate/', views.generate_review_view, name='generate'),
    path('api/generate/', views.GenerateReviewAPIView.as_view(), name='api_generate'),
    path('cold-start/', views.cold_start_view, name='cold_start'),
]
