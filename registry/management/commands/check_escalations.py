from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from registry.models import Document
from registry.views import notify_user

class Command(BaseCommand):
    help = 'Check pending requests and send escalation notifications'

    def handle(self, *args, **kwargs):
        pending_docs = Document.objects.filter(status__status_code='pending')

        if not pending_docs:
            self.stdout.write(self.style.SUCCESS('✅ No pending requests found.'))
            return

        for doc in pending_docs:
            time_pending = timezone.now() - doc.created_at

            if time_pending > timedelta(hours=72) and doc.escalation_level < 3:
                doc.escalation_level = 3
                doc.escalated_at = timezone.now()
                doc.save()
                notify_user(doc.submitted_by, doc, f"🚨 Escalated to Admin: {doc.title} pending 72+ hrs", 'escalation')
                self.stdout.write(self.style.WARNING(f'🔴 Escalated to Admin: {doc.reference_no}'))

            elif time_pending > timedelta(hours=48) and doc.escalation_level < 2:
                doc.escalation_level = 2
                doc.escalated_at = timezone.now()
                doc.save()
                notify_user(doc.submitted_by, doc, f"⚠️ Escalated to Supervisor: {doc.title} pending 48+ hrs", 'escalation')
                self.stdout.write(self.style.WARNING(f'🟡 Escalated to Supervisor: {doc.reference_no}'))

            elif time_pending > timedelta(hours=24) and doc.escalation_level < 1:
                doc.escalation_level = 1
                doc.escalated_at = timezone.now()
                doc.save()
                notify_user(doc.submitted_by, doc, f"⏳ Reminder: {doc.title} pending 24+ hrs", 'reminder')
                self.stdout.write(self.style.WARNING(f'🟢 Reminder sent: {doc.reference_no}'))

        self.stdout.write(self.style.SUCCESS('✅ Escalation check completed.'))