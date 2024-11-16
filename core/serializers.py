from rest_framework import serializers
from .models import User, Question, Answer, Feedback

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Required. Enter a secure password.'
    )
    
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'phone_number', 'is_teacher', 'profile_picture']
        extra_kwargs = {
            'email': {'help_text': 'Required. Enter a valid email address.'},
            'first_name': {'help_text': 'Required. Enter your first name.'},
            'last_name': {'help_text': 'Required. Enter your last name.'},
            'phone_number': {'required': False, 'help_text': 'Optional. Enter your phone number.'},
            'is_teacher': {'read_only': True},
            'profile_picture': {'required': False}
        }

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data.get('phone_number', ''),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)

class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text='Enter the 6-digit verification code sent to your email'
    )

from .models import Question, SubTopic

class QuestionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')
    available_subtopics = serializers.SerializerMethodField()
    sub_topic = serializers.PrimaryKeyRelatedField(queryset=SubTopic.objects.none(), required=False)

    class Meta:
        model = Question
        fields = ['id', 'user', 'content', 'main_topic', 'sub_topic', 
                  'available_subtopics', 'created_at', 'attachments']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        main_topic = self.context.get('main_topic')

        # Dynamically filter `sub_topic` queryset based on `main_topic` context
        if main_topic:
            self.fields['sub_topic'].queryset = SubTopic.objects.filter(main_topic=main_topic)
        else:
            self.fields['sub_topic'].queryset = SubTopic.objects.all()

    def get_available_subtopics(self, obj):
        # Use `obj.main_topic` for existing instances, or initial data for new ones
        main_topic = obj.main_topic if obj.id else self.initial_data.get('main_topic')
        if main_topic:
            subtopics = SubTopic.objects.filter(main_topic=main_topic)
            return {subtopic.id: subtopic.name for subtopic in subtopics}
        return {}

    def validate(self, data):
        main_topic = data.get('main_topic')
        sub_topic = data.get('sub_topic')

        # Ensure sub_topic belongs to the selected main_topic
        if main_topic and sub_topic:
            valid_subtopics = SubTopic.objects.filter(main_topic=main_topic).values_list('id', flat=True)
            if sub_topic.id not in valid_subtopics:
                raise serializers.ValidationError({
                    'sub_topic': f'Selected sub-topic does not belong to the specified main topic.'
                })

        return data

class AnswerSerializer(serializers.ModelSerializer):
    teacher = serializers.ReadOnlyField(source='teacher.email')
    question = serializers.ReadOnlyField(source='question.id')

    class Meta:
        model = Answer
        fields = ['id', 'question', 'teacher', 'content', 'created_at']
        extra_kwargs = {
            'content': {'help_text': 'Enter your answer here.'}
        }

class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Feedback
        fields = ['id', 'user', 'feedback', 'created_at']
        extra_kwargs = {
            'feedback': {'help_text': 'Enter your feedback here.'}
        }


# Add this to your existing serializers.py

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        help_text='Enter your email or phone number'
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Enter your password'
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            # Find user by email or phone number
            try:
                if '@' in username:
                    user = User.objects.get(email=username)
                else:
                    user = User.objects.get(phone_number=username)
                
                # Verify password
                if user.check_password(password):
                    if not user.is_active:
                        raise serializers.ValidationError({
                            'status': 'error',
                            'code': 'email_not_verified',
                            'message': 'Email not verified'
                        })
                    
                    attrs['user'] = user
                    return attrs
                else:
                    raise serializers.ValidationError({
                        'status': 'error',
                        'message': 'Invalid password'
                    })
                    
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'status': 'error',
                    'message': 'User not found'
                })
        else:
            raise serializers.ValidationError({
                'status': 'error',
                'message': 'Must include "username" and "password".'
            })

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text='Enter your registered email address to receive a new verification code'
    )



