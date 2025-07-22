import logging
from .models import Device, Image, Detection, PestType
from datetime import datetime
from .InsectDetector import InsectDetector
from django.utils import timezone
from django.core.files.uploadedfile import UploadedFile, InMemoryUploadedFile
import io
import numpy as np
import cv2

logger = logging.getLogger(__name__)

def get_device_and_update_last_connected(device_id):
    """Fetch device by ID and update its last connected time."""
    try:
        device = Device.objects.get(id=device_id)
        device.last_connected = timezone.now()
        device.save()
        return device
    except Device.DoesNotExist:
        logger.error(f"Device with id {device_id} does not exist.")
        raise

def decode_image(uploaded_image: UploadedFile):
    """Decode uploaded image to OpenCV format."""
    try:
        image_bytes = uploaded_image.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image.")
        return img
    except Exception as e:
        logger.error(f"Error decoding image: {e}")
        raise

def detect_and_annotate(img):
    """Run detection and annotate image with bounding boxes."""
    detector = InsectDetector()
    results = detector.detect(image=img)
    if results:
        annotated_img = detector.draw_bounding_boxes(img, results)
        return results, annotated_img
    return results, img

def save_annotated_image(device, annotated_img):
    """Encode and save annotated image, returning the Image instance."""
    try:
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
            raise ValueError("Error occurred in image saving phase.")
        return device_image
    except Exception as e:
        logger.error(f"Error saving annotated image: {e}")
        raise

def save_detection_results(device_image, results):
    """Save detection results to the database."""
    for detection in results:
        class_name = detection.get('class')
        confidence = detection.get('confidence')
        bbox = detection.get('bbox', [None, None, None, None])
        xmin, ymin, xmax, ymax = bbox
        bbox_width = xmax - xmin if xmax is not None and xmin is not None else None
        bbox_height = ymax - ymin if ymax is not None and ymin is not None else None
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

def process_image(device_id, image: UploadedFile):
    """
    Main entry point for processing an uploaded image from a device.
    Handles device update, image decoding, detection, annotation, saving, and result persistence.
    """
    device = get_device_and_update_last_connected(device_id)
    img = decode_image(image)
    results, annotated_img = detect_and_annotate(img)
    if results:
        device_image = save_annotated_image(device, annotated_img)
        save_detection_results(device_image, results)
        logger.info(f"Detection results: {results}")
    return results