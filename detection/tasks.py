import logging
from .models import Device, Image, Detection, PestType
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
        # Save Detection objects for each detection result
        for detection in results:
            class_name = detection.get('class')
            confidence = detection.get('confidence')
            bbox = detection.get('bbox', [None, None, None, None])
            xmin, ymin, xmax, ymax = bbox
            bbox_width = xmax - xmin if xmax is not None and xmin is not None else None
            bbox_height = ymax - ymin if ymax is not None and ymin is not None else None
            # Get or create PestType by class name
            pest_type, _ = PestType.objects.get_or_create(name=class_name, defaults={'description': class_name})
            Detection.objects.create(
                image=device_image,
                pest_type=pest_type,
                confidence=confidence,
                bbox_x=xmin,
                bbox_y=ymin,
                bbox_width=bbox_width,
                bbox_height=bbox_height
            )
        logger.info(f"{results}")
        # else:
        #     results['result_image'] = device_image
    return results