from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Notifications
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/notifications/(?P<user_id>\w+)/$', consumers.NotificationConsumer.as_asgi()),

    # Workflow updates
    re_path(r'ws/workflow/$', consumers.WorkflowConsumer.as_asgi()),
    re_path(r'ws/workflow/(?P<doc_id>\w+)/$', consumers.WorkflowConsumer.as_asgi()),

    # Document tracking
    re_path(r'ws/document/(?P<doc_id>\w+)/$', consumers.DocumentConsumer.as_asgi()),

    # Student progress (per-student, not global)
    re_path(r'ws/student-progress/(?P<user_id>\w+)/$', consumers.StudentProgressConsumer.as_asgi()),
]