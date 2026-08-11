from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Avg, Count, Sum

# Import application models. Keep broad import to match existing project pattern.
from .models import *

# ============================================================
# REGISTER ALL MODELS FIRST (ensures everything appears)
# ============================================================

# NOTE: Only include models here that do NOT have a dedicated @admin.register(...)
# ModelAdmin class further down in this file. Every other model below is already
# registered via those decorators. CartItem is the only model here with no custom ModelAdmin.
models_to_register = [
    CartItem,
]

for model in models_to_register:
    try:
        admin.site.register(model)
    except Exception:
        pass

# ============================================================
# READATHON / INTERVENTION / SIMPLE REGISTRATIONS
# ============================================================

try:
    admin.site.register(ReadathonReport)
except Exception:
    pass

try:
    admin.site.register(InterventionNote)
except Exception:
    pass

# ============================================================
# AI E-LAB MODELS
# ============================================================

try:
    from .elab_ai_models import ELabProject, ELabMilestone, StudentAIInsight, AIChatLog
    admin.site.register(ELabProject)
    admin.site.register(ELabMilestone)
    admin.site.register(StudentAIInsight)
    admin.site.register(AIChatLog)
except ImportError:
    pass
except Exception:
    pass

# ============================================================
# ENHANCED ADMIN FOR MARITIME ACADEMY
# ============================================================

