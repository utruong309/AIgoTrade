from django.urls import path
from . import auth_views

urlpatterns = [
    path('register/', auth_views.register, name='auth_register'),
    path('login/', auth_views.login, name='auth_login'),
    path('logout/', auth_views.logout, name='auth_logout'),
    path('profile/', auth_views.profile, name='auth_profile'),
]