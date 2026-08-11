# api/maritime_serializers.py
from rest_framework import serializers
from api.maritime_models import MaritimeCourse, MaritimeEnrollment, MaritimeContent


class MaritimeContentSerializer(serializers.ModelSerializer):
    """Serializer for MaritimeContent items."""
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MaritimeContent
        fields = [
            'id',
            'course',
            'title',
            'slug',
            'content_type',
            'body',
            'file',
            'file_url',
            'external_url',
            'order',
            'is_published',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'file_url']
        extra_kwargs = {'file': {'required': False, 'allow_null': True}}

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def validate(self, data):
        instance = getattr(self, 'instance', None)
        content_type = data.get('content_type') or (instance.content_type if instance else None)
        file = data.get('file') if 'file' in data else (instance.file if instance else None)
        external_url = data.get('external_url') if 'external_url' in data else (instance.external_url if instance else None)
        body = data.get('body') if 'body' in data else (instance.body if instance else None)

        if content_type == 'file' and not file:
            raise serializers.ValidationError({"file": "A file upload is required when content_type is 'file'."})
        if content_type == 'link' and not external_url:
            raise serializers.ValidationError({"external_url": "external_url is required when content_type is 'link'."})
        if content_type == 'text' and not body:
            raise serializers.ValidationError({"body": "Body text is required when content_type is 'text'."})
        return data


class MaritimeContentSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for nested lists to avoid heavy payloads when embedding."""
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MaritimeContent
        fields = ['id', 'title', 'slug', 'content_type', 'order', 'is_published', 'file_url']
        read_only_fields = fields

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None


class MaritimeCourseSerializer(serializers.ModelSerializer):
    """Serializer for MaritimeCourse including nested content list (read-only)."""
    contents = MaritimeContentSummarySerializer(many=True, read_only=True)

    class Meta:
        model = MaritimeCourse
        fields = [
            'id',
            'code',
            'title',
            'credits',
            'duration_weeks',
            'summary',
            'outcomes',
            'track',
            'order',
            'fee',
            'contents',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'contents']


class MaritimeEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for MaritimeEnrollment. User is read-only and set from request on create."""
    user_display = serializers.StringRelatedField(source='user', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = MaritimeEnrollment
        fields = [
            'id',
            'user',
            'user_display',
            'track',
            'course',
            'course_title',
            'status',
            'amount_paid',
            'payment_phone',
            'transaction_code',
            'payment_status',
            'payment_confirmed_by',
            'payment_confirmed_at',
            'access_code_sent',
            'access_code_used',
            'access_code_expires_at',
            'enrolled_at',
            'updated_at',
            'completed_at',
        ]
        read_only_fields = ['id', 'user', 'status', 'payment_confirmed_by', 'payment_confirmed_at', 'access_code_sent', 'access_code_used', 'access_code_expires_at', 'enrolled_at', 'updated_at']

    def validate(self, data):
        """
        For creation via MPESA flow:
        - Require transaction_code, payment_phone, amount_paid
        - Prevent duplicate enrollment for same user + course
        """
        if self.instance is None:
            request = self.context.get('request')
            user = getattr(request, 'user', None)

            # Extract course_id attempt: serializer input may be PK
            course_val = data.get('course')
            course_id = None
            if hasattr(course_val, 'id'):
                course_id = course_val.id
            else:
                course_id = course_val

            if not data.get('transaction_code'):
                raise serializers.ValidationError({"transaction_code": "Transaction code is required. Please paste your MPESA transaction code."})
            if not data.get('payment_phone'):
                raise serializers.ValidationError({"payment_phone": "Phone number used for payment is required."})
            if not data.get('amount_paid'):
                raise serializers.ValidationError({"amount_paid": "Amount paid is required."})

            # Prevent duplicate enrollment if user already has one for this course
            if user and user.is_authenticated and course_id:
                if MaritimeEnrollment.objects.filter(user=user, course_id=course_id).exists():
                    raise serializers.ValidationError({"non_field_errors": ["You already have an enrollment for this course."]})

        return data

    def create(self, validated_data):
        """Set user from request and set pending_verification status on create."""
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required to enroll.")
        validated_data['user'] = request.user
        validated_data['status'] = 'pending_verification'
        validated_data['payment_status'] = 'pending_verification'
        enrollment = super().create(validated_data)
        return enrollment