try:
    from .maritime_models import MaritimeCourse, MaritimeEnrollment, MaritimeContent

    try:
        admin.site.unregister(MaritimeCourse)
    except Exception:
        pass

    class MaritimeContentInline(admin.TabularInline):
        model = MaritimeContent
        fields = ('title', 'content_type', 'order', 'is_published', 'file', 'external_url')
        extra = 1
        show_change_link = True

    @admin.register(MaritimeCourse)
    class MaritimeCourseAdmin(admin.ModelAdmin):
        list_display = ['code', 'title', 'track', 'credits', 'duration_weeks', 'order', 'created_at']
        list_filter = ['track', 'credits', 'duration_weeks']
        search_fields = ['code', 'title', 'summary']
        ordering = ['track', 'order', 'code']
        readonly_fields = ['created_at', 'updated_at']
        inlines = [MaritimeContentInline]
        prepopulated_fields = {'code': ('title',)}

    try:
        admin.site.unregister(MaritimeEnrollment)
    except Exception:
        pass

    @admin.register(MaritimeEnrollment)
    class MaritimeEnrollmentAdmin(admin.ModelAdmin):
        list_display = [
            'user', 'course', 'track', 'status', 'amount_paid', 'payment_phone', 'transaction_code',
            'access_code_sent', 'access_code_used', 'access_code_expires_at', 'enrolled_at'
        ]
        list_filter = ['status', 'track', 'access_code_sent', 'access_code_used']
        search_fields = ['user__username', 'transaction_code', 'course__code', 'course__title']
        readonly_fields = [
            'enrolled_at', 'updated_at', 'payment_confirmed_at', 'access_code_hash',
            'access_code_expires_at', 'access_code_sent', 'access_code_used'
        ]
        actions = ['action_confirm_payment']

        def action_confirm_payment(self, request, queryset):
            count = 0
            for enrollment in queryset:
                if enrollment.status not in ('awaiting_activation', 'confirmed'):
                    enrollment.confirm_payment(confirmed_by_user=request.user)
                    count += 1
            self.message_user(request, f"{count} enrollments confirmed.")
        action_confirm_payment.short_description = "Confirm payment and issue access codes"

    try:
        admin.site.unregister(MaritimeContent)
    except Exception:
        pass

    @admin.register(MaritimeContent)
    class MaritimeContentAdmin(admin.ModelAdmin):
        list_display = ['title', 'course', 'content_type', 'order', 'is_published', 'created_at']
        list_filter = ['content_type', 'is_published', 'course']
        search_fields = ['title', 'body', 'external_url']
        raw_id_fields = ['course']
        readonly_fields = ['created_at', 'updated_at']
        ordering = ['course', 'order', 'created_at']
        fieldsets = (
            (None, {
                'fields': ('course', 'title', 'slug', 'content_type', 'order', 'is_published')
            }),
            ('Content', {
                'fields': ('body', 'file', 'external_url')
            }),
            ('Timestamps', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )

except ImportError:
    # maritime_models not present in this environment
    pass
except Exception:
    # swallow registration errors to avoid breaking admin autodiscover
    pass

# ============================================================
# 🛒 STORE ADMIN REGISTRATIONS
# ============================================================

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon_display', 'is_active', 'order', 'product_count']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    
    def icon_display(self, obj):
        return obj.icon if obj.icon else '📦'
    icon_display.short_description = 'Icon'
    
    def product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name_display', 'sku', 'product_type_badge', 'price_display', 
        'stock_status', 'is_active_badge', 'is_featured_badge'
    ]
    list_filter = ['product_type', 'is_active', 'is_featured', 'is_best_seller', 'categories']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['slug', 'sku', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['categories']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'sku', 'product_type', 'categories')
        }),
        ('Description', {
            'fields': ('short_description', 'description', 'specifications')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price', 'cost')
        }),
        ('Inventory', {
            'fields': ('stock', 'low_stock_threshold', 'is_in_stock', 'allow_backorder')
        }),
        ('Media', {
            'fields': ('main_image', 'images')
        }),
        ('Additional', {
            'fields': ('age_group', 'difficulty_level', 'includes', 'requirements', 'xp_reward')
        }),
        ('Status', {
            'fields': ('is_featured', 'is_best_seller', 'is_active', 'is_digital', 'digital_file')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description')
        }),
        ('Shipping', {
            'fields': ('weight',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def name_display(self, obj):
        return format_html('<strong>{}</strong>', obj.name[:40])
    name_display.short_description = 'Name'
    
    def price_display(self, obj):
        if obj.compare_price and obj.compare_price > obj.price:
            return format_html(
                '<span style="color:#DC2626;font-weight:bold;">KES {}</span> '
                '<span style="text-decoration:line-through;color:#9CA3AF;">KES {}</span>',
                obj.price, obj.compare_price
            )
        return format_html('<span style="font-weight:bold;">KES {}</span>', obj.price)
    price_display.short_description = 'Price'
    
    def product_type_badge(self, obj):
        colors = {
            'science_kit': '#16A34A',
            'electronics': '#3B82F6',
            'book': '#8B5CF6',
            'merchandise': '#F59E0B',
            'digital': '#EC4899',
            'robotics_kit': '#DC2626',
        }
        color = colors.get(obj.product_type, '#6B7280')
        label = dict(Product.PRODUCT_TYPES).get(obj.product_type, obj.product_type)
        return format_html(
            '<span style="background:{}20;color:{};padding:2px 10px;border-radius:12px;font-size:0.7rem;">{}</span>',
            color, color, label
        )
    product_type_badge.short_description = 'Type'
    
    def stock_status(self, obj):
        if obj.stock <= 0:
            if obj.allow_backorder:
                return format_html('<span style="color:#F59E0B;">⏳ Backorder</span>')
            return format_html('<span style="color:#DC2626;">❌ Out of Stock</span>')
        elif obj.stock <= obj.low_stock_threshold:
            return format_html('<span style="color:#F59E0B;">⚠️ Low Stock ({})</span>', obj.stock)
        return format_html('<span style="color:#16A34A;">✅ In Stock ({})</span>', obj.stock)
    stock_status.short_description = 'Stock'
    
    def is_active_badge(self, obj):
        return format_html(
            '<span style="color:{};">●</span> {}',
            '#16A34A' if obj.is_active else '#DC2626',
            'Active' if obj.is_active else 'Inactive'
        )
    is_active_badge.short_description = 'Status'
    
    def is_featured_badge(self, obj):
        return '⭐' if obj.is_featured else '—'
    is_featured_badge.short_description = 'Featured'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number_link', 'customer_name', 'email', 
        'total_display', 'order_status_badge', 'payment_status_badge', 
        'created_at_ago'
    ]
    list_filter = ['order_status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'full_name', 'email', 'phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'order_status', 'payment_status')
        }),
        ('Customer', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_county', 'shipping_postal_code')
        }),
        ('Billing', {
            'fields': ('billing_address', 'billing_city', 'billing_county')
        }),
        ('Payment', {
            'fields': ('payment_method', 'transaction_id')
        }),
        ('Totals', {
            'fields': ('subtotal', 'shipping_cost', 'tax', 'discount', 'total')
        }),
        ('Shipping Info', {
            'fields': ('tracking_number', 'shipping_carrier', 'estimated_delivery')
        }),
        ('Notes', {
            'fields': ('notes', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_number_link(self, obj):
        url = reverse('admin:api_order_change', args=[obj.id])
        return format_html('<a href="{}"><strong>{}</strong></a>', url, obj.order_number)
    order_number_link.short_description = 'Order #'
    
    def customer_name(self, obj):
        return obj.full_name or obj.user.get_full_name() if obj.user else 'Guest'
    customer_name.short_description = 'Customer'
    
    def total_display(self, obj):
        return format_html('<span style="font-weight:bold;">KES {}</span>', obj.total)
    total_display.short_description = 'Total'
    
    def order_status_badge(self, obj):
        colors = {
            'pending': '#F59E0B',
            'processing': '#3B82F6',
            'shipped': '#8B5CF6',
            'delivered': '#16A34A',
            'cancelled': '#DC2626',
            'refunded': '#6B7280',
        }
        color = colors.get(obj.order_status, '#6B7280')
        label = dict(Order.ORDER_STATUS).get(obj.order_status, obj.order_status)
        return format_html(
            '<span style="background:{}20;color:{};padding:2px 10px;border-radius:12px;font-size:0.7rem;">{}</span>',
            color, color, label
        )
    order_status_badge.short_description = 'Order Status'
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': '#F59E0B',
            'paid': '#16A34A',
            'failed': '#DC2626',
            'refunded': '#6B7280',
        }
        color = colors.get(obj.payment_status, '#6B7280')
        label = dict(Order.PAYMENT_STATUS).get(obj.payment_status, obj.payment_status)
        return format_html(
            '<span style="background:{}20;color:{};padding:2px 10px;border-radius:12px;font-size:0.7rem;">{}</span>',
            color, color, label
        )
    payment_status_badge.short_description = 'Payment'
    
    def created_at_ago(self, obj):
        delta = timezone.now() - obj.created_at
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60}m ago"
        return "Just now"
    created_at_ago.short_description = 'Created'
    
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    
    def mark_as_processing(self, request, queryset):
        queryset.update(order_status='processing')
        self.message_user(request, f"{queryset.count()} orders marked as processing")
    mark_as_processing.short_description = "Mark selected as Processing"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(order_status='shipped')
        self.message_user(request, f"{queryset.count()} orders marked as shipped")
    mark_as_shipped.short_description = "Mark selected as Shipped"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(order_status='delivered')
        self.message_user(request, f"{queryset.count()} orders marked as delivered")
    mark_as_delivered.short_description = "Mark selected as Delivered"
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(order_status='cancelled')
        self.message_user(request, f"{queryset.count()} orders cancelled")
    mark_as_cancelled.short_description = "Mark selected as Cancelled"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order_link', 'product_link', 'quantity', 'price_display', 'total_display']
    search_fields = ['order__order_number', 'product__name']
    list_filter = ['order__order_status']
    
    def order_link(self, obj):
        url = reverse('admin:api_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Order'
    
    def product_link(self, obj):
        url = reverse('admin:api_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_link.short_description = 'Product'
    
    def price_display(self, obj):
        return format_html('KES {}', obj.price)
    price_display.short_description = 'Price'
    
    def total_display(self, obj):
        return format_html('<strong>KES {}</strong>', obj.total)
    total_display.short_description = 'Total'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'product_link', 'created_at']
    search_fields = ['user__username', 'product__name']
    list_filter = ['created_at']
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return obj.session_key or 'Guest'
    user_link.short_description = 'User'
    
    def product_link(self, obj):
        return format_html('<a href="{}">{}</a>', reverse('admin:api_product_change', args=[obj.product.id]), obj.product.name)
    product_link.short_description = 'Product'


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'product_link', 'rating_stars', 'title', 'is_verified_purchase', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'created_at']
    search_fields = ['user__username', 'product__name', 'comment']
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def product_link(self, obj):
        url = reverse('admin:api_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_link.short_description = 'Product'
    
    def rating_stars(self, obj):
        return '⭐' * obj.rating + '☆' * (5 - obj.rating)
    rating_stars.short_description = 'Rating'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type_badge', 'discount_value_display', 'valid_dates', 'is_active_badge', 'usage']
    list_filter = ['is_active', 'discount_type']
    search_fields = ['code', 'description']
    readonly_fields = ['used_count']
    
    def discount_type_badge(self, obj):
        return '💯' if obj.discount_type == 'percentage' else '💰'
    discount_type_badge.short_description = 'Type'
    
    def discount_value_display(self, obj):
        if obj.discount_type == 'percentage':
            return format_html('<span style="font-weight:bold;">{}%</span>', obj.discount_value)
        return format_html('<span style="font-weight:bold;">KES {}</span>', obj.discount_value)
    discount_value_display.short_description = 'Value'
    
    def valid_dates(self, obj):
        return format_html(
            '{}<br/><span style="color:#9CA3AF;">to {}</span>',
            obj.valid_from.strftime('%Y-%m-%d'),
            obj.valid_to.strftime('%Y-%m-%d')
        )
    valid_dates.short_description = 'Valid'
    
    def is_active_badge(self, obj):
        if obj.is_valid:
            return format_html('<span style="color:#16A34A;">✅ Active</span>')
        return format_html('<span style="color:#DC2626;">❌ Expired</span>')
    is_active_badge.short_description = 'Status'
    
    def usage(self, obj):
        return format_html('{}/{}', obj.used_count, obj.usage_limit)
    usage.short_description = 'Used'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_link', 'total_items', 'subtotal_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'session_key']
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return obj.session_key or 'Guest'
    user_link.short_description = 'User'
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Items'
    
    def subtotal_display(self, obj):
        return format_html('KES {}', obj.subtotal)
    subtotal_display.short_description = 'Subtotal'

# ============================================================
# ENHANCED ADMIN FOR USERBOOK (Unregister and Re-register)
# ============================================================

try:
    admin.site.unregister(UserBook)
except Exception:
    pass

@admin.register(UserBook)
class UserBookAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'progress', 'current_page', 'reading_minutes', 'completed', 'last_read_at']
    list_filter = ['completed', 'bookmarked', 'last_read_at']
    search_fields = ['user__username', 'user__email', 'book__title']
    ordering = ['-last_read_at']
    readonly_fields = ['last_read_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'book')

# ============================================================
# ENHANCED ADMIN FOR BOOK
# ============================================================

try:
    admin.site.unregister(Book)
except Exception:
    pass

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'pages', 'is_published', 'is_featured']
    list_filter = ['is_published', 'is_featured', 'category']
    search_fields = ['title', 'author']
    readonly_fields = ['created_at', 'updated_at']

