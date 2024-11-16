# views.py

import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views import View
from .utils import create_and_save_email_verification, send_verification_email
from .models import EmailVerification, Feedback
from django.http import JsonResponse
from django.views.generic import TemplateView, ListView
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout
from django.views.generic.edit import FormView
from .models import Contact,Question
from .forms import ContactForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

class FAQView(ListView):
    model = Question
    template_name = "faq.html"
    context_object_name = "questions"
    paginate_by = 6  # Default number of questions per page

    def get_queryset(self):
        """
        Filter the questions based on the query parameters.
        """
        queryset = self.model.objects.all()

        # Filter by answer status
        filter_status = self.request.GET.get('filter', '').lower()
        if filter_status == 'answered':
            queryset = queryset.filter(answered=True)
        elif filter_status == 'not_answered':
            queryset = queryset.filter(answered=False)

        # Filter by main topic
        main_topic = self.request.GET.get('topic')
        if main_topic:
            queryset = queryset.filter(main_topic__name__icontains=main_topic)

        # Filter by subtopic
        sub_topic = self.request.GET.get('subtopic')
        if sub_topic:
            queryset = queryset.filter(sub_topic__name__icontains=sub_topic)

        # Search query
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(content__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )

        return queryset.order_by('-created_at')  # Latest questions first

    def get_context_data(self, **kwargs):
        """
        Add pagination and filter metadata to the context.
        """
        context = super().get_context_data(**kwargs)

        # Paginate questions manually for custom control
        questions = context['questions']
        paginator = Paginator(questions, self.paginate_by)

        page = self.request.GET.get('page')
        try:
            paginated_questions = paginator.page(page)
        except PageNotAnInteger:
            paginated_questions = paginator.page(1)
        except EmptyPage:
            paginated_questions = paginator.page(paginator.num_pages)

        context['questions'] = paginated_questions

        # Add current filters to context
        context['filter'] = self.request.GET.get('filter', '')
        context['topic'] = self.request.GET.get('topic', '')
        context['subtopic'] = self.request.GET.get('subtopic', '')
        context['search_query'] = self.request.GET.get('search', '')

        # Add metadata for dynamic filtering
        context['filters'] = ['Answered', 'Not Answered']
        context['main_topics'] = self.model.objects.values_list('main_topic__name', flat=True).distinct()
        context['sub_topics'] = self.model.objects.values_list('sub_topic__name', flat=True).distinct()

        return context


class ContactView(FormView):
    template_name = "contact.html"  # Path to your contact form template
    form_class = ContactForm
    # success_url = ""  # Redirect URL after successful submission

    def form_valid(self, form):
        Contact.objects.create(
            full_name=form.cleaned_data["full_name"],
            email=form.cleaned_data["email"],
            message=form.cleaned_data["message"],
        )
        # Add a success message flag
        return self.render_to_response(self.get_context_data(form=form, success=True))


class AboutView(TemplateView):
    template_name = "about.html"  # Replace with the actual path to your about.html file


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feedbacks = Feedback.objects.all().select_related('user')  # Use select_related to fetch user data efficiently
        context['feedbacks'] = feedbacks
        return context


class CustomLogoutView(View):
    def dispatch(self, request, *args, **kwargs):
        # Log out the user if authenticated
        if request.user.is_authenticated:
            logout(request)  # Use Django's built-in logout function
        # Redirect to the desired page after logout
        return redirect('core:home')  # Change 'home' to your desired redirect URL


class SignInView(View):
    template_name = "login.html"

    def get(self, request):
        # Display the sign-in form
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember-me', 'off') == 'on'
        
        # Authenticate the user
        user = authenticate(request, username=email, password=password)
        if user is not None:
            # Check if user is verified
            try:
                email_verification = EmailVerification.objects.get(user=user)
                
                if email_verification.verified:
                    login(request, user)
                    if not remember_me:
                        request.session.set_expiry(0)  # Session expires on browser close
                    print("You have successfully logged in.")
                    messages.success(request, "You have successfully logged in.")
                    return redirect('core:profile')  # Redirect to profile or home page
                else:
                    # Check if the verification code has expired or needs to be resent
                    if email_verification.is_expired():
                        email_verification.reset_code()  # Reset the code if expired
                        send_verification_email(user)
                        print(user.email)

                    request.session['email_to_verify'] = user.email
                    request.session['remaining_time'] = 60
                    return redirect('core:email-verification')

            except EmailVerification.DoesNotExist:
                print("This email is not registered or does not exist.")
                messages.error(request, "This email is not registered or does not exist.")
                return redirect('core:login')  # Redirect to login if user is not found

        else:
            messages.error(request, "Invalid email or password.")
            return render(request, self.template_name)



