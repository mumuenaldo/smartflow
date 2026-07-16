from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Department, Document, Status,
    Workflow, Assignment, Notification, Comment, AuditLog
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'get_full_name', 'email', 'role', 'department', 'is_active')
    list_filter = ('role', 'department', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('SmartFlow Info', {'fields': ('role', 'department')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('dept_name', 'location', 'created_at')
    search_fields = ('dept_name',)


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('status_name', 'status_code', 'description')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('reference_no', 'title', 'department', 'submitted_by', 'status', 'created_at')
    list_filter = ('status', 'department', 'requires_approval')
    search_fields = ('title', 'reference_no')
    date_hierarchy = 'created_at'


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('document', 'current_step', 'status', 'assigned_to', 'started_at')
    list_filter = ('status',)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('document', 'assigned_to', 'assigned_by', 'assigned_at', 'due_date')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'message', 'is_read', 'sent_at')
    list_filter = ('type', 'is_read')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'created_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'entity_type', 'entity_id', 'ip_address')
    list_filter = ('action', 'entity_type')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)