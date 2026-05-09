from django.urls import path
from . import views

app_name = 'task_b'

urlpatterns = [
    path('recommend/', views.recommend_view, name='recommend'),
    path('api/recommend/', views.RecommendAPIView.as_view(), name='api_recommend'),
]
