from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *

def token_payload(user):
    refresh=RefreshToken.for_user(user)
    return {'access':str(refresh.access_token),'refresh':str(refresh),'user':UserSerializer(user).data}

# ============================================================
# PROFILE & USER SERIALIZERS
# ============================================================

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=Profile
        fields=['user_type','phone','school','county','career_interest','parent_name','parent_email','teacher_name','teacher_email','auto_parent_reports','auto_teacher_reports','report_frequency']

class UserSerializer(serializers.ModelSerializer):
    profile=ProfileSerializer(read_only=True)
    name=serializers.SerializerMethodField()
    class Meta:
        model=User
        fields=['id','username','email','first_name','last_name','name','profile']
    def get_name(self,obj): return (obj.get_full_name() or obj.username)

# ============================================================
# AUTHENTICATION SERIALIZERS
# ============================================================

class RegisterSerializer(serializers.Serializer):
    username=serializers.CharField(required=False,allow_blank=True)
    email=serializers.EmailField()
    password=serializers.CharField(write_only=True,min_length=6)
    first_name=serializers.CharField(required=False,allow_blank=True)
    last_name=serializers.CharField(required=False,allow_blank=True)
    user_type=serializers.CharField(required=False,default='student')
    userType=serializers.CharField(required=False,allow_blank=True,write_only=True)
    phone=serializers.CharField(required=False,allow_blank=True)
    school=serializers.CharField(required=False,allow_blank=True)
    county=serializers.CharField(required=False,allow_blank=True)
    career_interest=serializers.CharField(required=False,allow_blank=True)
    parent_name=serializers.CharField(required=False,allow_blank=True)
    parent_email=serializers.EmailField(required=False,allow_blank=True)
    teacher_name=serializers.CharField(required=False,allow_blank=True)
    teacher_email=serializers.EmailField(required=False,allow_blank=True)
    auto_parent_reports=serializers.BooleanField(required=False)
    auto_teacher_reports=serializers.BooleanField(required=False)
    report_frequency=serializers.CharField(required=False,allow_blank=True)

    def validate(self, attrs):
        if attrs.get('userType') and not attrs.get('user_type'):
            attrs['user_type']=attrs['userType']
        valid_types=[choice[0] for choice in Profile.USER_TYPES]
        if attrs.get('user_type') not in valid_types:
            raise serializers.ValidationError({'user_type':f'Must be one of: {", ".join(valid_types)}'})
        return attrs

    def create(self,validated):
        username=validated.get('username') or validated['email']
        if User.objects.filter(username=username).exists() or User.objects.filter(email=validated['email']).exists():
            raise serializers.ValidationError({'email':'User already exists.'})
        user=User.objects.create_user(username=username,email=validated['email'],password=validated['password'],first_name=validated.get('first_name',''),last_name=validated.get('last_name',''))
        prof=user.profile
        prof.user_type=validated.get('user_type','student')
        prof.phone=validated.get('phone','')
        prof.school=validated.get('school','')
        prof.county=validated.get('county','')
        prof.career_interest=validated.get('career_interest','')
        prof.parent_name=validated.get('parent_name','')
        prof.parent_email=validated.get('parent_email') or None
        prof.teacher_name=validated.get('teacher_name','')
        prof.teacher_email=validated.get('teacher_email') or None
        if 'auto_parent_reports' in validated: prof.auto_parent_reports=validated.get('auto_parent_reports')
        if 'auto_teacher_reports' in validated: prof.auto_teacher_reports=validated.get('auto_teacher_reports')
        prof.report_frequency=validated.get('report_frequency','weekly') or 'weekly'
        prof.save()
        return user

class LoginSerializer(serializers.Serializer):
    username=serializers.CharField(required=False,allow_blank=True)
    email=serializers.EmailField(required=False,allow_blank=True)
    password=serializers.CharField(write_only=True)
    def validate(self,attrs):
        identifier=attrs.get('username') or attrs.get('email')
        if not identifier: raise serializers.ValidationError('Username or email required.')
        username=identifier
        if '@' in identifier:
            user=User.objects.filter(email__iexact=identifier).first()
            if user: username=user.username
        user=authenticate(username=username,password=attrs['password'])
        if not user: raise serializers.ValidationError('Invalid credentials.')
        attrs['user']=user
        return attrs

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(required=False, allow_blank=True)
    token = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

