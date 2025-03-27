from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    from django.urls import path
from . import views

urlpatterns = [
    path('', views.startups_list, name='startups_list'),
    path('startup/<int:startup_id>/', views.startup_detail, name='startup_detail'),
]