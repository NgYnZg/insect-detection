from django.urls import path
from . import views

urlpatterns = [
    path('api/devices/', views.receive_device_data, name='receive_device_data'),
    path('api/detect-insect/', views.detect_insect_from_image, name='detect_insect_from_image'),
] 