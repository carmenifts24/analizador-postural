"""Deteccion de pose corporal con MediaPipe."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import mediapipe as mp
import numpy as np

from src.posture_metrics import compute_posture_metrics


@dataclass
class PoseResult:
    annotated_image: np.ndarray
    pose_detected: bool
    landmarks: dict[str, dict[str, float]]
    landmarks_found: list[str]
    metrics: dict[str, dict[str, Any]]


class PoseDetector:
    """Encapsula MediaPipe Pose para mantener limpio el codigo de la app."""

    def __init__(
        self,
        static_image_mode: bool = True,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def process_image(self, image_rgb: np.ndarray) -> PoseResult:
        """Detecta pose y devuelve la imagen RGB anotada.

        Gradio entrega imagenes como arreglos NumPy en RGB. MediaPipe tambien
        procesa RGB, mientras que OpenCV dibuja y escribe habitualmente en BGR.
        Por eso se explicita el formato en cada paso.
        """
        image_rgb = _ensure_rgb_uint8(image_rgb)
        annotated = image_rgb.copy()
        result = self.pose.process(image_rgb)

        if not result.pose_landmarks:
            return PoseResult(
                annotated_image=annotated,
                pose_detected=False,
                landmarks={},
                landmarks_found=[],
                metrics={},
            )

        self.mp_drawing.draw_landmarks(
            annotated,
            result.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_styles.get_default_pose_landmarks_style(),
        )

        height, width = image_rgb.shape[:2]
        landmarks = _extract_landmarks(result.pose_landmarks, self.mp_pose, width, height)
        metrics = compute_posture_metrics(landmarks)
        return PoseResult(
            annotated_image=annotated,
            pose_detected=True,
            landmarks=landmarks,
            landmarks_found=sorted(landmarks.keys()),
            metrics=metrics,
        )

    def close(self) -> None:
        self.pose.close()

    def __enter__(self) -> "PoseDetector":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _ensure_rgb_uint8(image: np.ndarray) -> np.ndarray:
    """Normaliza la entrada a RGB uint8 para evitar errores de librerias."""
    if image is None:
        raise ValueError("No se recibio ninguna imagen.")

    image = np.asarray(image)
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    if image.shape[-1] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)
    return image


def _extract_landmarks(pose_landmarks, mp_pose, width: int, height: int) -> dict[str, dict[str, float]]:
    """Convierte landmarks normalizados a coordenadas en pixeles y visibilidad."""
    selected = {
        "left_shoulder": mp_pose.PoseLandmark.LEFT_SHOULDER,
        "right_shoulder": mp_pose.PoseLandmark.RIGHT_SHOULDER,
        "left_elbow": mp_pose.PoseLandmark.LEFT_ELBOW,
        "right_elbow": mp_pose.PoseLandmark.RIGHT_ELBOW,
        "left_wrist": mp_pose.PoseLandmark.LEFT_WRIST,
        "right_wrist": mp_pose.PoseLandmark.RIGHT_WRIST,
        "left_hip": mp_pose.PoseLandmark.LEFT_HIP,
        "right_hip": mp_pose.PoseLandmark.RIGHT_HIP,
        "left_knee": mp_pose.PoseLandmark.LEFT_KNEE,
        "right_knee": mp_pose.PoseLandmark.RIGHT_KNEE,
        "left_ankle": mp_pose.PoseLandmark.LEFT_ANKLE,
        "right_ankle": mp_pose.PoseLandmark.RIGHT_ANKLE,
    }

    points: dict[str, dict[str, float]] = {}
    for name, landmark_id in selected.items():
        landmark = pose_landmarks.landmark[landmark_id.value]
        points[name] = {
            "x": float(landmark.x * width),
            "y": float(landmark.y * height),
            "z": float(landmark.z),
            "visibility": float(landmark.visibility),
        }
    return points
