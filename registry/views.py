# ============================================
# SMARTFLOW - COMPLETE VIEWS.PY
# ============================================
# Developed by Munashe Muza (T2420016)
# TelOne Centre for Learning
# ============================================

import csv
import io
import json
import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.db.models import Avg, Count, ExpressionWrapper, F, fields, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ─────────────────────────────────────────────
# WEBSOCKET / CHANNELS IMPORTS FOR LIVE UPDATES
# ─────────────────────────────────────────────
try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    from .utils import get_workflow_chart_data, get_student_progress_data
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False

from .forms import (
    AdminRegistrationForm, ApprovalForm, AssignDocumentForm,
    BulkUploadForm, ClerkRegistrationForm, CommentForm,
    DepartmentForm, DocumentForm, LoginForm,
    ProfileUpdateForm, StaffRegistrationForm,
    StudentRegistrationForm, SupervisorRegistrationForm,
    UserCreateForm
)
from .models import Assignment, AuditLog, Comment, Department, Document, Notification, Status, User, Workflow

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def log_action(request, action, entity_type, entity_id=None, details=''):
    if request.user.is_authenticated:
        ip = request.META.get('REMOTE_ADDR', '')
        AuditLog.objects.create(
            user=request.user,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip,
        )

def notify_user(user, document, msg, ntype='system'):
    Notification.objects.create(
        user=user,
        document=document,
        message=msg,
        type=ntype,
    )
    try:
        send_mail(
            subject=f'SmartFlow — {ntype.capitalize()} Notification',
            message=msg,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass

def role_required(*roles):
    def decorator(view_func):
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, "You do not have permission to access that page.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

def admin_key_required(view_func):
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.role == 'admin' and not request.session.get('admin_verified', False):
            if request.resolver_match.view_name == 'admin_welcome':
                return view_func(request, *args, **kwargs)
            messages.warning(request, "Please enter your security credentials to access the console dashboard.")
            return redirect('admin_welcome')
        return view_func(request, *args, **kwargs)
    return _wrapped

def add_tracking_entry(document, user, action, details, request=None):
    tracking_entry = {
        'timestamp': timezone.now().isoformat(),
        'user': user.get_full_name() or user.username,
        'user_role': user.role,
        'action': action,
        'details': details,
        'ip_address': request.META.get('REMOTE_ADDR', '') if request else '',
    }
    
    if not document.tracking_history:
        document.tracking_history = []
    
    document.tracking_history.append(tracking_entry)
    document.last_activity = timezone.now()
    document.last_activity_by = user
    document.save(update_fields=['tracking_history', 'last_activity', 'last_activity_by'])
    
    if request:
        log_action(request, action, 'Document', document.id, details)
    
    if CHANNELS_AVAILABLE:
        try:
            channel_layer = get_channel_layer()
            latest_workflow = document.workflows.last()
            payload = {
                'action': action,
                'details': details,
                'timestamp': tracking_entry['timestamp'],
                'user': tracking_entry['user'],
                'status_code': document.status.status_code if document.status else 'pending',
                'status_name': document.status.status_name if document.status else 'Pending',
                'current_step': latest_workflow.current_step if latest_workflow else action.replace('_', ' ').title(),
                'workflow_status': latest_workflow.status if latest_workflow else 'pending',
                'updated_at': document.updated_at.isoformat() if document.updated_at else tracking_entry['timestamp'],
            }
            async_to_sync(channel_layer.group_send)(
                f"document_{document.id}",
                {"type": "document_update", "data": payload}
            )
        except Exception as e:
            print(f"Document WebSocket broadcast failed: {e}")
    
    if CHANNELS_AVAILABLE and document.student_requester:
        try:
            channel_layer = get_channel_layer()
            progress_data = get_student_progress_data(document.student_requester)
            async_to_sync(channel_layer.group_send)(
                f"student_progress_{document.student_requester.id}",
                {"type": "progress_update", "data": progress_data}
            )
        except Exception as e:
            print(f"Student progress WebSocket broadcast failed: {e}")
    
    return tracking_entry

def get_greeting():
    current_hour = datetime.now().hour
    if current_hour < 12:
        return "Good morning"
    elif current_hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"

# ─────────────────────────────────────────────
# PUBLIC PAGES
# ─────────────────────────────────────────────

def landing_page(request):
    if request.user.is_authenticated:
        if request.user.role == 'student':
            return redirect('student_dashboard')
        elif request.user.role == 'admin':
            return redirect('admin_welcome')
        return redirect('dashboard')
    return render(request, 'registry/landing.html')

def learn_more(request):
    return render(request, 'registry/learn_more.html')

def role_selection(request):
    return render(request, 'registry/role_selection.html')

# ─────────────────────────────────────────────
# REGISTRATION VIEWS
# ─────────────────────────────────────────────

def register_student(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = StudentRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'student'
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        login(request, user)
        messages.success(request, 'Student account created successfully!')
        return redirect('student_dashboard')
    
    return render(request, 'registry/register.html', {'form': form, 'role': 'Student'})

def register_clerk(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = ClerkRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'clerk'
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        messages.success(request, 'Clerk account created. Please log in.')
        return redirect('login')
    
    return render(request, 'registry/register.html', {'form': form, 'role': 'Registry Clerk'})

def register_staff(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = StaffRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'staff'
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        messages.success(request, 'Staff account created. Please log in.')
        return redirect('login')
    
    return render(request, 'registry/register.html', {'form': form, 'role': 'Staff Member'})

def register_supervisor(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = SupervisorRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'supervisor'
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        messages.success(request, 'Supervisor account created. Please log in.')
        return redirect('login')
    
    return render(request, 'registry/register.html', {'form': form, 'role': 'Supervisor'})

def register_admin(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if User.objects.filter(role='admin').exists():
        messages.error(request, 'Admin registration is restricted.')
        return redirect('landing_page')
    
    form = AdminRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'admin'
        user.is_staff = True
        user.is_superuser = True
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        messages.success(request, 'Admin account created! Please log in.')
        return redirect('login')
    
    return render(request, 'registry/register.html', {'form': form, 'role': 'Administrator'})

# ─────────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'student':
            return redirect('student_dashboard')
        elif request.user.role == 'admin':
            return redirect('admin_welcome')
        return redirect('dashboard')
    
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        log_action(request, 'LOGIN', 'User', user.id, f'{user.username} logged in')
        
        if user.role == 'student':
            return redirect('student_dashboard')
        elif user.role == 'admin':
            return redirect('admin_welcome')
        return redirect('dashboard')
    
    return render(request, 'registration/login.html', {'form': form})

@login_required
def logout_view(request):
    log_action(request, 'LOGOUT', 'User', request.user.id)
    if 'admin_verified' in request.session:
        del request.session['admin_verified']
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing_page')

# ─────────────────────────────────────────────
# DASHBOARD ROUTER
# ─────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    
    if user.role == 'student':
        return redirect('student_dashboard')
    elif user.role == 'supervisor':
        return redirect('supervisor_dashboard')
    elif user.role == 'clerk':
        return redirect('clerk_dashboard')
    elif user.role == 'staff':
        return redirect('staff_dashboard')
    elif user.role == 'admin':
        return redirect('admin_welcome')
    else:
        return redirect('landing_page')

# ─────────────────────────────────────────────
# STUDENT DASHBOARD
# ─────────────────────────────────────────────

@login_required
@role_required('student')
def student_dashboard(request):
    user = request.user
    unread = Notification.objects.filter(user=user, is_read=False).count()
    
    my_requests = Document.objects.filter(student_requester=user).order_by('-created_at')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        my_requests = my_requests.filter(status__status_code=status_filter)
    
    pending = Document.objects.filter(student_requester=user, status__status_code='pending').count()
    approved = Document.objects.filter(student_requester=user, status__status_code='approved').count()
    rejected = Document.objects.filter(student_requester=user, status__status_code='rejected').count()
    in_review = Document.objects.filter(student_requester=user, status__status_code='in_review').count()
    
    recent_notifications = Notification.objects.filter(user=user)[:5]
    
    monthly_data = []
    monthly_labels = []
    today = datetime.now().date()
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_name = month_date.strftime('%b %Y')
        monthly_labels.append(month_name)
        
        count = Document.objects.filter(
            student_requester=user,
            created_at__year=month_date.year,
            created_at__month=month_date.month
        ).count()
        monthly_data.append(count)
    
    context = {
        'greeting': get_greeting(),
        'my_requests': my_requests,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'in_review': in_review,
        'unread': unread,
        'recent_notifications': recent_notifications,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'status_filter': status_filter,
    }
    
    return render(request, 'registry/student_dashboard.html', context)

@login_required
@role_required('student')
def student_check_progress(request):
    user = request.user
    status_filter = request.GET.get('status', '')

    my_requests = Document.objects.filter(
        student_requester=user
    ).select_related('department', 'status').order_by('-created_at')

    pending = Document.objects.filter(student_requester=user, status__status_code='pending').count()
    approved = Document.objects.filter(student_requester=user, status__status_code='approved').count()
    rejected = Document.objects.filter(student_requester=user, status__status_code='rejected').count()
    in_review = Document.objects.filter(student_requester=user, status__status_code='in_review').count()

    monthly_data = []
    monthly_labels = []
    today = datetime.now().date()

    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_name = month_date.strftime('%b %Y')
        monthly_labels.append(month_name)

        count = Document.objects.filter(
            student_requester=user,
            created_at__year=month_date.year,
            created_at__month=month_date.month
        ).count()
        monthly_data.append(count)

    context = {
        'my_requests': my_requests,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'in_review': in_review,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'greeting': get_greeting(),
        'status_filter': status_filter,
    }

    return render(request, 'registry/student_check_progress.html', context)

@login_required
@role_required('student')
def student_my_requests(request):
    user = request.user
    my_requests = Document.objects.filter(student_requester=user).order_by('-created_at')
    
    context = {
        'my_requests': my_requests,
        'greeting': get_greeting(),
    }
    
    return render(request, 'registry/student_my_requests.html', context)

@login_required
@role_required('student')
def student_submit_request(request):
    departments = Department.objects.all()
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.student_requester = request.user
            doc.submitted_by = request.user
            doc.reference_no = f"STU-{uuid.uuid4().hex[:8].upper()}"
            
            target_department_id = request.POST.get('department')
            if target_department_id:
                target_department = get_object_or_404(Department, id=target_department_id)
                doc.department = target_department
                doc.current_location = target_department.dept_name
            
            pending_status, _ = Status.objects.get_or_create(
                status_code='pending',
                defaults={'status_name': 'Pending', 'description': 'Awaiting processing'}
            )
            doc.status = pending_status
            doc.save()
            
            doc.generate_qr_code()
            doc.save()
            
            add_tracking_entry(
                doc, request.user, 'SUBMITTED',
                f'Document submitted to {doc.department.dept_name if doc.department else "Registry"} Department. Reference: {doc.reference_no}',
                request
            )
            
            Workflow.objects.create(
                document=doc,
                current_step=f"Submitted to {doc.department.dept_name if doc.department else 'Registry'}",
                status='pending',
            )
            
            staff_users = User.objects.filter(role__in=['clerk', 'supervisor', 'admin'])
            if doc.department:
                dept_staff = User.objects.filter(department=doc.department, role__in=['clerk', 'supervisor'])
                if dept_staff.exists():
                    staff_users = dept_staff
            
            for staff in staff_users:
                notify_user(
                    staff, doc,
                    f'NEW STUDENT REQUEST from {request.user.get_full_name()}: {doc.title}\n'
                    f'Department: {doc.department.dept_name if doc.department else "Registry"}\n'
                    f'Reference: {doc.reference_no}',
                    ntype='assignment'
                )
            
            messages.success(request, 
                f'Your request "{doc.title}" has been submitted!\n'
                f'Reference: {doc.reference_no} | Forwarded to: {doc.department.dept_name if doc.department else "Registry"}'
            )
            
            if CHANNELS_AVAILABLE:
                try:
                    channel_layer = get_channel_layer()
                    data = get_workflow_chart_data()
                    async_to_sync(channel_layer.group_send)(
                        "workflow_updates",
                        {"type": "workflow_update", "data": data}
                    )
                except Exception as e:
                    print(f"WebSocket broadcast failed: {e}")
            
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DocumentForm()
    
    return render(request, 'registry/student_request_form.html', {
        'form': form,
        'departments': departments,
        'greeting': get_greeting(),
    })

@login_required
@role_required('student')
def student_track_request(request, pk):
    doc = get_object_or_404(Document, pk=pk, student_requester=request.user)
    workflows = doc.workflows.all()
    comments = doc.comments.filter(visible_to_student=True).select_related('user').all()
    
    add_tracking_entry(doc, request.user, 'VIEWED', 'Student viewed their request', request)
    
    context = {
        'doc': doc,
        'workflows': workflows,
        'comments': comments,
        'greeting': get_greeting(),
    }
    return render(request, 'registry/student_track.html', context)

@login_required
@role_required('student')
def student_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            log_action(request, 'PROFILE_UPDATED', 'User', request.user.id, 'Profile updated')
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('student_profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'registry/student_profile.html', {
        'form': form,
        'greeting': get_greeting(),
    })

@login_required
@role_required('student')
def cancel_request(request, pk):
    doc = get_object_or_404(Document, pk=pk, student_requester=request.user)
    
    if doc.status.status_code != 'pending':
        messages.error(request, 'Only pending requests can be cancelled.')
        return redirect('student_track', pk=pk)
    
    cancelled_status, _ = Status.objects.get_or_create(
        status_code='cancelled',
        defaults={'status_name': 'Cancelled'}
    )
    doc.status = cancelled_status
    doc.save()
    
    Comment.objects.create(document=doc, user=request.user, comment='Request cancelled by student.')
    add_tracking_entry(doc, request.user, 'CANCELLED', 'Request cancelled by student', request)
    
    wf = doc.workflows.last()
    if wf:
        wf.status = 'cancelled'
        wf.current_step = 'Cancelled'
        wf.completed_at = timezone.now()
        wf.save()
    
    staff_users = User.objects.filter(role__in=['clerk', 'supervisor', 'admin'])
    for staff in staff_users:
        notify_user(staff, doc, f'Request {doc.reference_no} has been CANCELLED by {request.user.get_full_name()}.', ntype='system')
    
    messages.success(request, 'Your request has been cancelled successfully.')
    return redirect('student_dashboard')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_action(request, 'PASSWORD_CHANGED', 'User', request.user.id)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'registry/change_password.html', {'form': form})

# ─────────────────────────────────────────────
# STAFF DASHBOARD
# ─────────────────────────────────────────────

@login_required
@role_required('staff')
def staff_dashboard(request):
    user = request.user
    unread = Notification.objects.filter(user=user, is_read=False).count()
    
    assignments_qs = Assignment.objects.filter(
        assigned_to=user
    ).select_related('document', 'document__status', 'assigned_by')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        assignments_qs = assignments_qs.filter(document__status__status_code=status_filter)
    
    pending_count = assignments_qs.filter(document__status__status_code='pending').count()
    completed_count = assignments_qs.filter(document__status__status_code='approved').count()
    total_count = assignments_qs.count()
    
    recent_assignments = assignments_qs.order_by('-assigned_at')[:10]
    
    context = {
        'greeting': get_greeting(),
        'assignments': recent_assignments,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'total_count': total_count,
        'unread': unread,
        'status_filter': status_filter,
    }
    return render(request, 'registry/staff_dashboard.html', context)

# ─────────────────────────────────────────────
# CLERK DASHBOARD
# ─────────────────────────────────────────────

@login_required
@role_required('clerk')
def clerk_dashboard(request):
    user = request.user
    unread = Notification.objects.filter(user=user, is_read=False).count()
    
    docs = Document.objects.filter(submitted_by=user).order_by('-created_at')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        docs = docs.filter(status__status_code=status_filter)
    
    total_docs = Document.objects.filter(submitted_by=user).count()
    pending = Document.objects.filter(submitted_by=user, status__status_code='pending').count()
    approved = Document.objects.filter(submitted_by=user, status__status_code='approved').count()
    rejected = Document.objects.filter(submitted_by=user, status__status_code='rejected').count()
    in_review = Document.objects.filter(submitted_by=user, status__status_code='in_review').count()
    
    context = {
        'greeting': get_greeting(),
        'docs': docs,
        'total_docs': total_docs,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'in_review': in_review,
        'unread': unread,
        'status_filter': status_filter,
    }
    
    return render(request, 'registry/clerk_dashboard.html', context)

@role_required('clerk', 'admin')
def document_register(request):
    form = DocumentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.submitted_by = request.user
        pending_status, _ = Status.objects.get_or_create(
            status_code='pending',
            defaults={'status_name': 'Pending', 'description': 'Awaiting processing'}
        )
        doc.status = pending_status
        doc.save()
        
        Workflow.objects.create(document=doc, current_step='Registered', status='pending')
        log_action(request, 'REGISTER_DOCUMENT', 'Document', doc.id, doc.title)
        messages.success(request, f'Document "{doc.title}" registered successfully.')
        
        if CHANNELS_AVAILABLE:
            try:
                channel_layer = get_channel_layer()
                data = get_workflow_chart_data()
                async_to_sync(channel_layer.group_send)(
                    "workflow_updates",
                    {"type": "workflow_update", "data": data}
                )
            except Exception as e:
                print(f"WebSocket broadcast failed: {e}")
        
        return redirect('document_list')
    
    return render(request, 'registry/document_form.html', {'form': form, 'action': 'Register'})

@role_required('clerk', 'admin')
def bulk_upload_documents(request):
    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV formatted file.')
                return redirect('bulk_upload')
            
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            
            success_count = 0
            error_count = 0
            
            pending_status, _ = Status.objects.get_or_create(
                status_code='pending',
                defaults={'status_name': 'Pending'}
            )
            
            for row in reader:
                try:
                    doc = Document.objects.create(
                        reference_no=f"BULK-{uuid.uuid4().hex[:8].upper()}",
                        title=row.get('title', 'Untitled'),
                        description=row.get('description', ''),
                        document_type=row.get('document_type', 'General'),
                        submitted_by=request.user,
                        status=pending_status,
                    )
                    
                    if row.get('department'):
                        try:
                            dept = Department.objects.get(dept_name=row['department'])
                            doc.department = dept
                            doc.save()
                        except Department.DoesNotExist:
                            pass
                    
                    Workflow.objects.create(document=doc, current_step='Registered via Bulk Upload', status='pending')
                    success_count += 1
                except Exception:
                    error_count += 1
            
            messages.success(request, f'{success_count} documents uploaded successfully!')
            if error_count > 0:
                messages.warning(request, f'{error_count} records failed verification structural checks.')
            
            log_action(request, 'BULK_UPLOAD', 'Document', None, f'Uploaded {success_count} documents')
            return redirect('document_list')
    else:
        form = BulkUploadForm()
    return render(request, 'registry/bulk_upload.html', {'form': form})

# ─────────────────────────────────────────────
# SUPERVISOR DASHBOARD
# ─────────────────────────────────────────────

@login_required
@role_required('supervisor')
def supervisor_dashboard(request):
    user = request.user
    unread = Notification.objects.filter(user=user, is_read=False).count()
    
    workflows = Workflow.objects.filter(
        Q(assigned_to=user) | Q(status='in_review')
    ).select_related('document').order_by('-started_at')[:10]
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        workflows = workflows.filter(status=status_filter)
    
    pending_approvals = Workflow.objects.filter(status='in_review').count()
    total_approved = Workflow.objects.filter(status='approved').count()
    total_rejected = Workflow.objects.filter(status='rejected').count()
    in_review = Workflow.objects.filter(status='in_review').count()
    total_pending = Workflow.objects.filter(status='pending').count()
    
    status_chart = {
        'labels': ['Pending', 'In Review', 'Approved', 'Rejected'],
        'data': [total_pending, in_review, total_approved, total_rejected],
        'colors': ['#F0A030', '#4A90D9', '#2EA86B', '#E55B5B'],
    }
    
    dept_data = Department.objects.annotate(
        doc_count=Count('documents')
    ).values('dept_name', 'doc_count').order_by('-doc_count')[:7]
    
    dept_chart = {
        'labels': [d['dept_name'] for d in dept_data] if dept_data else ['No Data'],
        'data': [d['doc_count'] for d in dept_data] if dept_data else [0],
    }
    
    monthly_labels = []
    monthly_data = []
    today = datetime.now().date()
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_name = month_date.strftime('%b %Y')
        monthly_labels.append(month_name)
        
        count = Workflow.objects.filter(
            started_at__year=month_date.year,
            started_at__month=month_date.month
        ).count()
        monthly_data.append(count)
    
    context = {
        'greeting': get_greeting(),
        'workflows': workflows,
        'pending_approvals': pending_approvals,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'in_review': in_review,
        'total_pending': total_pending,
        'unread': unread,
        'status_chart_raw': status_chart,
        'dept_chart_raw': dept_chart,
        'monthly_labels_raw': monthly_labels,
        'monthly_data_raw': monthly_data,
        'status_filter': status_filter,
    }
    return render(request, 'registry/supervisor_dashboard.html', context)

@login_required
@role_required('supervisor')
def workflow_overview(request):
    user = request.user
    unread = Notification.objects.filter(user=user, is_read=False).count()
    
    workflows = Workflow.objects.filter(
        Q(assigned_to=user) | Q(status='in_review')
    ).select_related('document', 'document__submitted_by', 'document__department').order_by('-started_at')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        workflows = workflows.filter(status=status_filter)
    
    pending_approvals = Workflow.objects.filter(status='in_review').count()
    total_approved = Workflow.objects.filter(status='approved').count()
    total_rejected = Workflow.objects.filter(status='rejected').count()
    in_review = Workflow.objects.filter(status='in_review').count()
    total_pending = Workflow.objects.filter(status='pending').count()
    
    status_chart = {
        'labels': ['Pending', 'In Review', 'Approved', 'Rejected'],
        'data': [total_pending, in_review, total_approved, total_rejected],
        'colors': ['#F0A030', '#4A90D9', '#2EA86B', '#E55B5B'],
    }
    
    dept_data = Department.objects.annotate(
        doc_count=Count('documents')
    ).values('dept_name', 'doc_count').order_by('-doc_count')[:7]
    
    dept_chart = {
        'labels': [d['dept_name'] for d in dept_data] if dept_data else ['No Data'],
        'data': [d['doc_count'] for d in dept_data] if dept_data else [0],
    }
    
    monthly_labels = []
    monthly_data = []
    today = datetime.now().date()
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_name = month_date.strftime('%b %Y')
        monthly_labels.append(month_name)
        
        count = Workflow.objects.filter(
            started_at__year=month_date.year,
            started_at__month=month_date.month
        ).count()
        monthly_data.append(count)
    
    context = {
        'greeting': get_greeting(),
        'workflows': workflows,
        'pending_approvals': pending_approvals,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'in_review': in_review,
        'total_pending': total_pending,
        'unread': unread,
        'status_chart_raw': status_chart,
        'dept_chart_raw': dept_chart,
        'monthly_labels_raw': monthly_labels,
        'monthly_data_raw': monthly_data,
        'status_filter': status_filter,
    }
    
    return render(request, 'registry/workflow_overview.html', context)

@role_required('supervisor', 'admin')
def approval_view(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    form = ApprovalForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        action = form.cleaned_data['action']
        comment_text = form.cleaned_data.get('comment', '')
        
        target_status = 'processed' if action in ('approved', 'processed') else 'rejected'
        display_step = 'Processed & Ready' if target_status == 'processed' else 'Request Rejected'

        wf = doc.workflows.last()
        if wf:
            wf.status = target_status
            wf.current_step = display_step
            wf.completed_at = timezone.now()
            wf.save()
        
        new_status, _ = Status.objects.get_or_create(
            status_code=target_status,
            defaults={'status_name': target_status.capitalize()}
        )
        doc.status = new_status
        doc.save()
        
        add_tracking_entry(
            doc, 
            request.user, 
            target_status.upper(), 
            f'Document set to {target_status} by {request.user.get_full_name()}. Comments: {comment_text[:100] if comment_text else "None"}', 
            request
        )
        
        if comment_text:
            Comment.objects.create(document=doc, user=request.user, comment=comment_text)
        
        ntype = 'approval' if target_status == 'processed' else 'rejection'
        msg = f'Your document "{doc.title}" (Ref: {doc.reference_no}) has been {target_status} by {request.user.get_full_name()}.'
        if doc.submitted_by:
            notify_user(doc.submitted_by, doc, msg, ntype=ntype)
        
        log_action(request, target_status.upper(), 'Document', doc.id, comment_text)
        messages.success(request, f'Document has been successfully set to {target_status}.')
        
        if CHANNELS_AVAILABLE:
            try:
                channel_layer = get_channel_layer()
                data = get_workflow_chart_data()
                async_to_sync(channel_layer.group_send)(
                    "workflow_updates",
                    {
                        "type": "workflow_update",
                        "data": data
                    }
                )
            except Exception as e:
                print(f"WebSocket broadcast failed: {e}")
        
        return redirect('document_detail', pk=pk)
    
    return render(request, 'registry/approval_form.html', {'form': form, 'doc': doc})

# ─────────────────────────────────────────────
# DOCUMENT MANAGEMENT
# ─────────────────────────────────────────────

@login_required
def document_list(request):
    user = request.user
    if user.role in ('admin', 'supervisor'):
        docs = Document.objects.select_related('department', 'submitted_by', 'status').all()
    elif user.role == 'clerk':
        docs = Document.objects.filter(submitted_by=user).select_related('department', 'status')
    else:
        assigned_ids = Assignment.objects.filter(assigned_to=user).values_list('document_id', flat=True)
        docs = Document.objects.filter(id__in=assigned_ids).select_related('department', 'status')
    
    query = request.GET.get('q', '')
    if query:
        docs = docs.filter(Q(title__icontains=query) | Q(reference_no__icontains=query))
    
    return render(request, 'registry/document_list.html', {'docs': docs, 'query': query})

@login_required
def document_detail(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    workflows = doc.workflows.all()
    comments = doc.comments.select_related('user').all()
    comment_form = CommentForm()
    
    add_tracking_entry(doc, request.user, 'VIEWED', f'Document viewed by {request.user.get_full_name() or request.user.username}', request)
    
    if request.method == 'POST' and 'comment_submit' in request.POST:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            c = comment_form.save(commit=False)
            c.document = doc
            c.user = request.user
            c.save()
            add_tracking_entry(doc, request.user, 'COMMENT_ADDED', f'Comment added: {c.comment[:100]}', request)
            return redirect('document_detail', pk=pk)
    
    return render(request, 'registry/document_detail.html', {
        'doc': doc,
        'workflows': workflows,
        'comments': comments,
        'comment_form': comment_form,
    })

@role_required('clerk', 'admin')
def document_assign(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    form = AssignDocumentForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        assignee = form.cleaned_data['assign_to']
        due = form.cleaned_data.get('due_date')
        
        Assignment.objects.create(
            document=doc,
            assigned_to=assignee,
            assigned_by=request.user,
            due_date=due,
        )
        
        wf = doc.workflows.last()
        if wf:
            wf.current_step = 'Assigned'
            wf.assigned_to = assignee
            wf.save()
        
        assigned_status, _ = Status.objects.get_or_create(
            status_code='assigned',
            defaults={'status_name': 'Assigned', 'description': 'Assigned to a processing officer'}
        )
        doc.status = assigned_status
        doc.save()
        
        add_tracking_entry(
            doc, request.user, 'ASSIGNED', 
            f'Assigned to {assignee.get_full_name() or assignee.username}', 
            request
        )
        
        notify_user(
            assignee, doc, 
            f'Document "{doc.title}" (Ref: {doc.reference_no}) has been assigned to you.', 
            ntype='assignment'
        )
        
        log_action(request, 'ASSIGN_DOCUMENT', 'Document', doc.id, f'→ {assignee.username}')
        messages.success(request, f'Document successfully assigned to {assignee.get_full_name() or assignee.username}.')
        return redirect('document_detail', pk=pk)
    
    return render(request, 'registry/assign_form.html', {'form': form, 'doc': doc})

# ─────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────

@login_required
def notifications_view(request):
    notes = Notification.objects.filter(user=request.user).order_by('-sent_at')
    has_new = notes.filter(is_read=False).exists()
    notes.filter(is_read=False).update(is_read=True)
    
    context = {
        'notifications': notes,
        'has_new_notifications': has_new,
        'greeting': get_greeting(),
    }
    return render(request, 'registry/notifications.html', context)

# ─────────────────────────────────────────────
# REPORTS & ANALYTICS
# ─────────────────────────────────────────────

@role_required('supervisor', 'admin')
def reports_view(request):
    dept_stats = Department.objects.annotate(
        doc_count=Count('documents'),
        approved=Count('documents', filter=Q(documents__status__status_code='approved')),
        pending=Count('documents', filter=Q(documents__status__status_code='pending')),
        rejected=Count('documents', filter=Q(documents__status__status_code='rejected')),
    )
    total_docs = Document.objects.count()
    total_approved = Document.objects.filter(status__status_code='approved').count()
    total_pending = Document.objects.filter(status__status_code='pending').count()
    total_rejected = Document.objects.filter(status__status_code='rejected').count()
    
    return render(request, 'registry/reports.html', {
        'dept_stats': dept_stats,
        'total_docs': total_docs,
        'total_approved': total_approved,
        'total_pending': total_pending,
        'total_rejected': total_rejected,
        'greeting': get_greeting(),
    })

@role_required('supervisor', 'admin')
def export_to_excel(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="smartflow_documents_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Reference No', 'Title', 'Document Type', 'Status', 'Submitted By', 'Department', 'Created At', 'Last Updated'])
    
    documents = Document.objects.select_related('submitted_by', 'department', 'status').all()
    
    for doc in documents:
        writer.writerow([
            doc.reference_no,
            doc.title,
            doc.document_type or 'N/A',
            doc.status.status_name if doc.status else 'Pending',
            doc.submitted_by.get_full_name() if doc.submitted_by else 'Unknown',
            doc.department.dept_name if doc.department else 'N/A',
            doc.created_at.strftime('%Y-%m-%d %H:%M'),
            doc.updated_at.strftime('%Y-%m-%d %H:%M'),
        ])
    
    log_action(request, 'EXPORT_EXCEL', 'Document', None, 'Exported all documents to CSV')
    return response

@login_required
def export_document_pdf(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="SmartFlow_{doc.reference_no}.pdf"'
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    p.setFillColorRGB(0.05, 0.23, 0.43)
    p.rect(0, height - 60, width, 60, fill=1)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height - 40, "SmartFlow - Document Report")
    
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 100, f"Reference: {doc.reference_no}")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 130, f"Title: {doc.title}")
    p.drawString(50, height - 150, f"Description: {doc.description or 'No description'}")
    p.drawString(50, height - 170, f"Document Type: {doc.document_type or 'Not specified'}")
    p.drawString(50, height - 190, f"Status: {doc.status.status_name if doc.status else 'Pending'}")
    p.drawString(50, height - 210, f"Submitted By: {doc.submitted_by.get_full_name() if doc.submitted_by else 'Unknown'}")
    p.drawString(50, height - 230, f"Submitted On: {doc.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(50, height - 250, f"Last Updated: {doc.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if doc.department:
        p.drawString(50, height - 270, f"Department: {doc.department.dept_name}")
    
    p.setFont("Helvetica", 8)
    p.setFillColorRGB(0.5, 0.5, 0.5)
    p.drawString(50, 30, "Generated by SmartFlow - TelOne Registry Department")
    p.drawString(50, 20, f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    log_action(request, 'EXPORT_PDF', 'Document', doc.id, 'Exported to PDF')
    return response

# ─────────────────────────────────────────────
# ADVANCED SEARCH
# ─────────────────────────────────────────────

@login_required
def advanced_search(request):
    departments = Department.objects.all()
    statuses = Status.objects.all()
    documents = Document.objects.select_related('department', 'submitted_by', 'status')
    
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    department_filter = request.GET.get('department', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if query:
        documents = documents.filter(
            Q(title__icontains=query) | 
            Q(reference_no__icontains=query) |
            Q(description__icontains=query)
        )
    if status_filter:
        documents = documents.filter(status__id=status_filter)
    if department_filter:
        documents = documents.filter(department__id=department_filter)
    if date_from:
        documents = documents.filter(created_at__date__gte=date_from)
    if date_to:
        documents = documents.filter(created_at__date__lte=date_to)
    
    context = {
        'documents': documents,
        'departments': departments,
        'statuses': statuses,
        'query': query,
        'selected_status': status_filter,
        'selected_department': department_filter,
        'date_from': date_from,
        'date_to': date_to,
        'greeting': get_greeting(),
    }
    return render(request, 'registry/advanced_search.html', context)

# ─────────────────────────────────────────────
# ADMIN MANAGEMENT
# ─────────────────────────────────────────────

@login_required
@admin_key_required
def admin_welcome(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    error = None
    if request.method == 'POST':
        admin_key = request.POST.get('admin_key')
        if admin_key == 'SMARTFLOW_ADMIN_2024':
            request.session['admin_verified'] = True
            return redirect('admin_launchpad')
        else:
            error = True
            log_action(request, 'FAILED_KEY_ENTRY', 'User', request.user.id, 'Invalid admin security key signature input.')
    
    return render(request, 'registry/admin_welcome.html', {'error': error})

@login_required
@admin_key_required
def admin_launchpad(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    context = {
        'greeting': get_greeting(),
        'total_docs': Document.objects.count(),
        'total_users': User.objects.filter(is_active=True).count(),
        'total_depts': Department.objects.count(),
        'unread': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'registry/admin_launchpad.html', context)

@login_required
@admin_key_required
def admin_workspace(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    context = {
        'greeting': get_greeting(),
        'total_docs': Document.objects.count(),
        'total_users': User.objects.filter(is_active=True).count(),
        'total_depts': Department.objects.count(),
        'unread': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'registry/admin_workspace.html', context)

@login_required
@admin_key_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    return check_progress(request)

# ─────────────────────────────────────────────
# CHECK PROGRESS VIEW
# ─────────────────────────────────────────────

@login_required
@admin_key_required
def check_progress(request):
    if request.user.role != 'admin':
        return redirect('dashboard')

    status_filter = request.GET.get('status', '')
    dept_filter = request.GET.get('department', '')

    documents = Document.objects.select_related(
        'department', 'status', 'submitted_by'
    ).order_by('-created_at')

    pending_count = Document.objects.filter(status__status_code='pending').count()
    review_count = Document.objects.filter(status__status_code='in_review').count()
    approved_count = Document.objects.filter(status__status_code='approved').count()
    rejected_count = Document.objects.filter(status__status_code='rejected').count()

    today = timezone.now().date()
    timeline_labels = []
    timeline_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        timeline_labels.append(day.strftime('%a'))
        day_count = Document.objects.filter(created_at__date=day).count()
        timeline_data.append(day_count)

    dept_metrics = Department.objects.annotate(
        doc_count=Count('documents')
    ).order_by('-doc_count')

    dept_labels = [dept.dept_name for dept in dept_metrics]
    dept_data = [dept.doc_count for dept in dept_metrics]

    context = {
        'greeting': get_greeting(),
        'documents': documents,
        'pending_count': pending_count,
        'review_count': review_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'timeline_labels': json.dumps(timeline_labels),
        'timeline_data': json.dumps(timeline_data),
        'dept_labels': json.dumps(dept_labels),
        'dept_data': json.dumps(dept_data),
        'status_filter': status_filter,
        'dept_filter': dept_filter,
        'unread': Notification.objects.filter(user=request.user, is_read=False).count(),
    }

    return render(request, 'registry/check_progress.html', context)

# ─────────────────────────────────────────────
# AUDIT TRAIL
# ─────────────────────────────────────────────

@role_required('admin')
@admin_key_required
def audit_trail(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    return render(request, 'registry/audit_trail.html', {'logs': logs, 'greeting': get_greeting()})

# ─────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────

@role_required('admin')
@admin_key_required
def manage_users(request):
    users = User.objects.select_related('department').all()
    return render(request, 'registry/manage_users.html', {'users': users, 'greeting': get_greeting()})

@role_required('admin')
@admin_key_required
def create_user(request):
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        log_action(request, 'CREATE_USER', 'User', user.id, user.username)
        messages.success(request, f'User "{user.username}" created successfully.')
        return redirect('manage_users')
    return render(request, 'registry/user_form.html', {'form': form, 'action': 'Create'})

# ─────────────────────────────────────────────
# DEPARTMENT MANAGEMENT
# ─────────────────────────────────────────────

@role_required('admin')
@admin_key_required
def manage_departments(request):
    depts = Department.objects.annotate(member_count=Count('members'))
    return render(request, 'registry/manage_departments.html', {'depts': depts, 'greeting': get_greeting()})

@role_required('admin')
@admin_key_required
def create_department(request):
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        dept = form.save()
        log_action(request, 'CREATE_DEPARTMENT', 'Department', dept.id, dept.dept_name)
        messages.success(request, f'Department "{dept.dept_name}" created.')
        return redirect('manage_departments')
    return render(request, 'registry/department_form.html', {'form': form, 'action': 'Create'})

# ─────────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────────

def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    return render(request, 'errors/500.html', status=500)

def handler403(request, exception):
    return render(request, 'errors/403.html', status=403)