# ============================================================
# SCHOOL OS SERIALIZER
# ============================================================

class SchoolOSResourceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    module = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = GenericResource
        fields = ['id', 'resource_type', 'module', 'title', 'summary', 'data', 'status', 'createdAt', 'updatedAt']

    def get_module(self, obj):
        return (obj.data or {}).get('module') or obj.resource_type

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        data = rep.pop('data') or {}
        return {**rep, **data}

    def to_internal_value(self, data):
        known = {k: data.get(k) for k in ['resource_type', 'title', 'summary', 'status'] if k in data}
        extra = {k: v for k, v in data.items() if k not in known and k not in ['id', 'createdAt', 'updatedAt', 'resource_type']}
        known['resource_type'] = data.get('resource_type') or 'school_os'
        known['data'] = extra
        return super().to_internal_value(known)

# ============================================================
# EDUCATIONAL CONTENT SERIALIZERS
# ============================================================

class ProgramSerializer(serializers.ModelSerializer):
    class Meta: model=Program; fields='__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    program_slug=serializers.CharField(write_only=True,required=False,allow_blank=True)
    program_title=serializers.CharField(source='program.title',read_only=True)
    programSlug=serializers.CharField(write_only=True,required=False,allow_blank=True)
    class Meta:
        model=Enrollment
        fields='__all__'
        read_only_fields=['user']
    def validate(self,attrs):
        slug=attrs.pop('program_slug',None) or attrs.pop('programSlug',None)
        if slug and not attrs.get('program'):
            program=Program.objects.filter(slug=slug).first() or Program.objects.filter(title__iexact=slug.replace('-', ' ')).first()
            if not program:
                raise serializers.ValidationError({'program_slug':'Program not found.'})
            attrs['program']=program
        return attrs

class LessonSerializer(serializers.ModelSerializer):
    class Meta: model=Lesson; fields='__all__'

class VideoSerializer(serializers.ModelSerializer):
    class Meta: model=Video; fields='__all__'

class ContentItemSerializer(serializers.ModelSerializer):
    class Meta: model=ContentItem; fields='__all__'

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta: model=Assessment; fields='__all__'

class StudentScoreSerializer(serializers.ModelSerializer):
    class Meta: model=StudentScore; fields='__all__'; read_only_fields=['user']

class StudentIntelligenceProfileSerializer(serializers.ModelSerializer):
    class Meta: model=StudentIntelligenceProfile; fields='__all__'; read_only_fields=['user']

# ============================================================
# GENERIC RESOURCE SERIALIZER
# ============================================================

class GenericResourceSerializer(serializers.ModelSerializer):
    id=serializers.IntegerField(read_only=True)
    createdAt=serializers.DateTimeField(source='created_at',read_only=True)
    updatedAt=serializers.DateTimeField(source='updated_at',read_only=True)
    class Meta:
        model=GenericResource
        fields=['id','resource_type','title','summary','data','status','createdAt','updatedAt']
    def to_representation(self,instance):
        rep=super().to_representation(instance)
        data=rep.pop('data') or {}
        return {**rep, **data}
    def to_internal_value(self,data):
        known={k:data.get(k) for k in ['resource_type','title','summary','status'] if k in data}
        extra={k:v for k,v in data.items() if k not in known and k not in ['id','createdAt','updatedAt']}
        known['data']=extra
        return super().to_internal_value(known)

# ============================================================
# M-PESA SERIALIZER
# ============================================================

class MpesaPaymentSerializer(serializers.ModelSerializer):
    class Meta: model=MpesaPayment; fields='__all__'; read_only_fields=['user','order_number','status','response']

# ============================================================
# BOOKS & READING SERIALIZERS
# ============================================================

