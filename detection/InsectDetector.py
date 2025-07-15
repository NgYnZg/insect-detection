import cv2
import numpy as np
import os
from typing import List, Dict, Union, Tuple
from ultralytics import YOLO

class InsectDetector:
    @staticmethod
    def get_available_models() -> List[str]:
        """
        Get list of available model names from the Models directory.
        
        :return: List of model names (without .pt extension)
        """
        models_dir = "./Models"
        available_models = []
        
        if os.path.exists(models_dir):
            for file in os.listdir(models_dir):
                if file.endswith('.pt'):
                    # Remove .pt extension to get model name
                    model_name = file[:-3]
                    available_models.append(model_name)
        
        return available_models

    def __init__(self, model_name: str = "yolov11s", device: str = 'cpu'):
        """
        Initializes the YOLO model for insect detection.

        :param model_path: Path to the YOLO model file (.pt format).
        :param device: 'cpu' or 'cuda' for GPU inference.
        :raises FileNotFoundError: If the model file does not exist at the specified path.
        """
        self.device = device
        model_path = f"./Models/{model_name}.pt"
        # Check if model file exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at path: {model_path}")
        
        self.model = YOLO(model_path)
        self.model.to(self.device)

    def detect(self, image: Union[str, np.ndarray], conf_threshold: float = 0.30) -> List[Dict]:
        """
        Performs object detection on the input image.

        :param image: Path to the image file or an image array (BGR format).
        :param conf_threshold: Confidence threshold for detections.
        :return: List of detections with class names, confidence scores, and bounding boxes.
        """
        # Load and preprocess the image
        if isinstance(image, str):
            img = cv2.imread(image)
            if img is None:
                raise ValueError(f"Image at path '{image}' could not be loaded.")
        else:
            img = image

        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Perform detection
        results = self.model(img_rgb)

        # Extract detections
        detections = []
        result = results[0]  # Get the first (and usually only) result
        boxes = result.boxes
        for box in boxes:
            xmin, ymin, xmax, ymax = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            class_name = self.model.names[cls]
            detections.append({
                'class': class_name,
                'confidence': conf,
                'bbox': [xmin, ymin, xmax, ymax]
            })

        return detections

    def detect_with_annotations(self, image: Union[str, np.ndarray], conf_threshold: float = 0.30) -> Tuple[List[Dict], np.ndarray]:
        """
        Performs object detection and returns both detections and annotated image.

        :param image: Path to the image file or an image array (BGR format).
        :param conf_threshold: Confidence threshold for detections.
        :return: Tuple of (detections, annotated_image)
        """
        # Load and preprocess the image
        if isinstance(image, str):
            img = cv2.imread(image)
            if img is None:
                raise ValueError(f"Image at path '{image}' could not be loaded.")
        else:
            img = image.copy()

        # Get detections
        detections = self.detect(image, conf_threshold)
        
        # Draw bounding boxes on the image
        annotated_img = self.draw_bounding_boxes(img, detections)
        
        return detections, annotated_img

    def draw_bounding_boxes(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draws bounding boxes and labels on the image.

        :param image: Input image (BGR format).
        :param detections: List of detection dictionaries.
        :return: Annotated image with bounding boxes.
        """
        annotated_img = image.copy()
        
        for detection in detections:
            bbox = detection['bbox']
            class_name = detection['class']
            confidence = detection['confidence']
            
            xmin, ymin, xmax, ymax = bbox
            
            # Draw bounding box
            cv2.rectangle(annotated_img, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            
            # Create label text
            label = f"{class_name}: {confidence:.2f}"
            
            # Get text size for background rectangle
            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            # Draw background rectangle for text
            cv2.rectangle(annotated_img, (xmin, ymin - text_height - 10), (xmin + text_width, ymin), (0, 255, 0), -1)
            
            # Draw text
            cv2.putText(annotated_img, label, (xmin, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return annotated_img
