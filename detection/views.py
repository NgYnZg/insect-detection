from django.shortcuts import get_object_or_404
import os
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Device
from .tasks import process_image
from .InsectDetector import InsectDetector
import cv2
import numpy as np

logger = logging.getLogger(__name__)

def save_image(annotated_img, filename, annotated=False):
    """
    Save the image to the media directory and return the URL.
    """
    directory = "original_images"
    if annotated_img is not None and annotated is True:
        # Create filename for annotated image
        name, ext = os.path.splitext(filename)
        filename = f"{name}_annotated{ext}"
        directory = "annotated_images"
    
    # Create the full path
    media_dir = os.path.join(settings.MEDIA_ROOT, directory)
    os.makedirs(media_dir, exist_ok=True)
    
    file_path = os.path.join(media_dir, filename)
    
    # Save the image
    cv2.imwrite(file_path, annotated_img)
    
    # Return the URL
    return f"/media/{directory}/{filename}"


@csrf_exempt
@require_POST
def receive_device_data(request):
    device_id = request.POST.get('device_id')
    if not device_id:
        return JsonResponse({'error': 'Missing device id'}, status=400)
    device = get_object_or_404(Device, id=device_id)
    name = request.POST.get('name')
    image = request.FILES.get('image')

    if not name or not image:
        return JsonResponse({'error': 'Missing name or image'}, status=400)
        
    try:
        results = process_image(device_id, image)
        logger.info(f"Received data from device {device.name}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Data received and queued for processing'
        })
    except ValueError as e:
        logger.error(f"Error processing image: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }, status=500)

@csrf_exempt
@require_POST
def detect_insect_from_image(request):
    image = request.FILES.get('image')
    model_name = request.POST.get('model', 'yolov11s')  # Default to yolov11s if not provided
    
    if not image:
        return JsonResponse({'error': 'No image provided'}, status=400)
    try:
        # Read image file into numpy array
        image_bytes = image.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return JsonResponse({'error': 'Invalid image file'}, status=400)
        
        # Run detection with annotations using selected model
        detector = InsectDetector(model_name=model_name)
        detections, annotated_img = detector.detect_with_annotations(img)
        if annotated_img is not None:
            # Save annotated image and get URL
            annotated_image_url = save_image(annotated_img, image.name, True)
            original_image_url = save_image(img, image.name)
        if detections is None:
            detections = "No insects detected in the uploaded image."
        return JsonResponse({
            'detections': detections, 
            'annotated_image_url': annotated_image_url,
            'original_image_url': original_image_url,
            'status': 'success'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    