# ============================================================
# ENHANCED ADMIN FOR STUDENT SCORE
# ============================================================

try:
    admin.site.unregister(StudentScore)
except Exception:
    pass

@admin.register(StudentScore)
class StudentScoreAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'score', 'max_score', 'created_at']
    list_filter = ['topic', 'created_at']
    search_fields = ['user__username', 'user__email', 'topic']
    ordering = ['-created_at']

# ============================================================
# ENHANCED ADMIN FOR PROFILE
# ============================================================

try:
    admin.site.unregister(Profile)
except Exception:
    pass

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'school', 'county', 'phone']
    list_filter = ['user_type', 'county']
    search_fields = ['user__username', 'user__email', 'phone', 'school']

# ============================================================
# ENHANCED ADMIN FOR PROGRAM
# ============================================================

try:
    admin.site.unregister(Program)
except Exception:
    pass

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_active', 'created_at']
    list_filter = ['is_active', 'category']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}

# ============================================================
# ENHANCED ADMIN FOR ENROLLMENT
# ============================================================

try:
    admin.site.unregister(Enrollment)
except Exception:
    pass

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'program', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email', 'program__title', 'email', 'full_name']

# ============================================================
# ENHANCED ADMIN FOR LESSON
# ============================================================

try:
    admin.site.unregister(Lesson)
