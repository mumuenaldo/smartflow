# registry/utils.py
from datetime import datetime, timedelta
from django.db.models import Count
from .models import Workflow, Document


def get_student_progress_data(student):
    """Same logic as the student_check_progress view — pulled out here
    so it can be reused both for the initial page render and for the
    live WebSocket broadcast when any of this student's documents change."""
    my_requests = Document.objects.filter(student_requester=student)
    pending = my_requests.filter(status__status_code='pending').count()
    approved = my_requests.filter(status__status_code='approved').count()
    rejected = my_requests.filter(status__status_code='rejected').count()
    in_review = my_requests.filter(status__status_code='in_review').count()

    monthly_data = []
    monthly_labels = []
    today = datetime.now().date()

    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        monthly_labels.append(month_date.strftime('%b %Y'))
        count = Document.objects.filter(
            student_requester=student,
            created_at__year=month_date.year,
            created_at__month=month_date.month
        ).count()
        monthly_data.append(count)

    return {
        'pending': pending,
        'in_review': in_review,
        'approved': approved,
        'rejected': rejected,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
    }


def get_workflow_chart_data():
    status_counts = {
        'pending': Workflow.objects.filter(status='pending').count(),
        'in_review': Workflow.objects.filter(status='in_review').count(),
        'approved': Workflow.objects.filter(status='approved').count(),
        'rejected': Workflow.objects.filter(status='rejected').count(),
    }
    
    # FIX: Changed 'document__department__name' to 'document__department__dept_name'
    dept_qs = Workflow.objects.values('document__department__dept_name').annotate(
        count=Count('id')
    )
    dept_labels = [d['document__department__dept_name'] or 'Unassigned' for d in dept_qs]
    dept_data = [d['count'] for d in dept_qs]
    
    return {
        'status': {
            'labels': ['Pending', 'In Review', 'Approved', 'Rejected'],
            'data': [status_counts['pending'], status_counts['in_review'], status_counts['approved'], status_counts['rejected']]
        },
        'dept': {
            'labels': dept_labels,
            'data': dept_data
        },
        'pending': status_counts['in_review'] # This tracks what's currently awaiting supervisor review
    }