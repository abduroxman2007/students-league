# admin.py (to promote users)
from django.contrib import admin
from .models import (
    User, 
    EmailVerification, 
    Banner, 
    Question, 
    Answer, 
    Insight, 
    Feedback,
    MainTopic,
    SubTopic
)

@admin.action(description='Promote selected users to teachers')
def promote_to_teacher(modeladmin, request, queryset):
    queryset.update(is_teacher=True)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_teacher')
    actions = [promote_to_teacher]

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'verification_code', 'verified', 'created_at')

@admin.register(MainTopic)
class MainTopicAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(SubTopic)
class SubTopicAdmin(admin.ModelAdmin):
    list_display = ('main_topic','name')

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('image', 'is_active', 'created_at')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'main_topic', 'sub_topic', 'status', 'created_at', 'updated_at')
    search_fields = ('content',)
    list_filter = ('main_topic', 'sub_topic', 'status', 'created_at')

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'teacher', 'created_at')
    list_filter = ('teacher',)
    search_fields = ('content',)

@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ('video_url',)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('feedback',)
