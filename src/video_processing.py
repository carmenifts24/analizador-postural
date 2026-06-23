"""Procesamiento de videos cortos para PoseCheck."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile

import cv2

from src.pose_detector import PoseDetector
from src.posture_metrics import Metric, average_metrics


@dataclass
class VideoProcessingResult:
    output_path: str
    total_frames: int
    frames_analyzed: int
    frames_with_pose: int
    landmarks_found: list[str]
    average_metrics: dict[str, Metric]


def process_video_file(video_path: str, target_fps: int = 10, max_seconds: int = 10) -> VideoProcessingResult:
    """Procesa un video muestreando frames para reducir costo computacional.

    En Hugging Face Spaces conviene evitar procesar videos largos a FPS completo.
    Por eso se limita la duracion y se calcula un `sample_step` segun el FPS real.
    """
    input_path = Path(video_path)
    if not input_path.exists():
        raise FileNotFoundError(f"No se encontro el video: {video_path}")

    capture = cv2.VideoCapture(str(input_path))
    if not capture.isOpened():
        raise ValueError("OpenCV no pudo abrir el archivo de video.")

    source_fps = capture.get(cv2.CAP_PROP_FPS) or target_fps
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames_available = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    max_frames = int(min(total_frames_available or source_fps * max_seconds, source_fps * max_seconds))
    sample_step = max(int(round(source_fps / target_fps)), 1)

    output_dir = Path(tempfile.mkdtemp(prefix="posecheck_"))
    output_path = output_dir / "video_procesado.mp4"
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        min(source_fps, target_fps),
        (width, height),
    )

    metrics_per_frame = []
    landmarks_found: set[str] = set()
    frames_read = 0
    frames_analyzed = 0
    frames_with_pose = 0

    with PoseDetector(static_image_mode=False) as detector:
        while frames_read < max_frames:
            ok, frame_bgr = capture.read()
            if not ok:
                break

            if frames_read % sample_step == 0:
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                result = detector.process_image(frame_rgb)
                annotated_bgr = cv2.cvtColor(result.annotated_image, cv2.COLOR_RGB2BGR)
                writer.write(annotated_bgr)
                frames_analyzed += 1

                if result.pose_detected:
                    frames_with_pose += 1
                    metrics_per_frame.append(result.metrics)
                    landmarks_found.update(result.landmarks_found)

            frames_read += 1

    capture.release()
    writer.release()

    return VideoProcessingResult(
        output_path=str(output_path),
        total_frames=frames_read,
        frames_analyzed=frames_analyzed,
        frames_with_pose=frames_with_pose,
        landmarks_found=sorted(landmarks_found),
        average_metrics=average_metrics(metrics_per_frame),
    )
