from django.urls import path
from . import views

from .views_files.ai_views import (
    student_ai_action,
    student_ai_bulk,
    supervisor_ai_action,
    staff_ai_action,
    admin_ai_action,
    ai_chat,
    #  AI Dashboard Views 
    student_ai_dashboard,
    supervisor_ai_dashboard,
    staff_ai_dashboard,
    clerk_ai_dashboard,
    admin_ai_dashboard,
    chatbot_view,
)

urlpatterns = [
    # ─────────────────────────────────────────────
    # PUBLIC PAGES (no login required)
    # ─────────────────────────────────────────────
    path('', views.landing_page, name='landing_page'),
    path('learn-more/', views.learn_more, name='learn_more'),
    path('role-selection/', views.role_selection, name='role_selection'),

    # ─────────────────────────────────────────────
    # REGISTRATION (role-based)
    # ─────────────────────────────────────────────
    path('register/student/', views.register_student, name='register_student'),
    path('register/clerk/', views.register_clerk, name='register_clerk'),
    path('register/staff/', views.register_staff, name='register_staff'),
    path('register/supervisor/', views.register_supervisor, name='register_supervisor'),
    path('register/admin/', views.register_admin, name='register_admin'),

    # ─────────────────────────────────────────────
    # AUTH
    # ─────────────────────────────────────────────
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ─────────────────────────────────────────────
    # DASHBOARDS 
    # ─────────────────────────────────────────────
    path('dashboard/', views.dashboard, name='dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('supervisor/dashboard/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/workflow/', views.workflow_overview, name='workflow_overview'),
    path('clerk/dashboard/', views.clerk_dashboard, name='clerk_dashboard'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),

    # ─────────────────────────────────────────────
    # STUDENT ROUTES
    # ─────────────────────────────────────────────
    path('student/submit/', views.student_submit_request, name='student_submit'),
    path('student/track/<int:pk>/', views.student_track_request, name='student_track'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/progress/', views.student_check_progress, name='student_check_progress'),
    path('student/my-requests/', views.student_my_requests, name='student_my_requests'),

    # ─────────────────────────────────────────────
    # DOCUMENTS
    # ─────────────────────────────────────────────
    path('documents/', views.document_list, name='document_list'),
    path('documents/register/', views.document_register, name='document_register'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/assign/', views.document_assign, name='document_assign'),
    path('documents/<int:pk>/approve/', views.approval_view, name='approval_view'),

    # ─────────────────────────────────────────────
    # EXPORT
    # ─────────────────────────────────────────────
    path('document/<int:pk>/export/', views.export_document_pdf, name='export_document'),
    path('export/excel/', views.export_to_excel, name='export_excel'),

    # ─────────────────────────────────────────────
    # BULK UPLOAD
    # ─────────────────────────────────────────────
    path('documents/bulk-upload/', views.bulk_upload_documents, name='bulk_upload'),

    # ─────────────────────────────────────────────
    # ADVANCED SEARCH
    # ─────────────────────────────────────────────
    path('search/advanced/', views.advanced_search, name='advanced_search'),

    # ─────────────────────────────────────────────
    # NOTIFICATIONS
    # ─────────────────────────────────────────────
    path('notifications/', views.notifications_view, name='notifications'),

    # ─────────────────────────────────────────────
    # REPORTS & AUDIT
    # ─────────────────────────────────────────────
    path('reports/', views.reports_view, name='reports'),
    path('audit-trail/', views.audit_trail, name='audit_trail'),

    # ─────────────────────────────────────────────
    # ADMIN — USERS
    # ─────────────────────────────────────────────
    path('users/', views.manage_users, name='manage_users'),
    path('users/create/', views.create_user, name='create_user'),

    # ─────────────────────────────────────────────
    # ADMIN — DEPARTMENTS
    # ─────────────────────────────────────────────
    path('departments/', views.manage_departments, name='manage_departments'),
    path('departments/create/', views.create_department, name='create_department'),

    # ─────────────────────────────────────────────
    # CANCEL REQUEST (STUDENT FEATURE)
    # ─────────────────────────────────────────────
    path('request/<int:pk>/cancel/', views.cancel_request, name='cancel_request'),

    # ─────────────────────────────────────────────
    # CHANGE PASSWORD (ALL USERS)
    # ─────────────────────────────────────────────
    path('change-password/', views.change_password, name='change_password'),

    # ─────────────────────────────────────────────
    # ADMIN WELCOME, LAUNCHPAD, & ANALYTICS
    # ─────────────────────────────────────────────
    path('control/welcome/', views.admin_welcome, name='admin_welcome'),
    path('control/launchpad/', views.admin_launchpad, name='admin_launchpad'),
    path('control/workspace/', views.admin_workspace, name='admin_workspace'),
    path('control/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # ─────────────────────────────────────────────
    # ADMIN PROGRESS & ANALYTICS
    # ─────────────────────────────────────────────
    path('check-progress/', views.admin_dashboard, name='check_progress'),

    # ─────────────────────────────────────────────
    # AI ENDPOINTS
    # ─────────────────────────────────────────────
    path('api/ai/student/<int:document_id>/', student_ai_action, name='ai_student_action'),
    path('api/ai/student/<int:document_id>/bulk/', student_ai_bulk, name='ai_student_bulk'),
    path('api/ai/supervisor/<int:document_id>/', supervisor_ai_action, name='ai_supervisor_action'),
    path('api/ai/staff/', staff_ai_action, name='ai_staff_action'),
    path('api/ai/admin/', admin_ai_action, name='ai_admin_action'),
    path('api/ai/chat/', ai_chat, name='ai_chat'),

    # ─────────────────────────────────────────────
    # AI DASHBOARD PAGES
    # ─────────────────────────────────────────────
    path('ai/student-dashboard/', student_ai_dashboard, name='student_ai_dashboard'),
    path('ai/supervisor-dashboard/', supervisor_ai_dashboard, name='supervisor_ai_dashboard'),
    path('ai/staff-dashboard/', staff_ai_dashboard, name='staff_ai_dashboard'),
    path('ai/clerk-dashboard/', clerk_ai_dashboard, name='clerk_ai_dashboard'),
    path('ai/admin-dashboard/', admin_ai_dashboard, name='admin_ai_dashboard'),
    path('ai/chatbot/', chatbot_view, name='chatbot'),
    path('ai/student/<int:document_id>/', student_ai_dashboard, name='student_ai_dashboard_doc'),
    path('ai/supervisor/<int:document_id>/', supervisor_ai_dashboard, name='supervisor_ai_dashboard_doc'),
]