"""
Módulo de procesamiento de video para análisis postural.

Implementa un pipeline de muestreo de frames que:
  1. Abre el video con OpenCV y calcula un paso de muestreo para aproximar
     el target_fps sin procesar todos los frames.
  2. Analiza cada frame seleccionado con PoseDetector.
  3. Escribe los frames anotados en un archivo temporal con codec mp4v.
  4. Convierte ese archivo a H.264 con ffmpeg para compatibilidad con navegadores.
  5. Devuelve las métricas promedio de todos los frames donde se detectó pose.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile

import cv2
import imageio_ffmpeg

from src.pose_detector import PoseDetector
from src.posture_metrics import Metric, average_metrics


# Agrupa todos los resultados del video en un único objeto de retorno.
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

    # Algunos contenedores no reportan el FPS; se usa target_fps como fallback para no dividir por cero
    source_fps = capture.get(cv2.CAP_PROP_FPS) or target_fps
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames_available = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    # total_frames_available puede ser 0 si el contenedor no lo reporta; en ese caso se estima por duración
    max_frames = int(min(total_frames_available or source_fps * max_seconds, source_fps * max_seconds))
    # Cuántos frames del video original equivalen a un frame del target_fps deseado
    sample_step = max(int(round(source_fps / target_fps)), 1)

    output_dir = Path(tempfile.mkdtemp(prefix="posecheck_"))
    # Dos archivos: raw usa el codec mp4v que OpenCV escribe nativamente;
    # el definitivo será recodificado a H.264 por ffmpeg para compatibilidad con navegadores.
    raw_output_path = output_dir / "video_procesado_raw.mp4"
    output_path = output_dir / "video_procesado.mp4"
    writer = cv2.VideoWriter(
        str(raw_output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),  # fourcc es el código de 4 caracteres que identifica el codec
        min(source_fps, target_fps),      # el video de salida no puede tener más FPS de los que se analizan
        (width, height),
    )

    if not writer.isOpened():
        capture.release()
        raise ValueError("OpenCV no pudo crear el archivo de video de salida.")

    metrics_per_frame = []
    landmarks_found: set[str] = set()  # set para deduplicar automáticamente landmarks vistos en distintos frames
    frames_read = 0
    frames_analyzed = 0
    frames_with_pose = 0

    # static_image_mode=False activa el modo de seguimiento entre frames,
    # más eficiente para video que volver a detectar la pose desde cero en cada frame.
    with PoseDetector(static_image_mode=False) as detector:
        while frames_read < max_frames:
            ok, frame_bgr = capture.read()
            if not ok:
                break

            if frames_read % sample_step == 0:
                # OpenCV lee en BGR; MediaPipe y PoseDetector esperan RGB
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                result = detector.process_image(frame_rgb)
                # cv2.VideoWriter también escribe en BGR
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

    browser_output_path = _convert_to_browser_mp4(raw_output_path, output_path)

    return VideoProcessingResult(
        output_path=str(browser_output_path),
        total_frames=frames_read,
        frames_analyzed=frames_analyzed,
        frames_with_pose=frames_with_pose,
        landmarks_found=sorted(landmarks_found),
        average_metrics=average_metrics(metrics_per_frame),
    )


def _convert_to_browser_mp4(input_path: Path, output_path: Path) -> Path:
    """Convierte el video a H.264 para que el navegador lo reproduzca.

    OpenCV puede escribir MP4 con `mp4v`, pero algunos navegadores o componentes
    de Gradio no lo muestran correctamente. `imageio-ffmpeg` trae un binario de
    ffmpeg reproducible, util tanto localmente como en Hugging Face Spaces.
    """
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()  # ruta al binario de ffmpeg empaquetado en el paquete Python
    command = [
        ffmpeg,
        "-y",           # sobreescribe el archivo de salida sin preguntar (modo no interactivo)
        "-i",
        str(input_path),
        "-vcodec",
        "libx264",      # H.264: codec de video estándar soportado por todos los navegadores modernos
        "-pix_fmt",
        "yuv420p",      # formato de píxel requerido por H.264 para compatibilidad con reproductores HTML5; sin esto algunos navegadores rechazan el video
        "-movflags",
        "+faststart",   # mueve el átomo 'moov' al inicio del archivo para que el navegador pueda reproducir antes de descargar todo
        str(output_path),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        # Si ffmpeg falla por cualquier motivo se devuelve el video raw como fallback
        return input_path

    # Verificación extra: ffmpeg puede crear un archivo vacío ante ciertos errores silenciosos
    return output_path if output_path.exists() and output_path.stat().st_size > 0 else input_path
