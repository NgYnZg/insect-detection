from django.urls import path
from . import views

urlpatterns = [
    path('', views.overview, name='overview'),
    path('devices/', views.device_list, name='device_list'),
    path('devices/add/', views.add_device, name='add_device'),
    path('devices/<int:device_id>/', views.device_detail, name='device_detail'),
    path('devices/<int:device_id>/delete/', views.delete_device, name='delete_device'),
    path('detect-insect-upload/', views.detect_insect_upload, name='detect_insect_upload'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('devices/recover/', views.recover_devices, name='recover_devices'),
    path('devices/recover-action/', views.recover_device, name='recover_device'),
]
