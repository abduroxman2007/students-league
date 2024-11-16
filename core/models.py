# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings  # To reference the User model
from django.core.exceptions import ValidationError

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/',  null=True, blank=True, default='profile_pictures/defaultAvatar.png')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def is_teacher(self):
        return hasattr(self, 'teacherprofile')

    def is_student(self):
        return hasattr(self, 'studentprofile')

import random
import string
from django.utils import timezone
from django.db import models
from datetime import timedelta

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    verification_code = models.CharField(max_length=6)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expiration_time = models.DateTimeField(null=True, blank=True)  # Field for expiration

    def generate_verification_code(self):
        return ''.join(random.choices(string.digits, k=6))

    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = self.generate_verification_code()
        if not self.expiration_time:
            self.expiration_time = timezone.now() + timedelta(hours=1)  # Code expires in 1 hour
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expiration_time

    def reset_code(self):
        self.verification_code = self.generate_verification_code()
        self.expiration_time = timezone.now() + timedelta(seconds=60)  # Reset expiration time
        self.save()

    def __str__(self):
        return f"Verification for {self.user.email}"

class Banner(models.Model):
    image = models.ImageField(upload_to='banners/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class MainTopic(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class SubTopic(models.Model):
    main_topic = models.ForeignKey(MainTopic, on_delete=models.CASCADE, related_name="subtopics")
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.main_topic.name})"
    
# core/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

class Question(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='questions'
    )
    content = models.TextField()
    main_topic = models.ForeignKey(
        'MainTopic', 
        on_delete=models.CASCADE, 
        related_name='questions'
    )
    sub_topic = models.ForeignKey(
        'SubTopic', 
        on_delete=models.CASCADE, 
        related_name='questions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=False)  # False = Not Answered, True = Answered
    attachments = models.FileField(
        upload_to='attachments/', 
        null=True, 
        blank=True
    )  # Optional file attachments

    def clean(self):
        if self.sub_topic.main_topic != self.main_topic:
            raise ValidationError(
                f"The selected sub-topic '{self.sub_topic}' does not belong to the main topic '{self.main_topic}'."
            )

    def __str__(self):
        return f"Question by {self.user} on {self.main_topic} ({self.created_at})"



class Answer(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='answer')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='answers')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.teacher.is_teacher:
            raise ValidationError({
                'teacher': 'Only teachers can create answers. This user is not a teacher.'
            })
        
        # Optional: Check if the question already has an answer
        if (self.question.answer.exists() and 
            self.question.answer.first().id != self.id):
            raise ValidationError({
                'question': 'This question already has an answer'
            })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Answer to: {self.question.content[:50]} by {self.teacher.first_name}'

    class Meta:
        ordering = ['-created_at']

class Insight(models.Model):
    video_url = models.URLField()
    description = models.TextField()

# Feedback 
class Feedback(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='feedback'
    )
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.user.email}"

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expiration_time = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expiration_time

# core/models.py

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacherprofile')
    # bio = models.TextField(blank=True)
    # Add any teacher-specific fields here (e.g., subjects taught)
    
    def __str__(self):
        return f"Teacher Profile for {self.user.email}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='studentprofile')
    # grade_level = models.CharField(max_length=20, blank=True)
    # Add any student-specific fields here (e.g., current courses)
    
    def __str__(self):
        return f"Student Profile for {self.user.email}"


class Contact(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField(help_text="Describe how we can help you.")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contact from {self.full_name} - {self.email}"
