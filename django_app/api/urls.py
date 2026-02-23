"""
Growvity API URL Configuration - Simplified
"""
from django.urls import path
from . import views


urlpatterns = [
    # API Root
    path('', views.ApiRootView.as_view(), name='api-root'),
    
    # Building endpoints (simplified - no hierarchy)
    path('buildings/', views.BuildingListView.as_view(), name='building-list'),
    path('buildings/<str:uid>/', views.BuildingDetailView.as_view(), name='building-detail'),
    path('buildings/<str:uid>/recompute/', views.BuildingRecomputeView.as_view(), name='building-recompute'),
    
    # Project endpoints (Synthetic)
    path('projects/', views.ProjectListView.as_view(), name='project-list'),
    path('projects/<str:uid>/tree/', views.ProjectTreeView.as_view(), name='project-tree'),
]
