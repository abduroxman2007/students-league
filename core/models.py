# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings  # To reference the User model
from django.core.exceptions import ValidationError

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role='student', **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)



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
    
    # New field to indicate user role
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')  # Default to student
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def is_teacher(self):
        if self.role == 'teacher':
            return True
        return False

    def is_student(self):
        if self.role == 'student':
            return True
        return False

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
        self.expiration_time = timezone.now() + timedelta(minutes=5)  # Reset expiration time
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
        if not self.teacher.is_teacher():
            raise ValidationError({
                'teacher': 'Only teachers can create answers. This user is not a teacher.'
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


class Contact(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField(help_text="Describe how we can help you.")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contact from {self.full_name} - {self.email}"