class BookSerializer(serializers.ModelSerializer):
    cover_url=serializers.SerializerMethodField()
    file_url=serializers.SerializerMethodField()
    pdf_url=serializers.SerializerMethodField()
    
    class Meta:
        model=Book
        fields=['id','title','slug','author','description','text_content','category','grade','language','program','cover','cover_url','file','file_url','pdf','pdf_url','external_url','reading_level','pages','estimated_minutes','xp_reward','is_featured','is_published','metadata','created_at','updated_at']
        read_only_fields=['slug','created_at','updated_at']
    
    def get_cover_url(self,obj):
        request=self.context.get('request')
        if obj.cover:
            return request.build_absolute_uri(obj.cover.url) if request else obj.cover.url
        return ''
    
    def get_file_url(self,obj):
        request=self.context.get('request')
        if obj.file:
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return obj.external_url or ''
    
    def get_pdf_url(self, obj):
        """Return absolute URL for PDF file (for Readathon viewer)"""
        request = self.context.get('request')
        if obj.pdf:
            return request.build_absolute_uri(obj.pdf.url) if request else obj.pdf.url
        return ''

class UserBookSerializer(serializers.ModelSerializer):
    book_detail=BookSerializer(source='book',read_only=True)
    book_slug=serializers.CharField(write_only=True,required=False,allow_blank=True)
    class Meta:
        model=UserBook
        fields=['id','book','book_slug','book_detail','progress','current_page','reading_minutes','bookmarked','completed','notes','last_read_at','metadata','created_at','updated_at']
        read_only_fields=['created_at','updated_at']
    def validate(self,attrs):
        slug=attrs.pop('book_slug',None)
        if slug and not attrs.get('book'):
            book=Book.objects.filter(slug=slug,is_published=True).first()
            if not book:
                raise serializers.ValidationError({'book_slug':'Book not found.'})
            attrs['book']=book
        return attrs

# ============================================================
# READATHON REPORTS & INTERVENTIONS
# ============================================================

class ReadathonReportSerializer(serializers.ModelSerializer):
    content = serializers.CharField(source='body', read_only=True)
    report = serializers.CharField(source='body', read_only=True)
    insight = serializers.CharField(source='body', read_only=True)
    summary = serializers.SerializerMethodField()
    book_title = serializers.SerializerMethodField()

    class Meta:
        model = ReadathonReport
        fields = '__all__'
        read_only_fields = ['user', 'delivery_status', 'emailed_at', 'created_at', 'updated_at']

    def get_summary(self, obj):
        return (obj.body or '')[:500]

    def get_book_title(self, obj):
        return (obj.metadata or {}).get('book_title') or obj.title

class InterventionNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterventionNote
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

# ============================================================
# ACTIVITY LOG SERIALIZER
# ============================================================

