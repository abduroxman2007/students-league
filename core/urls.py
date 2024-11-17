# core/urls.py
from django.urls import path
from . import views

app_name = 'core'  # Add this line

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('login/', views.SignInView.as_view(), name='login'),
    path('sign-up/', views.RegisterView.as_view(), name='sign_up'),
    path('email-verification/', views.EmailVerificationView.as_view(), name='email-verification'),
    path('resend-code/', views.resend_code, name='resend-code'),

    path('reset-password/', views.RequestPasswordResetView.as_view(), name='reset-password'),
    path('reset-password/<str:token>/', views.ResetPasswordView.as_view(), name='reset-password'),

    path('about/', views.AboutView.as_view(), name='about'),
    path('faq/', views.FAQView.as_view(), name='faq'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    
    path('profile/', views.ProfileView.as_view(), name='profile'),

    path("logout/", views.CustomLogoutView.as_view(), name="logout"),

]
