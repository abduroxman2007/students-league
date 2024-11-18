# views.py

import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views import View
from .utils import send_verification_email
from .models import *
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
            queryset = queryset.filter(answer__isnull=False)
        elif filter_status == 'not_answered':
            queryset = queryset.filter(answer__isnull=True)

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
                Q(user__email__icontains=search_query)
            )

        # If the user is a teacher, return their answered questions and answers
        # if self.request.user.is_teacher():
        #     queryset = queryset.filter(answer__teacher=self.request.user)

        # If the user is a student, return all questions
        elif self.request.user.is_student():
            pass  # No additional filtering needed for students

        return queryset.order_by('-created_at')  # Latest questions first

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
        print("Email: ",email, "  Password: ", password)
        user = authenticate(request, username=email, password=password)
        print("USer: ",user)
        if user is not None:
            print("Email: ",email, "  Password: ", password)
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
            is_active=True
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
            print("Verificatiion object: ", verification)

            if verification.is_expired() == True:
                print("Code was expired")
                messages.error(request, "The verification code has expired.")
                return render(request,  'email_verification.html', {'email': email, 'remaining_time': request.session.get('remaining_time')})

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




from django.contrib.auth.mixins import LoginRequiredMixin
from .utils import send_verification_email, send_password_reset_email, generate_random_token
from django.utils import timezone
from datetime import timedelta
from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

class ProfileView(LoginRequiredMixin, View):
    template_name = "profile.html"

    def get(self, request, *args, **kwargs):
        user = request.user
        context = {
            'user_info': user,
        }
        print(Question.objects.filter(status=False))
        if user.is_student():
            context.update({
                'questions': Question.objects.filter(user=user),
                'feedback': Feedback.objects.filter(user=user).first(),
            })
        else:
            context.update({
                'unanswered_questions': Question.objects.filter(status=False),
                'answers': Answer.objects.filter(teacher=user),
            })
        
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        body = {}

        if request.FILES is None:
            body = json.loads(request.body)
            print("maybe it will work")

        if user.is_student():
            print("Not worked yet: ", request.FILES)
            if 'main_topic' in request.POST:
                    print("It did work")
                    question_text = request.POST.get('content')
                    main_topic_id = request.POST.get('main_topic')
                    sub_topic_id = request.POST.get('sub_topic')
                    attachments = request.FILES.get('attachments')
                    print("attachments: ", main_topic_id, sub_topic_id)
                    print("attachments: ", attachments)

                    if question_text and main_topic_id and sub_topic_id:
                        print("will not be here soon ig")
                        main_topic = get_object_or_404(MainTopic, name=main_topic_id)
                        print("will not be here soon ig")
                        sub_topic = get_object_or_404(SubTopic, name=sub_topic_id, main_topic=main_topic)
                        print("will not be here soon ig")

                        Question.objects.create(
                            user=user,
                            content=question_text,
                            main_topic=main_topic,
                            sub_topic=sub_topic,
                            attachments=attachments
                        )
                        messages.success(request, "Question created successfully")
                        return redirect('core:faq')  # Redirect to profile after successful question creation


            elif 'feedback' in body:
                if Feedback.objects.filter(user=user).exists():
                    return JsonResponse({'error': 'Feedback already exists'}, status=400)
                feedback_text = body.get('feedback')
                if feedback_text:
                    Feedback.objects.create(user=user, feedback=feedback_text)
                    return JsonResponse({'message': 'Feedback created successfully'})
                return JsonResponse({'error': 'Feedback text is required'}, status=400)

            
        elif user.is_teacher():
            print(request.POST)
            print(request.POST)
            if 'answer' in body or 'answer' in request.POST:
                if 'answer' in request.POST:
                    question_id = request.POST.get('question_id')
                    answer_text = request.POST.get('answer')
                else:
                    question_id = body.get('question_id')
                    answer_text = body.get('answer')    
                print(question_id)    
                question = get_object_or_404(Question, id=question_id, status=False)
                if answer_text:
                    print(" Answer : ", answer_text)
                    Answer.objects.create(teacher=user, question=question, content=answer_text)
                    question.status = True
                    question.save()
                    return JsonResponse({'message': 'Answer created successfully'})
                return JsonResponse({'error': 'Answer text is required'}, status=400)

        elif 'email_change' in body or 'email_change' in request.POST:
            new_email = body.get('email')
            if User.objects.filter(email=new_email).exists():
                return JsonResponse({'error': 'Email is already in use'}, status=400)
            send_verification_email(user, new_email)
            return JsonResponse({'message': 'Verification email sent successfully'})

        elif 'password_reset' in body or 'password_reset' in request.POST:
            token = generate_random_token()
            expiration_time = timezone.now() + timedelta(hours=1)
            PasswordResetToken.objects.create(user=user, token=token, expiration_time=expiration_time)
            send_password_reset_email(user, token)
            return JsonResponse({'message': 'Password reset email sent successfully'})

        return JsonResponse({'error': 'Invalid request'}, status=400)

    def put(self, request, *args, **kwargs):
        user = request.user
        body = json.loads(request.body)

        if 'user_info' in body:
            user.first_name = body['user_info'].get('first_name', user.first_name)
            user.last_name = body['user_info'].get('last_name', user.last_name)
            user.phone_number = body['user_info'].get('phone_number', user.phone_number)
            user.save()
            return JsonResponse({'message': 'User information updated successfully'})

        elif user.is_student() and 'feedback' in body:
            feedback = get_object_or_404(Feedback, user=user)
            feedback.feedback = body.get('feedback', feedback.feedback)
            feedback.save()
            return JsonResponse({'message': 'Feedback updated successfully'})

        elif user.is_teacher() and 'answer' in body:
            answer_id = body.get('answer_id')
            answer_text = body.get('answer')
            answer = get_object_or_404(Answer, id=answer_id, teacher=user)
            if answer_text:
                answer.content = answer_text
                answer.save()
                return JsonResponse({'message': 'Answer updated successfully'})

        return JsonResponse({'error': 'Invalid request'}, status=400)

    def delete(self, request, *args, **kwargs):
        user = request.user
        body = json.loads(request.body)

        if user.is_student() and 'question_id' in body:
            question = get_object_or_404(Question, id=body.get('question_id'), user=user)
            question.delete()
            return JsonResponse({'message': 'Question deleted successfully'})

        elif user.is_teacher() and 'answer_id' in body:
            answer = get_object_or_404(Answer, id=body.get('answer_id'), teacher=user)
            question = get_object_or_404(Question, id=answer.question.id)
            question.status = False
            question.save()
            answer.delete()
            return JsonResponse({'message': 'Answer deleted successfully'})

        elif 'feedback' in body:
            feedback = get_object_or_404(Feedback, user=user)
            feedback.delete()
            return JsonResponse({'message': 'Feedback deleted successfully'})

        return JsonResponse({'error': 'Invalid request'}, status=400)


