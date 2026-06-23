"""Interfaz principal de PoseCheck.

Este archivo es el punto de entrada para Hugging Face Spaces. La logica de
vision artificial esta separada en `src/` para que el proyecto sea mas facil de
leer, probar y defender.

La UI tiene tres pestañas:
  - Imagen: carga de archivo JPG/PNG para análisis de pose estático.
  - Webcam: captura directa desde la cámara del dispositivo.
  - Video corto: análisis frame a frame con métricas promediadas.
"""

from __future__ import annotations

import os
import traceback
from typing import Any

import gradio as gr

from src.pose_detector import PoseDetector
from src.posture_metrics import format_metrics_table, summarize_feedback
from src.video_processing import process_video_file


APP_TITLE = "Analizador Postural - PoseCheck"
# Centralizado para garantizar que aparezca de forma idéntica en todas las salidas de la UI
DISCLAIMER = (
    "PoseCheck es una herramienta educativa de procesamiento de imagenes. "
    "No realiza diagnosticos medicos ni reemplaza la evaluacion profesional."
)


def _empty_image_response(message: str) -> tuple[None, list[list[Any]], str]:
    # Devuelve la tupla de tres elementos que Gradio espera (imagen, tabla, texto),
    # evitando repetir la misma estructura en cada rama de retorno anticipado.
    return None, [], f"### Resultado\n\n{message}\n\n{DISCLAIMER}"


def analyze_image(image):
    """Procesa una imagen estatica recibida desde archivo o webcam."""
    if image is None:
        return _empty_image_response("Cargue o capture una imagen para comenzar.")

    try:
        # static_image_mode=True: cada imagen se detecta independientemente,
        # sin seguimiento entre frames (apropiado para imágenes sueltas).
        # El gestor de contexto garantiza que detector.close() se llame siempre.
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
        # traceback.format_exc() captura el stack trace completo como string
        # para mostrarlo en la UI sin interrumpir la aplicación.
        detail = traceback.format_exc()
        return (
            None,
            [],
            "### Error durante el procesamiento\n\n"
            f"`{type(exc).__name__}: {exc}`\n\n"
            "Revise las dependencias y el formato del archivo cargado.\n\n"
            # <details> es HTML válido dentro de Markdown de Gradio;
            # crea una sección colapsable para que el detalle técnico no sature la salida principal.
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

        # Si no se detectó pose en ningún frame el feedback genérico es engañoso; se reemplaza completo
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
                    sources=["upload"],  # solo carga de archivo, sin cámara en esta pestaña
                    type="numpy",        # Gradio entrega la imagen como array NumPy, que es lo que espera PoseDetector
                )
                image_output = gr.Image(label="Imagen procesada", type="numpy")
            image_button = gr.Button("Analizar imagen", variant="primary")
            image_metrics = gr.Dataframe(
                headers=["Metrica", "Valor", "Interpretacion"],
                datatype=["str", "str", "str"],
                label="Metricas posturales",
                interactive=False,  # la tabla es solo lectura; el usuario no debe poder editar los resultados
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
                    sources=["webcam"],  # solo cámara, sin carga de archivo en esta pestaña
                    type="numpy",
                    interactive=True,
                    mirror_webcam=True,  # espeja el preview para que se vea como un selfie (más intuitivo)
                )
                webcam_output = gr.Image(label="Imagen procesada", type="numpy")
            webcam_button = gr.Button("Analizar captura", variant="primary")
            webcam_metrics = gr.Dataframe(
                headers=["Metrica", "Valor", "Interpretacion"],
                datatype=["str", "str", "str"],
                label="Metricas posturales",
                interactive=False,
            )
            webcam_feedback = gr.Markdown(
                "### Resultado\n\nActive la camara, tome una foto y espere el analisis. "
                "Si el navegador pide permisos, debe aceptarlos para que Gradio reciba la imagen."
            )
            # .change dispara el análisis automáticamente cada vez que la webcam captura un frame nuevo
            webcam_input.change(
                analyze_image,
                inputs=webcam_input,
                outputs=[webcam_output, webcam_metrics, webcam_feedback],
                show_progress="full",  # muestra una barra de carga durante la inferencia
            )
            # .click permite al usuario repetir el análisis sobre la misma captura sin mover la cámara
            webcam_button.click(
                analyze_image,
                inputs=webcam_input,
                outputs=[webcam_output, webcam_metrics, webcam_feedback],
                show_progress="full",
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
    # Las variables de entorno permiten configurar el servidor sin modificar el código;
    # Hugging Face Spaces las inyecta automáticamente al desplegar la aplicación.
    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        share=os.getenv("GRADIO_SHARE", "false").lower() == "true",  # crea un túnel público ngrok; debe ser False en producción
    )
