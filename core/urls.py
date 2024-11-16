# core/urls.py
from django.urls import path
from . import views

app_name = 'core'  # Add this line

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('sign-up/', views.RegisterView.as_view(), name='sign_up'),
    path('email-verification/', views.EmailVerificationView.as_view(), name='email-verification'),
    path('login/', views.SignInView.as_view(), name='login'),
    path('resend-code/', views.resend_code, name='resend-code'),

    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    
    path('profile/', views.DashboardView.as_view(), name='profile'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('faq/', views.FAQView.as_view(), name='faq'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    
    # path('feedback/', views.feedback, name='feedback'),
    # path('request-password-reset/', views.request_password_reset, name='request-password-reset'),
    # path('reset-password/<str:token>/', views.reset_password, name='reset-password'),

]
