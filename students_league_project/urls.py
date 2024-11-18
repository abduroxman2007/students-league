# students_league_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    # path('api/verify-email/', include('verify_email.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else []
