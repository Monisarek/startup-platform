from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path("", include("accounts.urls")),
    path('admin/', admin.site.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler404 = "accounts.views.custom_404"
