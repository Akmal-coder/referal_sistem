from django.urls import path
from . import views

urlpatterns = [
    # API
    path('auth/send-code/', views.send_code, name='api-send-code'),
    path('auth/verify-code/', views.verify_code, name='api-verify-code'),
    path('profile/', views.profile, name='api-profile'),
    path('profile/activate-invite/', views.activate_invite, name='api-activate-invite'),
    # HTML страницы
    path('auth/', views.auth_page, name='auth-page'),
    path('profile-page/', views.profile_page, name='profile-page'),
    path('logout/', views.logout_view, name='logout'),
]
