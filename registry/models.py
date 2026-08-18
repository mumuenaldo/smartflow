from django.conf import settings  # ⭐ ADD THIS IMPORT
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import qrcode
from django.core.files.base import ContentFile
from io import BytesIO
import uuid

# ─────────────────────────────────────────────
# CUSTOM USER MANAGER 
# ─────────────────────────────────────────────
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        email = self.normalize_email(email) if email else ''
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(username, email, password, **extra_fields)


# ─────────────────────────────────────────────
# 1. DEPARTMENT
# ─────────────────────────────────────────────
class Department(models.Model):
    dept_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.dept_name

    class Meta:
        ordering = ['dept_name']


# ─────────────────────────────────────────────
# 2. CUSTOM USER 
# ─────────────────────────────────────────────
class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('clerk', 'Registry Clerk'),
        ('supervisor', 'Supervisor'),
        ('staff', 'Staff Member'),
        ('admin', 'Administrator'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='members'
    )
    
    # Student-specific fields
    student_id = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def is_student(self):
        return self.role == 'student'

    def is_clerk(self):
        return self.role == 'clerk'

    def is_supervisor(self):
        return self.role == 'supervisor'

    def is_staff_member(self):
        return self.role == 'staff'

    def is_administrator(self):
        return self.role == 'admin' or self.is_superuser

    def can_submit_documents(self):
        return self.is_authenticated

    def can_approve_documents(self):
        return self.is_supervisor() or self.is_administrator()

    def can_view_all_documents(self):
        return self.is_supervisor() or self.is_administrator() or self.is_clerk()

    def can_manage_users(self):
        return self.is_administrator()

    class Meta:
        ordering = ['username']


# ─────────────────────────────────────────────
# 3. STATUS
# ─────────────────────────────────────────────
class Status(models.Model):
    status_name = models.CharField(max_length=50)
    status_code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_visible_to_student = models.BooleanField(default=True)

    def __str__(self):
        return self.status_name

    class Meta:
        verbose_name_plural = 'Statuses'


# ─────────────────────────────────────────────
# 4. DOCUMENT 
# ─────────────────────────────────────────────
class Document(models.Model):
    PRIORITY_CHOICES = [
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🟠 High'),
        ('urgent', '🔴 Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    reference_no = models.CharField(max_length=50, unique=True, blank=True)
    document_type = models.CharField(max_length=100, blank=True)
    file_path = models.FileField(upload_to='documents/', blank=True, null=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True,
        related_name='documents'
    )
    submitted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='submitted_documents'
    )
    status = models.ForeignKey(
        Status, on_delete=models.SET_NULL, null=True,
        related_name='documents'
    )
    requires_approval = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    escalation_level = models.IntegerField(default=0)
    escalated_at = models.DateTimeField(null=True, blank=True)
    
    student_requester = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='student_requests',
        limit_choices_to={'role': 'student'}
    )
    
    tracking_history = models.JSONField(default=list, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    last_activity_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='last_activities'
    )

    def __str__(self):
        return f"{self.reference_no} — {self.title}"

    def get_status_display_for_student(self):
        if self.status and self.status.is_visible_to_student:
            return self.status.status_name
        return "In Progress"

    # ✅ QR CODE GENERATION — FIXED!
    def generate_qr_code(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"{settings.SITE_URL}/verify/{self.reference_no}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0d3b6e", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        self.qr_code.save(f"qr_{self.reference_no}.png", ContentFile(buffer.getvalue()), save=False)

    def save(self, *args, **kwargs):
        if not self.reference_no:
            unique_suffix = str(uuid.uuid4()).upper()[:6]
            self.reference_no = f"SF-2026-{unique_suffix}"
            
        if not self.qr_code:
            self.generate_qr_code()

        super(Document, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']


# ─────────────────────────────────────────────
# 5. WORKFLOW
# ─────────────────────────────────────────────
class Workflow(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
        ('archived', 'Archived'),
        ('cancelled', 'Cancelled'),
    ]
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE,
        related_name='workflows'
    )
    current_step = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_workflows'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Workflow [{self.document.reference_no}] — {self.get_status_display()}"

    class Meta:
        ordering = ['-started_at']


# ─────────────────────────────────────────────
# 6. ASSIGNMENT
# ─────────────────────────────────────────────
class Assignment(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE,
        related_name='assignments'
    )
    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='received_assignments'
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='given_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.document.reference_no} → {self.assigned_to.username}"


# ─────────────────────────────────────────────
# 7. NOTIFICATION
# ─────────────────────────────────────────────
class Notification(models.Model):
    TYPE_CHOICES = [
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
        ('assignment', 'Assignment'),
        ('reminder', 'Reminder'),
        ('system', 'System'),
        ('status_update', 'Status Update'),
        ('escalation', 'Escalation'),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='notifications'
    )
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notifications'
    )
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.type}] → {self.user.username}: {self.message[:40]}"

    class Meta:
        ordering = ['-sent_at']


# ─────────────────────────────────────────────
# 8. COMMENT
# ─────────────────────────────────────────────
class Comment(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='comments'
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    visible_to_student = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} on {self.document.reference_no}"

    class Meta:
        ordering = ['created_at']


# ─────────────────────────────────────────────
# 9. AUDIT LOG
# ─────────────────────────────────────────────
class AuditLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50)
    entity_id = models.IntegerField(null=True, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, blank=True)

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user} — {self.action}"

    class Meta:
        ordering = ['-timestamp']


# ─────────────────────────────────────────────
# 10. LEARN MORE PAGE CONTENT
# ─────────────────────────────────────────────
class LearnMoreContent(models.Model):
    section_title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.section_title

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Learn More Content'


# ─────────────────────────────────────────────
# 11. FAQ
# ─────────────────────────────────────────────
class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.question

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'FAQs'