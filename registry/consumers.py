# registry/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class WorkflowConsumer(AsyncWebsocketConsumer):
    """Broadcasts live workflow/document status updates to everyone
    watching a dashboard (student, supervisor, admin)."""

    async def connect(self):
        self.group_name = "workflow_updates"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "connection",
            "status": "connected"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def workflow_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "workflow_update",
            "data": event["data"]
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """Per-user notification stream. Joins a group scoped to the
    connecting user's id (from the URL) so only that user's browser
    receives their notifications."""

    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs'].get('user_id', 'anon')
        self.group_name = f"notifications_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "connection",
            "status": "connected"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "data": event["data"]
        }))


class DocumentConsumer(AsyncWebsocketConsumer):
    """Per-document tracking stream, e.g. for a student watching
    their own request's live status on the track page."""

    async def connect(self):
        self.doc_id = self.scope['url_route']['kwargs']['doc_id']
        self.group_name = f"document_{self.doc_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "connection",
            "status": "connected"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def document_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "document_update",
            "data": event["data"]
        }))


class StudentProgressConsumer(AsyncWebsocketConsumer):
    """Per-student progress stream for student_check_progress.html.
    Unlike WorkflowConsumer (global counts across everyone), this is
    scoped to one student's own requests only."""

    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f"student_progress_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "connection",
            "status": "connected"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def progress_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "progress_update",
            "data": event["data"]
        }))