from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.shortcuts import get_object_or_404
from .models import Question, Answer, User


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"
    login_url = "core:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.groups.filter(name='Student').exists():
            # Student-specific data
            questions = Question.objects.filter(user=user)
            unanswered_questions = questions.filter(answer__isnull=True)
            answers = Answer.objects.filter(question__user=user)

            context.update({
                'questions': unanswered_questions,
                'answers': answers,
                'personal_info': {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'profile_picture': user.profile_picture,
                }
            })

        elif user.groups.filter(name='Teacher').exists():
            # Teacher-specific data
            answered_questions = Question.objects.filter(answer__teacher=user)
            unanswered_questions = Question.objects.filter(answer__isnull=True)

            context.update({
                'questions': {
                    'answered': answered_questions,
                    'unanswered': unanswered_questions,
                },
                'personal_info': {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'profile_picture': user.profile_picture,
                }
            })

        elif user.is_superuser:
            # Admin-specific data
            all_questions = Question.objects.all()
            all_answers = Answer.objects.all()
            all_students = User.objects.filter(groups__name='Student')
            all_teachers = User.objects.filter(groups__name='Teacher')

            context.update({
                'questions': all_questions,
                'answers': all_answers,
                'students': all_students,
                'teachers': all_teachers,
                'personal_info': {
                    'name': user.first_name,
                    'email': user.email,
                    'is_superuser': user.is_superuser,
                }
            })

        return context




from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterView(View):
    def get(self, request):
        return render(request, 'signup.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')

        # Input validation
        if not all([email, password, confirm_password, first_name, last_name, phone_number]):
            messages.error(request, "All fields are required.")
            return render(request, 'signup.html')
        
        if password != confirm_password:
            messages.error(request, "Passwords must be same.")
            return render(request, 'signup.html')

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return render(request, 'signup.html')

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=False
        )

        # Create and send email verification
        EmailVerification.objects.create(user=user)
        send_verification_email(user)

        # Redirect to the centralized email verification page
        messages.success(request, "Registration successful! Please verify your email.")
        return redirect('core:email-verification')



class EmailVerificationView(View):
    def get(self, request):
        email = request.session.get('email_to_verify')
        remaining_time = request.session.get('remaining_time')
        return render(request, 'email_verification.html', {'email': email, 'remaining_time': remaining_time})

    def post(self, request):
        email = request.POST.get('email')
        verification_code = request.POST.get('code')
        print(email, " and here is the code: ", verification_code)

        try:
            verification = EmailVerification.objects.get(
                user__email=email,
                verification_code=verification_code
            )

            # Check if the code is expired
            if verification.is_expired():
                messages.error(request, "The verification code has expired.")
                return render(request,  'email_verification.html', {'email': email, 'remaining_time': request.session.get('remaining_time')})

            # Mark user as verified and active
            verification.verified = True
            verification.save()
            user = verification.user
            user.is_active = True
            user.save()
            
            login(request, user)

            messages.success(request, "Email verified successfully! Please log in.")
            return redirect('core:profile')  # Redirect to profile after verification

        except EmailVerification.DoesNotExist:
            messages.error(request, "Invalid email or verification code.")
            return render(request, 'email_verification.html')

from django.http import JsonResponse
from .models import EmailVerification

def resend_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        print("Request has came and here it is: ", email)

        if not email:
            return JsonResponse({"success": False, "message": "Email not provided."})

        try:
            email_verification = EmailVerification.objects.get(email=email)
            email_verification.reset_code()  # Regenerate and save the new code
            return JsonResponse({"success": True, "message": "Code resent successfully."})
        except EmailVerification.DoesNotExist:
            return JsonResponse({"success": False, "message": "Email not found."})

    return JsonResponse({"success": False, "message": "Invalid request method."})