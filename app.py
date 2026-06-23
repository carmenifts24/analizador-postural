"""Interfaz principal de PoseCheck.

Este archivo es el punto de entrada para Hugging Face Spaces. La logica de
vision artificial esta separada en `src/` para que el proyecto sea mas facil de
leer, probar y defender.
"""

from __future__ import annotations

import traceback
from typing import Any

import gradio as gr

from src.pose_detector import PoseDetector
from src.posture_metrics import format_metrics_table, summarize_feedback
from src.video_processing import process_video_file


APP_TITLE = "Analizador Postural - PoseCheck"
DISCLAIMER = (
    "PoseCheck es una herramienta educativa de procesamiento de imagenes. "
    "No realiza diagnosticos medicos ni reemplaza la evaluacion profesional."
)


def _empty_image_response(message: str) -> tuple[None, list[list[Any]], str]:
    return None, [], f"### Resultado\n\n{message}\n\n{DISCLAIMER}"


def analyze_image(image):
    """Procesa una imagen estatica recibida desde archivo o webcam."""
    if image is None:
        return _empty_image_response("Cargue o capture una imagen para comenzar.")

    try:
        with PoseDetector(static_image_mode=True) as detector:
            result = detector.process_image(image)

        if not result.pose_detected:
            return (
                result.annotated_image,
                [],
                "### Resultado\n\nNo se detecto una persona con confianza suficiente. "
                "Pruebe con una imagen iluminada, de cuerpo mas completo y con una sola persona visible.\n\n"
                f"{DISCLAIMER}",
            )

        table = format_metrics_table(result.metrics)
        feedback = summarize_feedback(result.metrics, result.landmarks_found)
        return result.annotated_image, table, f"### Resultado\n\n{feedback}\n\n{DISCLAIMER}"
    except Exception as exc:  # pragma: no cover - ayuda a depurar en Spaces
        detail = traceback.format_exc()
        return (
            None,
            [],
            "### Error durante el procesamiento\n\n"
            f"`{type(exc).__name__}: {exc}`\n\n"
            "Revise las dependencias y el formato del archivo cargado.\n\n"
            f"<details><summary>Detalle tecnico</summary>\n\n```text\n{detail}\n```\n\n</details>",
        )


def analyze_video(video_path):
    """Procesa un video corto y devuelve un video anotado mas un resumen."""
    if not video_path:
        return None, [], "### Resultado\n\nCargue un video corto para comenzar."

    try:
        result = process_video_file(video_path)
        table = format_metrics_table(result.average_metrics)
        feedback = (
            f"Se analizaron {result.frames_analyzed} frames de {result.total_frames} frames leidos. "
            f"Se detecto pose en {result.frames_with_pose} frames.\n\n"
            f"{summarize_feedback(result.average_metrics, result.landmarks_found)}"
        )

        if result.frames_with_pose == 0:
            feedback = (
                f"Se analizaron {result.frames_analyzed} frames, pero no se detecto una persona "
                "con confianza suficiente. Pruebe con un video mas iluminado, estable y de cuerpo completo."
            )

        return result.output_path, table, f"### Resultado\n\n{feedback}\n\n{DISCLAIMER}"
    except Exception as exc:  # pragma: no cover - ayuda a depurar en Spaces
        detail = traceback.format_exc()
        return (
            None,
            [],
            "### Error durante el procesamiento del video\n\n"
            f"`{type(exc).__name__}: {exc}`\n\n"
            "Use videos cortos, idealmente de 5 a 10 segundos y 720p o menor.\n\n"
            f"<details><summary>Detalle tecnico</summary>\n\n```text\n{detail}\n```\n\n</details>",
        )


with gr.Blocks(title="Analizador Postural", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        f"""
        # {APP_TITLE}

        Aplicacion web educativa con MediaPipe Pose y Gradio para detectar landmarks
        corporales, dibujar el esqueleto y calcular metricas geometricas simples de postura.

        **Importante:** {DISCLAIMER}
        """
    )

    with gr.Tabs():
        with gr.Tab("Imagen"):
            with gr.Row():
                image_input = gr.Image(
                    label="Subir imagen JPG o PNG",
                    sources=["upload"],
                    type="numpy",
                )
                image_output = gr.Image(label="Imagen procesada", type="numpy")
            image_button = gr.Button("Analizar imagen", variant="primary")
            image_metrics = gr.Dataframe(
                headers=["Metrica", "Valor", "Interpretacion"],
                datatype=["str", "str", "str"],
                label="Metricas posturales",
                interactive=False,
            )
            image_feedback = gr.Markdown()
            image_button.click(
                analyze_image,
                inputs=image_input,
                outputs=[image_output, image_metrics, image_feedback],
            )

        with gr.Tab("Webcam"):
            with gr.Row():
                webcam_input = gr.Image(
                    label="Capturar foto desde webcam",
                    sources=["webcam"],
                    type="numpy",
                )
                webcam_output = gr.Image(label="Imagen procesada", type="numpy")
            webcam_button = gr.Button("Analizar captura", variant="primary")
            webcam_metrics = gr.Dataframe(
                headers=["Metrica", "Valor", "Interpretacion"],
                datatype=["str", "str", "str"],
                label="Metricas posturales",
                interactive=False,
            )
            webcam_feedback = gr.Markdown()
            webcam_button.click(
                analyze_image,
                inputs=webcam_input,
                outputs=[webcam_output, webcam_metrics, webcam_feedback],
            )

        with gr.Tab("Video corto"):
            gr.Markdown(
                "Use videos breves, preferentemente de 5 a 10 segundos, con una sola persona visible."
            )
            with gr.Row():
                video_input = gr.Video(label="Subir video", sources=["upload"])
                video_output = gr.Video(label="Video procesado")
            video_button = gr.Button("Analizar video", variant="primary")
            video_metrics = gr.Dataframe(
                headers=["Metrica", "Valor", "Interpretacion"],
                datatype=["str", "str", "str"],
                label="Promedio de metricas",
                interactive=False,
            )
            video_feedback = gr.Markdown()
            video_button.click(
                analyze_video,
                inputs=video_input,
                outputs=[video_output, video_metrics, video_feedback],
            )

    gr.Markdown(
        """
        ### Criterios de lectura

        Las metricas se calculan a partir de puntos corporales detectados por MediaPipe.
        Sirven para explorar alineaciones e inclinaciones en una imagen, no para evaluar salud,
        rendimiento deportivo ni diagnosticar condiciones clinicas.
        """
    )


if __name__ == "__main__":
    demo.launch()