class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for ActivityLog model"""
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'user_name', 'action', 'details', 'ip_address', 'user_agent', 'created_at']
        read_only_fields = ['created_at']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else 'Anonymous'

# ============================================================
# 🛒 STORE SERIALIZERS
# ============================================================

class ProductCategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'image', 'parent', 'subcategories', 'is_active', 'order', 'product_count']
    
    def get_subcategories(self, obj):
        return ProductCategorySerializer(obj.children.all(), many=True).data
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

class ProductSerializer(serializers.ModelSerializer):
    categories = ProductCategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories', queryset=ProductCategory.objects.all(), many=True, write_only=True
    )
    in_stock = serializers.BooleanField(read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    main_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'product_type',
            'short_description', 'description', 'specifications',
            'price', 'compare_price', 'cost',
            'stock', 'low_stock_threshold', 'in_stock', 'allow_backorder',
            'main_image', 'main_image_url', 'images',
            'categories', 'category_ids', 'tags',
            'age_group', 'difficulty_level', 'includes', 'requirements',
            'xp_reward',
            'is_featured', 'is_best_seller', 'is_active', 'is_digital',
            'digital_file', 'meta_title', 'meta_description', 'weight',
            'is_on_sale', 'average_rating', 'review_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'sku', 'created_at', 'updated_at']
    
    def get_main_image_url(self, obj):
        if obj.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0
    
    def get_review_count(self, obj):
        return obj.reviews.count()

class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'user_name', 'user_avatar', 'rating', 'title', 'comment', 'is_verified_purchase', 'helpful_count', 'created_at']
        read_only_fields = ['user', 'is_verified_purchase', 'helpful_count', 'created_at']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_user_avatar(self, obj):
        return None  # Can be extended with profile picture

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source='product', queryset=Product.objects.all(), write_only=True
    )
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cart_items', many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'subtotal', 'is_active', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_sku', 'product_image', 'quantity', 'price', 'total']
    
    def get_product_image(self, obj):
        if obj.product.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.product.main_image.url)
            return obj.product.main_image.url
        return None

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    payment_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user',
            'email', 'phone', 'full_name',
            'shipping_address', 'shipping_city', 'shipping_county', 'shipping_postal_code',
            'billing_address', 'billing_city', 'billing_county',
            'subtotal', 'shipping_cost', 'tax', 'discount', 'total',
            'order_status', 'status_display', 'payment_status', 'payment_display',
            'payment_method', 'transaction_id',
            'tracking_number', 'shipping_carrier', 'estimated_delivery',
            'notes', 'items', 'items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        return obj.items.count()
    
    def get_status_display(self, obj):
        return dict(Order.ORDER_STATUS).get(obj.order_status, obj.order_status)
    
    def get_payment_display(self, obj):
        return dict(Order.PAYMENT_STATUS).get(obj.payment_status, obj.payment_status)

class OrderCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    shipping_address = serializers.CharField()
    shipping_city = serializers.CharField()
    shipping_county = serializers.CharField()
    shipping_postal_code = serializers.CharField(required=False, allow_blank=True)
    billing_address = serializers.CharField(required=False, allow_blank=True)
    billing_city = serializers.CharField(required=False, allow_blank=True)
    billing_county = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source='product', queryset=Product.objects.all(), write_only=True
    )
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_id', 'created_at']

class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Coupon
        fields = ['code', 'description', 'discount_type', 'discount_value', 'minimum_order', 'max_discount', 'is_valid', 'valid_from', 'valid_to']

class CouponValidationSerializer(serializers.Serializer):
    code = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)

# ============================================================
# 🛒 PAYMENT SERIALIZER
# ============================================================

class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    user_name = serializers.SerializerMethodField()
    payment_method_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_number', 'user', 'user_name',
            'amount', 'payment_method', 'payment_method_display',
            'status', 'status_display', 'transaction_id',
            'payment_details', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'transaction_id', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else 'Guest'
    
    def get_payment_method_display(self, obj):
        return dict(Payment.PAYMENT_METHODS).get(obj.payment_method, obj.payment_method)
    
    def get_status_display(self, obj):
        return dict(Payment.PAYMENT_STATUS).get(obj.status, obj.status)

# ============================================================
# 🛒 ADDRESS SERIALIZER
# ============================================================

class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address model"""
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Address
        fields = [
            'id', 'address_type', 'full_name', 'phone',
            'address_line1', 'address_line2', 'city', 'county',
            'postal_code', 'country', 'is_default', 'notes',
            'full_address', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_full_address(self, obj):
        parts = [obj.address_line1]
        if obj.address_line2:
            parts.append(obj.address_line2)
        parts.append(obj.city)
        parts.append(obj.county)
        if obj.postal_code:
            parts.append(obj.postal_code)
        parts.append(obj.country)
        return ', '.join(parts)

# ============================================================
# 🛒 COUPON USAGE SERIALIZER
# ============================================================

class CouponUsageSerializer(serializers.ModelSerializer):
    """Serializer for CouponUsage model"""
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    user_name = serializers.SerializerMethodField()
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = CouponUsage
        fields = ['id', 'coupon', 'coupon_code', 'user', 'user_name', 'order', 'order_number', 'discount_amount', 'used_at']
        read_only_fields = ['used_at']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else obj.user.username

# ============================================================
# STORE STATS SERIALIZER
# ============================================================

class StoreStatsSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_customers = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    recent_orders = OrderSerializer(many=True)
    generated_at = serializers.DateTimeField()
