import os
import fitz

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models import Sum, F


def extract_pdf_text(file_path):
    text = ""

    try:
        doc = fitz.open(file_path)

        for page in doc:
            text += page.get_text() + "\n"

        doc.close()

    except Exception as e:
        print("PDF extraction error:", e)

    return text.strip()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ============================================================
# USER PROFILE
# ============================================================

class Profile(TimeStampedModel):
    USER_TYPES = (
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("parent", "Parent"),
        ("mentor", "Mentor"),
        ("school_admin", "School Admin"),
        ("admin", "Admin"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default="student")
    phone = models.CharField(max_length=50, blank=True)
    school = models.CharField(max_length=150, blank=True)
    county = models.CharField(max_length=100, blank=True)
    career_interest = models.CharField(max_length=150, blank=True)
    
    # Grade field for ranking/filtering
    grade = models.CharField(max_length=50, blank=True)

    # E-Readathon reporting contacts and preferences
    parent_name = models.CharField(max_length=200, blank=True)
    parent_email = models.EmailField(blank=True, null=True)
    teacher_name = models.CharField(max_length=200, blank=True)
    teacher_email = models.EmailField(blank=True, null=True)
    auto_parent_reports = models.BooleanField(default=True)
    auto_teacher_reports = models.BooleanField(default=True)
    report_frequency = models.CharField(max_length=20, default="weekly", blank=True)

    privacy_settings = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.user.username


# ============================================================
# EDUCATIONAL CONTENT
# ============================================================

class Program(TimeStampedModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "program"
            slug = base
            i = 2

            while Program.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Enrollment(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=30, default="pending")
    metadata = models.JSONField(default=dict, blank=True)


class Lesson(TimeStampedModel):
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="lessons",
    )
    title = models.CharField(max_length=200)
    topic = models.CharField(max_length=150, blank=True)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)


class Video(TimeStampedModel):
    title = models.CharField(max_length=200)
    url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    topic = models.CharField(max_length=150, blank=True)


class ContentItem(TimeStampedModel):
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=50, default="article")
    body = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)


class Assessment(TimeStampedModel):
    title = models.CharField(max_length=200)
    topic = models.CharField(max_length=150, blank=True)
    questions = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)


class StudentScore(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scores")
    topic = models.CharField(max_length=150)
    score = models.FloatField(default=0)
    max_score = models.FloatField(default=100)
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)


# ============================================================
# GENERIC RESOURCES
# ============================================================

class GenericResource(TimeStampedModel):
    RESOURCE_TYPES = (
        ("task", "Task"),
        ("note", "Note"),
        ("discussion", "Discussion"),
        ("assignment", "Assignment"),
        ("grade", "Grade"),
        ("event", "Event"),
        ("study_group", "Study Group"),
        ("career_session", "Career Session"),
        ("feedback", "Feedback"),
        ("support_request", "Support Request"),
        ("book", "Book"),
        ("my_book", "My Book"),
        ("achievement", "Achievement"),
        ("notification", "Notification"),
        ("subscription", "Subscription"),
        ("lab_project", "Lab Project"),
        ("school_os", "Efunza School OS"),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES)
    title = models.CharField(max_length=250, blank=True)
    summary = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=50, blank=True)


# ============================================================
# STUDENT INTELLIGENCE
# ============================================================

class StudentIntelligenceProfile(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="intelligence_profiles",
    )
    analytics = models.JSONField(default=dict, blank=True)
    weak_topics = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    predictive_performance = models.JSONField(default=dict, blank=True)
    career_guidance = models.JSONField(default=dict, blank=True)


# ============================================================
# ACTIVITY LOGGING
# ============================================================