except Exception:
    pass

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_published']
    list_filter = ['is_published']
    search_fields = ['title', 'content']

# ============================================================
# ENHANCED ADMIN FOR VIDEO
# ============================================================

try:
    admin.site.unregister(Video)
except Exception:
    pass

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'topic', 'created_at']
    search_fields = ['title', 'description']

# ============================================================
# ENHANCED ADMIN FOR CONTENT ITEM
# ============================================================

try:
    admin.site.unregister(ContentItem)
except Exception:
    pass

@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'created_at']
    list_filter = ['content_type']
    search_fields = ['title']

# ============================================================
# ENHANCED ADMIN FOR ASSESSMENT
# ============================================================

try:
    admin.site.unregister(Assessment)
except Exception:
    pass

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title']

# ============================================================
# ENHANCED ADMIN FOR GENERIC RESOURCE
# ============================================================

try:
    admin.site.unregister(GenericResource)
except Exception:
    pass

@admin.register(GenericResource)
class GenericResourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'owner', 'resource_type', 'title', 'status', 'created_at']
    list_filter = ['resource_type', 'status', 'created_at']
    search_fields = ['owner__username', 'title', 'summary']
    ordering = ['-created_at']

# ============================================================
# ENHANCED ADMIN FOR STUDENT INTELLIGENCE PROFILE
# ============================================================

