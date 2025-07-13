import logging
from .models import Device, Image
from datetime import datetime
from .InsectDetector import InsectDetector
from django.utils import timezone
from django.http import JsonResponse
from django.core.files.uploadedfile import UploadedFile, InMemoryUploadedFile
import io
import numpy as np
import cv2

logger = logging.getLogger(__name__)

def process_image(device_id, image: UploadedFile):
    device = Device.objects.get(id=device_id)
    current_time = timezone.now()
    
    # Read the image file in uint8 format, then convert the 1D array into 3D array (RGB image)
    image_bytes = image.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Update device's last connected time
    device.last_connected = current_time
    device.save()
    
    # Start Detection
    detector = InsectDetector()
    results = detector.detect(image=img)
    
    if results:
        # Draw bounding boxes on the image
        annotated_img = detector.draw_bounding_boxes(img, results)
        
        # Encode the annotated image to JPEG
        _, buffer = cv2.imencode('.jpg', annotated_img)
        image_bytes = buffer.tobytes()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f"{timestamp}_{device.name}.jpg"
        image_file = InMemoryUploadedFile(
            file=io.BytesIO(image_bytes),
            field_name='file_path',
            name=new_filename,
            content_type='image/jpeg',
            size=len(image_bytes),
            charset=None
        )

        logger.info(f"Received from device: {device.name}, image name: {new_filename}, image size: {image_file.size}")
        device_image = Image.objects.create(
            device=device,
            file_path=image_file,
            created_at=timezone.now()
        )
        if not device_image:
            raise ValueError(f"Error occurred in image processing phase.")
        logger.info(f"{results}")
        # else:
        #     results['result_image'] = device_image
    return results