class ActivityLog(TimeStampedModel):
    """Audit log for user activities"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user or 'Anonymous'} - {self.action} - {self.created_at}"


# ============================================================
# M-PESA PAYMENTS
# ============================================================

class MpesaPayment(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=100, unique=True)
    phone = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default="pending")
    response = models.JSONField(default=dict, blank=True)


# ============================================================
# BOOKS & READING
# ============================================================

class Book(TimeStampedModel):
    PROGRAM_CHOICES = (
        ("e-readathon", "E-Readathon"),
        ("general", "General Library"),
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    author = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    text_content = models.TextField(blank=True)

    category = models.CharField(max_length=100, blank=True)
    grade = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=50, default="English")
    program = models.CharField(
        max_length=80,
        choices=PROGRAM_CHOICES,
        default="e-readathon",
    )

    cover = models.ImageField(upload_to="books/covers/", null=True, blank=True)
    file = models.FileField(upload_to="books/files/", null=True, blank=True)
    pdf = models.FileField(
        upload_to="books/pdfs/",
        null=True,
        blank=True,
        help_text="PDF file for the book (for Readathon display)"
    )
    external_url = models.URLField(blank=True)

    reading_level = models.CharField(max_length=100, blank=True)
    pages = models.PositiveIntegerField(default=0)
    estimated_minutes = models.PositiveIntegerField(default=0)
    xp_reward = models.PositiveIntegerField(default=50)

    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "book"
            slug = base
            i = 2

            while Book.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1

            self.slug = slug

        super().save(*args, **kwargs)

        try:
            if self.file and self.file.name.lower().endswith(".pdf") and not self.text_content:
                pdf_path = self.file.path

                if os.path.exists(pdf_path):
                    extracted_text = extract_pdf_text(pdf_path)

                    if extracted_text:
                        self.text_content = extracted_text[:200000]
                        super().save(update_fields=["text_content"])

        except Exception as e:
            print("Book extraction error:", e)

    def __str__(self):
        return self.title


class UserBook(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="library_books")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reader_records")
    progress = models.FloatField(default=0)
    current_page = models.PositiveIntegerField(default=0)
    reading_minutes = models.PositiveIntegerField(default=0)
    bookmarked = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("user", "book")

    def __str__(self):
        return f"{self.user} - {self.book}"


# ============================================================
# READATHON REPORTS & INTERVENTIONS
# ============================================================

class ReadathonReport(TimeStampedModel):
    REPORT_TYPES = (
        ("parent", "Parent Report"),
        ("teacher", "Teacher Insight"),
    )
    DELIVERY_STATUS = (
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="readathon_reports")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    recipient_email = models.EmailField(blank=True)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default="draft")
    emailed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.report_type}: {self.title}"


class InterventionNote(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="readathon_interventions")
    title = models.CharField(max_length=255, default="Reading Intervention")
    note = models.TextField()
    status = models.CharField(max_length=30, default="open")
    priority = models.CharField(max_length=30, default="medium")
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.title


# ============================================================
# 🛒 STORE / E-COMMERCE MODELS
# ============================================================

class ProductCategory(TimeStampedModel):
    """Product categories like 'Science Kits', 'Electronics', 'Books'"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Emoji or icon name
    image = models.ImageField(upload_to='store/categories/', null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    """Main product model for store items"""
    
    PRODUCT_TYPES = (
        ('science_kit', 'Science Fair Kit'),
        ('electronics', 'Electronics Component'),
        ('book', 'Readathon Book'),
        ('merchandise', 'Merchandise'),
        ('digital', 'Digital Product'),
        ('robotics_kit', 'Robotics Kit'),
    )
    
    # Basic Info
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    sku = models.CharField(max_length=50, unique=True, blank=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='science_kit')
    
    # Description
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    specifications = models.JSONField(default=dict, blank=True)  # Technical specs
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Original price for discounts
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Cost price
    
    # Inventory
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    is_in_stock = models.BooleanField(default=True)
    allow_backorder = models.BooleanField(default=False)
    
    # Media
    main_image = models.ImageField(upload_to='store/products/', null=True, blank=True)
    images = models.JSONField(default=list, blank=True)  # List of image URLs
    
    # Categorization
    categories = models.ManyToManyField(ProductCategory, related_name='products')
    tags = models.JSONField(default=list, blank=True)  # List of tags
    
    # Additional
    age_group = models.CharField(max_length=50, blank=True)  # e.g., "8-12 years"
    difficulty_level = models.CharField(max_length=20, blank=True, choices=(
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ))
    includes = models.TextField(blank=True)  # What's included in the kit
    requirements = models.TextField(blank=True)  # What else is needed
    
    # XP Reward
    xp_reward = models.PositiveIntegerField(default=0)
    
    # Status
    is_featured = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_digital = models.BooleanField(default=False)
    digital_file = models.FileField(upload_to='store/digital/', null=True, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Shipping
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            import random
            prefix = dict(self.PRODUCT_TYPES).get(self.product_type, 'PRD')[:3].upper()
            self.sku = f"{prefix}-{random.randint(10000, 99999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    @property
    def in_stock(self):
        return self.stock > 0 or self.allow_backorder
    
    @property
    def is_on_sale(self):
        return self.compare_price and self.compare_price > self.price


class Cart(TimeStampedModel):
    """Shopping cart model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_key = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    @property
    def total_items(self):
        return self.cart_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
    
    @property
    def subtotal(self):
        total = self.cart_items.aggregate(total=Sum(F('quantity') * F('product__price')))['total']
        return total or 0


class CartItem(TimeStampedModel):
    """Individual cart item"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    @property
    def total_price(self):
        return self.quantity * self.product.price


class Order(TimeStampedModel):
    """Order model"""
    
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    # User Info
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    order_number = models.CharField(max_length=50, unique=True)
    
    # Customer Details
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    full_name = models.CharField(max_length=200)
    
    # Shipping Details
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_county = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    
    # Billing Details (optional - can be same as shipping)
    billing_address = models.TextField(blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_county = models.CharField(max_length=100, blank=True)
    
    # Order Details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)  # mpesa, card, etc.
    transaction_id = models.CharField(max_length=200, blank=True)
    
    # Shipping
    tracking_number = models.CharField(max_length=100, blank=True)
    shipping_carrier = models.CharField(max_length=100, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"EFZ-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    @property
    def is_completed(self):
        return self.order_status in ['delivered', 'cancelled', 'refunded']


class OrderItem(TimeStampedModel):
    """Individual order item"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class Wishlist(TimeStampedModel):
    """User wishlist"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class ProductReview(TimeStampedModel):
    """Product reviews and ratings"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"


class Coupon(TimeStampedModel):
    """Discount coupons"""
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=(
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ))
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.code
    
    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_to and self.used_count < self.usage_limit


class Payment(TimeStampedModel):
    """Payment transactions"""
    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=200, unique=True, blank=True)
    payment_details = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.transaction_id or self.id} - {self.amount}"


class Address(TimeStampedModel):
    """User addresses for shipping/billing"""
    ADDRESS_TYPES = (
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
        ('both', 'Both'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='both')
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Kenya')
    is_default = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.county}"


class CouponUsage(TimeStampedModel):
    """Track coupon usage per user"""
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_usages')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='coupon_usages')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-used_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.coupon.code} - {self.discount_amount}"


# ============================================================
# AI E-Lab / Student Intelligence models (with error handling)
# ============================================================

try:
    from .elab_ai_models import ELabProject, ELabMilestone, StudentAIInsight, AIChatLog
except ImportError:
    # If elab_ai_models doesn't exist, define placeholder classes
    class ELabProject(models.Model):
        class Meta:
            managed = False
            db_table = 'elab_project_placeholder'
    
    class ELabMilestone(models.Model):
        class Meta:
            managed = False
            db_table = 'elab_milestone_placeholder'
    
    class StudentAIInsight(models.Model):
        class Meta:
            managed = False
            db_table = 'student_ai_insight_placeholder'
    
    class AIChatLog(models.Model):
        class Meta:
            managed = False
            db_table = 'ai_chat_log_placeholder'
    
    print("Warning: elab_ai_models.py not found. Using placeholder E-Lab models.")
except Exception as e:
    print(f"Error importing E-Lab models: {e}")
    # Define placeholder classes
    class ELabProject(models.Model):
        class Meta:
            managed = False
            db_table = 'elab_project_placeholder'
    
    class ELabMilestone(models.Model):
        class Meta:
            managed = False
            db_table = 'elab_milestone_placeholder'
    
    class StudentAIInsight(models.Model):
        class Meta:
            managed = False
            db_table = 'student_ai_insight_placeholder'
    
    class AIChatLog(models.Model):
        class Meta:
            managed = False
            db_table = 'ai_chat_log_placeholder'
