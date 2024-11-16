# core/forms.py
from django import forms
from .models import User, Question, Answer, Feedback, MainTopic, SubTopic
from django.contrib.auth.forms import AuthenticationForm

from django import forms

class ContactForm(forms.Form):
    full_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"placeholder": "Your full name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "Your email"}))
    message = forms.CharField(widget=forms.Textarea(attrs={"placeholder": "How can we help you?", "rows": 5}))


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'phone_number', 'profile_picture']

    password = forms.CharField(widget=forms.PasswordInput)

class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['email', 'password']

    # You can add custom widgets or additional styling if needed.
    # Example: Adding a custom placeholder for the email field
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Email Address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'profile_picture']


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['content', 'main_topic', 'sub_topic', 'attachments']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set sub-topics based on the selected main-topic
        if 'main_topic' in self.data:
            try:
                main_topic_id = int(self.data.get('main_topic'))
                self.fields['sub_topic'].queryset = SubTopic.objects.filter(main_topic_id=main_topic_id)
            except (ValueError, TypeError):
                pass  # Ignore if no valid main_topic is provided
        elif self.instance.pk:
            self.fields['sub_topic'].queryset = self.instance.main_topic.subtopics.all()

    def clean(self):
        cleaned_data = super().clean()
        main_topic = cleaned_data.get("main_topic")
        sub_topic = cleaned_data.get("sub_topic")

        if main_topic and sub_topic and sub_topic.main_topic != main_topic:
            raise forms.ValidationError("The sub-topic must belong to the selected main topic.")

        return cleaned_data


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['content']


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['feedback']
