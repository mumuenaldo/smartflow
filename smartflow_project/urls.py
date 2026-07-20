from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from registry import views

urlpatterns = [

    path('portal/welcome/', views.admin_welcome, name='admin_welcome'),
    
    
    path('portal/launchpad/', views.admin_launchpad, name='admin_launchpad'),

    path('admin/', admin.site.urls),
    
    path('', include('registry.urls')),
    
    
    path('document/<int:pk>/export/', views.export_document_pdf, name='export_document'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)