from django.views import View
from django.shortcuts import render, redirect
from .models import PasswordResetToken
from .utils import send_password_reset_email, generate_random_token

class RequestPasswordResetView(View):
    def post(self, request):
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        
        if user:
            token = generate_random_token()
            expiration_time = timezone.now() + timedelta(hours=1)  # Token valid for 1 hour
            
            # Save the token in the database
            PasswordResetToken.objects.create(user=user, token=token, expiration_time=expiration_time)
            
            # Send the password reset email
            send_password_reset_email(user, token)
            messages.success(request, "Password reset email sent.")
        else:
            messages.error(request, "No user found with this email.")
        
        return redirect('core:login')  # Redirect to login or another page
    

class ResetPasswordView(View):
    def get(self, request, token):
        # Check if the token is valid
        password_reset_token = PasswordResetToken.objects.filter(token=token).first()
        if password_reset_token and not password_reset_token.is_expired():
            return render(request, 'reset_password.html', {'token': token})
        else:
            messages.error(request, "Invalid or expired token.")
            return redirect('core:login')

    def post(self, request, token):
        new_password = request.POST.get('new_password')
        new_password = request.POST.get('new_password')
        password_reset_token = PasswordResetToken.objects.filter(token=token).first()
        
        if password_reset_token and not password_reset_token.is_expired():
            user = password_reset_token.user
            user.set_password(new_password)
            user.save()
            password_reset_token.delete()  # Optionally delete the token after use
            messages.success(request, "Your password has been reset successfully.")
            return redirect('core:login')
        else:
            messages.error(request, "Invalid or expired token.")
            return redirect('core:login')