"""
Admin interface for verification models.
"""
from django.contrib import admin
from django.utils import timezone
from .models import SeniorProfile, PhoneVerification, SeniorRegistration


@admin.register(SeniorProfile)
class SeniorProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for managing senior verification requests.
    """
    list_display = (
        "user",
        "status",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )
    list_filter = ("status", "created_at", "reviewed_at")
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "proof_summary",
    )
    raw_id_fields = ("user", "reviewed_by")
    readonly_fields = ("id", "created_at", "updated_at")
    
    fieldsets = (
        ("User Information", {
            "fields": ("user", "proof_summary")
        }),
        ("Review Status", {
            "fields": ("status", "reviewed_by", "reviewed_at", "admin_notes")
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    actions = ["approve_seniors", "reject_seniors"]
    
    def approve_seniors(self, request, queryset):
        """
        Bulk action to approve selected senior profiles.
        Sets reviewed_by and reviewed_at automatically.
        """
        count = 0
        for profile in queryset.filter(status="pending"):
            profile.status = "approved"
            profile.reviewed_by = request.user
            profile.reviewed_at = timezone.now()
            profile.save()
            count += 1
        
        self.message_user(
            request,
            f"Successfully approved {count} senior profile(s). Approval emails sent."
        )
    approve_seniors.short_description = "Approve selected senior profiles"
    
    def reject_seniors(self, request, queryset):
        """
        Bulk action to reject selected senior profiles.
        """
        count = 0
        for profile in queryset.filter(status="pending"):
            profile.status = "rejected"
            profile.reviewed_by = request.user
            profile.reviewed_at = timezone.now()
            profile.save()
            count += 1
        
        self.message_user(
            request,
            f"Successfully rejected {count} senior profile(s)."
        )
    reject_seniors.short_description = "Reject selected senior profiles"
    
    def save_model(self, request, obj, form, change):
        """
        Auto-set reviewed_by and reviewed_at when status changes.
        """
        if change and "status" in form.changed_data:
            if obj.status in ["approved", "rejected"]:
                obj.reviewed_by = request.user
                obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    """
    Admin interface for phone verification records.
    """
    list_display = (
        "phone_number",
        "user",
        "verified_at",
        "expires_at",
        "is_expired",
        "created_at",
    )
    list_filter = ("verified_at", "created_at")
    search_fields = ("phone_number", "user__username", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "is_expired")
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("Phone Information", {
            "fields": ("phone_number", "user")
        }),
        ("Verification", {
            "fields": ("otp_code", "expires_at", "verified_at", "is_expired")
        }),
        ("Metadata", {
            "fields": ("id", "created_at"),
            "classes": ("collapse",)
        }),
    )



@admin.register(SeniorRegistration)
class SeniorRegistrationAdmin(admin.ModelAdmin):
    """
    Admin interface for managing detailed senior registrations from seniors-frontend.
    """
    list_display = (
        "full_name",
        "call_name",
        "college_email",
        "partner_college",
        "graduation_year",
        "status",
        "created_at",
    )
    list_filter = ("status", "partner_college", "graduation_year", "branch", "created_at")
    search_fields = (
        "full_name",
        "call_name",
        "college_email",
        "personal_email",
        "phone",
        "student_id",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    
    fieldsets = (
        ("Basic Information", {
            "fields": (
                "full_name",
                "call_name",
                "college_email",
                "personal_email",
                "phone",
            )
        }),
        ("Academic Details", {
            "fields": (
                "partner_college",
                "graduation_year",
                "branch",
                "student_id",
                "current_status",
            )
        }),
        ("Verification", {
            "fields": (
                "id_card_image",
                "college_email_verified",
                "phone_verified",
            )
        }),
        ("Application Essays", {
            "fields": (
                "why_join",
                "best_experience",
                "advice_to_juniors",
                "skills_gained",
            ),
            "classes": ("collapse",)
        }),
        ("Review Status", {
            "fields": (
                "status",
                "reviewed_by",
                "reviewed_at",
                "admin_notes",
                "user",
            )
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    actions = ["approve_and_create_accounts", "reject_registrations"]
    
    def approve_and_create_accounts(self, request, queryset):
        """
        Bulk action to approve registrations and create user accounts.
        """
        from accounts.models import User
        from django.utils import timezone
        
        count = 0
        for registration in queryset.filter(status="pending"):
            try:
                # Create username from college email
                username = registration.college_email.split('@')[0]
                
                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    self.message_user(
                        request,
                        f"User {username} already exists. Skipping {registration.full_name}.",
                        level='warning'
                    )
                    continue
                
                # Create user account
                user = User.objects.create_user(
                    username=username,
                    email=registration.personal_email,
                    first_name=registration.call_name,
                )
                
                # Create SeniorProfile
                SeniorProfile.objects.create(
                    user=user,
                    proof_summary=f"""
Registration Details:
College: {registration.partner_college}
Year: {registration.graduation_year}
Branch: {registration.branch}

Why Join: {registration.why_join}

Best Experience: {registration.best_experience}

Advice: {registration.advice_to_juniors}

Skills: {registration.skills_gained}
                    """.strip(),
                    status='approved'
                )
                
                # Update registration
                registration.user = user
                registration.status = 'approved'
                registration.reviewed_by = request.user
                registration.reviewed_at = timezone.now()
                registration.save()
                
                # Send approval email
                from .services import send_senior_approved_email
                send_senior_approved_email(user)
                
                count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Error processing {registration.full_name}: {str(e)}",
                    level='error'
                )
        
        self.message_user(
            request,
            f"Successfully approved {count} registration(s) and created user accounts."
        )
    approve_and_create_accounts.short_description = "Approve and create user accounts"
    
    def reject_registrations(self, request, queryset):
        """
        Bulk action to reject selected registrations.
        """
        from django.utils import timezone
        
        count = 0
        for registration in queryset.filter(status="pending"):
            registration.status = "rejected"
            registration.reviewed_by = request.user
            registration.reviewed_at = timezone.now()
            registration.save()  # This will trigger the signal to send rejection email
            count += 1
        
        self.message_user(
            request,
            f"Successfully rejected {count} registration(s). Rejection emails sent."
        )
    reject_registrations.short_description = "Reject selected registrations"
