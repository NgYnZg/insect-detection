from django.db import models

# Create your models here.

class Device(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.CharField(max_length=100)
    longitude = models.CharField(max_length=100)
    status = models.BooleanField(default=True)
    last_connected = models.DateTimeField(default=None, null=True)
    last_disconnected = models.DateTimeField(default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Image(models.Model):
    def image_upload_to(instance, filename):
        return f"devices/{filename}"

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='images')
    file_path = models.FileField(upload_to=image_upload_to)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_path


class PestType(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name


class Detection(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='detections')
    pest_type = models.ForeignKey(PestType, on_delete=models.CASCADE, related_name='detections')
    confidence = models.DecimalField(default=None, decimal_places=2, max_digits=5)
    bbox_x = models.IntegerField(default=None)
    bbox_y = models.IntegerField(default=None)
    bbox_width = models.IntegerField(default=None)
    bbox_height = models.IntegerField(default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Confidence level: {self.confidence} \nBounding box x: {self.bbox_x} \nBounding box y: {self.bbox_y}"
    
    

