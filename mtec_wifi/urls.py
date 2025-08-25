from django.contrib import admin
from django.urls import path, include
from core.views import mpesa_callback

urlpatterns = [
    path('admin/', admin.site.urls),
    path('daraja/', include('daraja.urls')),  # Use daraja.urls for django-daraja
    path('', include('core.urls')),
    path('mpesa/stk-push/callback/', mpesa_callback, name='mpesa_callback'),
]