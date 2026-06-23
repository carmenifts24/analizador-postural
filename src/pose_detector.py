"""
Módulo de detección de pose corporal usando MediaPipe Pose.

Expone la clase PoseDetector que encapsula el ciclo completo:
  1. Normalización de la imagen de entrada a RGB uint8.
  2. Inferencia del modelo de pose (33 landmarks corporales).
  3. Dibujado de conexiones esqueléticas sobre la imagen.
  4. Extracción y desnormalización de los 12 puntos articulares
     relevantes para el análisis postural.
  5. Cálculo de métricas posturales mediante posture_metrics.
"""

from __future__ import annotations  # habilita anotaciones de tipo diferidas (PEP 563); permite referencias a tipos definidos más abajo en el archivo

from dataclasses import dataclass
from typing import Any

import cv2
import mediapipe as mp
import numpy as np

from src.posture_metrics import compute_posture_metrics


# Agrupa todos los resultados de un análisis en un único objeto de retorno,
# evitando devolver tuplas con múltiples elementos sin nombre.
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
        # Accesos directos a los submódulos de MediaPipe para no repetir la ruta completa en cada llamada
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            enable_segmentation=False,  # la máscara de segmentación no se usa; desactivarla reduce el costo computacional
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
        annotated = image_rgb.copy()  # copia para no mutar la imagen original; draw_landmarks dibuja in-place sobre el array
        result = self.pose.process(image_rgb)

        if not result.pose_landmarks:
            return PoseResult(
                annotated_image=annotated,
                pose_detected=False,
                landmarks={},
                landmarks_found=[],
                metrics={},
            )

        # Dibuja los 33 landmarks y sus conexiones sobre la copia anotada
        self.mp_drawing.draw_landmarks(
            annotated,
            result.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_styles.get_default_pose_landmarks_style(),
        )

        # NumPy representa shape como (alto, ancho, canales); se desempaqueta en ese orden
        height, width = image_rgb.shape[:2]
        landmarks = _extract_landmarks(result.pose_landmarks, self.mp_pose, width, height)
        metrics = compute_posture_metrics(landmarks)
        return PoseResult(
            annotated_image=annotated,
            pose_detected=True,
            landmarks=landmarks,
            landmarks_found=sorted(landmarks.keys()),  # orden alfabético para salida determinista independiente del modelo
            metrics=metrics,
        )

    def close(self) -> None:
        self.pose.close()

    # __enter__ y __exit__ implementan el protocolo de gestor de contexto,
    # lo que permite usar `with PoseDetector() as pd:` y garantiza que
    # close() se invoque incluso si ocurre una excepción.
    def __enter__(self) -> "PoseDetector":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _ensure_rgb_uint8(image: np.ndarray) -> np.ndarray:
    """Normaliza la entrada a RGB uint8 para evitar errores de librerias."""
    if image is None:
        raise ValueError("No se recibio ninguna imagen.")

    image = np.asarray(image)  # convierte PIL Image, listas u otros array-like a ndarray sin copiar datos cuando ya es compatible
    if image.ndim == 2:
        # Imagen en escala de grises (sin canal de color); se replica el canal único a los tres canales RGB
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    if image.shape[-1] == 4:
        # El cuarto canal es transparencia (alpha); MediaPipe no lo soporta, por lo que se descarta
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
    if image.dtype != np.uint8:
        # Imágenes float en rango [0.0, 1.0] o con valores fuera de [0, 255] se recortan antes del cast para evitar desbordamiento
        image = np.clip(image, 0, 255).astype(np.uint8)
    return image


def _extract_landmarks(pose_landmarks, mp_pose, width: int, height: int) -> dict[str, dict[str, float]]:
    """Convierte landmarks normalizados a coordenadas en pixeles y visibilidad."""
    # Se filtran los 12 puntos articulares relevantes para la postura;
    # MediaPipe devuelve 33 landmarks en total, incluyendo cara y dedos que no se utilizan en este análisis.
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
            # MediaPipe normaliza x e y al rango [0, 1]; se multiplica por las dimensiones reales para obtener píxeles
            "x": float(landmark.x * width),
            "y": float(landmark.y * height),
            "z": float(landmark.z),                    # profundidad relativa a la cadera; ya está en unidades corporales, no requiere desnormalización
            "visibility": float(landmark.visibility),  # confianza de detección del punto [0.0 – 1.0]
        }
    return points
