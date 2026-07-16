from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from registry import views

urlpatterns = [
    # 1. Your custom Admin welcome screen (Safe prefix to prevent 404 conflicts)
    path('portal/welcome/', views.admin_welcome, name='admin_welcome'),
    
    # 2. Separate URL for your new spacious multi-link Phase 2 Launchpad
    path('portal/launchpad/', views.admin_launchpad, name='admin_launchpad'),

    # 3. Default built-in Django Admin interface
    path('admin/', admin.site.urls),
    
    # 4. Include all individual app urls (Students, Clerks, etc.)
    path('', include('registry.urls')),
    
    # 5. Document PDF Export route moved safely inside the list
    path('document/<int:pk>/export/', views.export_document_pdf, name='export_document'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)