try:
    admin.site.unregister(StudentIntelligenceProfile)
except Exception:
    pass

@admin.register(StudentIntelligenceProfile)
class StudentIntelligenceProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

# ============================================================
# ENHANCED ADMIN FOR M-PESA PAYMENT
# ============================================================

try:
    admin.site.unregister(MpesaPayment)
except Exception:
    pass

@admin.register(MpesaPayment)
class MpesaPaymentAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'phone', 'user__username']
    readonly_fields = ['created_at', 'updated_at']

# ============================================================
# ENHANCED ADMIN FOR READATHON REPORT
# ============================================================

try:
    admin.site.unregister(ReadathonReport)
except Exception:
    pass

@admin.register(ReadathonReport)
class ReadathonReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'report_type', 'title', 'delivery_status', 'created_at']
    list_filter = ['report_type', 'delivery_status']
    search_fields = ['user__username', 'title']

# ============================================================
# ENHANCED ADMIN FOR INTERVENTION NOTE
# ============================================================

try:
    admin.site.unregister(InterventionNote)
except Exception:
    pass

@admin.register(InterventionNote)
class InterventionNoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['user__username', 'title']

# ============================================================
# ENHANCED ADMIN FOR E-LAB PROJECTS (if available)
# ============================================================

try:
    from .elab_ai_models import ELabProject, ELabMilestone, StudentAIInsight, AIChatLog
    
    try:
        admin.site.unregister(ELabProject)
    except Exception:
        pass
    
    @admin.register(ELabProject)
    class ELabProjectAdmin(admin.ModelAdmin):
        list_display = ['title', 'category', 'stage', 'created_at']
        list_filter = ['category', 'stage']
        search_fields = ['title', 'description']
    
    try:
        admin.site.unregister(ELabMilestone)
    except Exception:
        pass
    
    @admin.register(ELabMilestone)
    class ELabMilestoneAdmin(admin.ModelAdmin):
        list_display = ['title', 'project', 'status', 'due_date']
        list_filter = ['status']
    
    try:
        admin.site.unregister(StudentAIInsight)
    except Exception:
        pass
    
    @admin.register(StudentAIInsight)
    class StudentAIInsightAdmin(admin.ModelAdmin):
        list_display = ['id']
    
    try:
        admin.site.unregister(AIChatLog)
    except Exception:
        pass
    
    @admin.register(AIChatLog)
    class AIChatLogAdmin(admin.ModelAdmin):
        list_display = ['agent', 'module', 'created_at']
        list_filter = ['agent', 'module']
        search_fields = ['prompt', 'response']
        
except ImportError:
    pass
except Exception:
    pass