"""
Módulo de cálculo e interpretación de métricas posturales geométricas.

A partir de los 12 landmarks extraídos por PoseDetector, computa cinco
indicadores simples y defendibles en un contexto educativo introductorio:

  - Inclinación de hombros: ángulo de la línea biacromial respecto a la horizontal.
  - Inclinación de cadera: ídem para la línea biilíaca.
  - Alineación troncal: desplazamiento lateral de la línea media de hombros
    respecto a la línea media de cadera, expresado en porcentaje del ancho de hombros.
  - Ángulos articulares de brazos y piernas: ángulo formado en cada articulación
    (hombro-codo-muñeca, cadera-rodilla-tobillo).

Ninguna métrica infiere condiciones clínicas; son exploraciones visuales.
"""

from __future__ import annotations  # habilita anotaciones de tipo diferidas (PEP 563)

from math import atan2, degrees
from statistics import mean
from typing import Any


# Aliases de tipo para simplificar las firmas de funciones;
# Metric reúne los campos label/value/unit/level/message de cada indicador.
Metric = dict[str, Any]
Landmarks = dict[str, dict[str, float]]

# Umbral mínimo de confianza de MediaPipe para considerar un landmark válido.
# Por debajo de 0.45 el punto es demasiado incierto para calcular ángulos confiables.
MIN_VISIBILITY = 0.45


def compute_posture_metrics(landmarks: Landmarks) -> dict[str, Metric]:
    """Calcula metricas geometricas basicas a partir de landmarks.

    Las metricas elegidas son simples y defendibles en una materia introductoria:
    inclinacion de hombros, inclinacion de cadera, alineacion troncal y angulos
    de brazos/piernas. No infieren condiciones clinicas.
    """
    metrics: dict[str, Metric] = {}

    # Se usa el mismo umbral de 8° para hombros y cadera; valor referencial
    # para uso educativo, no un criterio clínico.
    metrics["shoulder_tilt"] = _tilt_metric(
        "Inclinacion de hombros",
        landmarks,
        "left_shoulder",
        "right_shoulder",
        warning_threshold=8.0,
    )
    metrics["hip_tilt"] = _tilt_metric(
        "Inclinacion de cadera",
        landmarks,
        "left_hip",
        "right_hip",
        warning_threshold=8.0,
    )
    metrics["torso_alignment"] = _torso_alignment_metric(landmarks)
    metrics["left_arm_angle"] = _angle_metric(
        "Angulo brazo izquierdo",
        landmarks,
        "left_shoulder",
        "left_elbow",
        "left_wrist",
    )
    metrics["right_arm_angle"] = _angle_metric(
        "Angulo brazo derecho",
        landmarks,
        "right_shoulder",
        "right_elbow",
        "right_wrist",
    )
    metrics["left_leg_angle"] = _angle_metric(
        "Angulo pierna izquierda",
        landmarks,
        "left_hip",
        "left_knee",
        "left_ankle",
    )
    metrics["right_leg_angle"] = _angle_metric(
        "Angulo pierna derecha",
        landmarks,
        "right_hip",
        "right_knee",
        "right_ankle",
    )

    return metrics


def format_metrics_table(metrics: dict[str, Metric]) -> list[list[str]]:
    rows: list[list[str]] = []
    for metric in metrics.values():
        value = metric.get("value")
        unit = metric.get("unit", "")
        # .strip() elimina el espacio sobrante cuando unit es cadena vacía
        value_text = "No disponible" if value is None else f"{value:.1f} {unit}".strip()
        rows.append([metric["label"], value_text, metric["message"]])
    return rows


def summarize_feedback(metrics: dict[str, Metric], landmarks_found: list[str]) -> str:
    """Genera una devolucion breve y docente a partir de las metricas."""
    if not metrics:
        return "No hay metricas disponibles para interpretar."

    valid_metrics = [metric for metric in metrics.values() if metric.get("value") is not None]
    warnings = [metric for metric in valid_metrics if metric.get("level") == "warning"]

    if not valid_metrics:
        return (
            "Se detecto una pose, pero los puntos necesarios no tuvieron suficiente visibilidad "
            "para calcular metricas confiables."
        )

    intro = (
        "Se detecto la pose corporal y se calcularon metricas geometricas simples "
        f"a partir de {len(landmarks_found)} landmarks relevantes."
    )
    if not warnings:
        return (
            f"{intro}\n\n"
            "En esta imagen no aparecen desalineaciones marcadas segun los umbrales educativos definidos. "
            "La lectura debe entenderse como una exploracion visual, no como evaluacion profesional."
        )

    # Se limita a 3 advertencias para no saturar el texto de retroalimentación
    warning_text = "; ".join(metric["message"] for metric in warnings[:3])
    return (
        f"{intro}\n\n"
        f"Observaciones principales: {warning_text}. "
        "Conviene revisar la posicion de la camara, la iluminacion y si el cuerpo aparece completo."
    )


def average_metrics(metrics_list: list[dict[str, Metric]]) -> dict[str, Metric]:
    """Promedia metricas del video conservando etiquetas e interpretacion."""
    if not metrics_list:
        return {}

    averaged: dict[str, Metric] = {}
    keys = metrics_list[0].keys()
    for key in keys:
        # Se toma el primer frame como plantilla para copiar label, unit y estructura;
        # solo value, message y level se recalculan con el promedio.
        base = metrics_list[0][key].copy()
        values = [metrics[key]["value"] for metrics in metrics_list if metrics[key].get("value") is not None]
        if values:
            base["value"] = mean(values)
            base["message"] = _message_for_metric(key, base["value"])
            base["level"] = _level_for_metric(key, base["value"])
        else:
            base["value"] = None
            base["message"] = "No se pudo calcular en los frames analizados."
            base["level"] = "unknown"
        averaged[key] = base
    return averaged


def _tilt_metric(
    label: str,
    landmarks: Landmarks,
    point_a: str,
    point_b: str,
    warning_threshold: float,
) -> Metric:
    if not _visible(landmarks, point_a, point_b):
        return _unavailable(label)

    a = landmarks[point_a]
    b = landmarks[point_b]
    # atan2 calcula el ángulo de la recta que une los dos puntos respecto al eje X;
    # preserva el cuadrante correcto, a diferencia de atan(dy/dx) que pierde el signo.
    angle = degrees(atan2(a["y"] - b["y"], a["x"] - b["x"]))
    # Se colapsa a [-90°, 90°] para medir solo la desviación respecto a la horizontal,
    # independientemente de cuál hombro/cadera está más alto.
    normalized = abs(_normalize_horizontal_angle(angle))
    return {
        "label": label,
        "value": normalized,
        "unit": "grados",
        "level": "warning" if normalized >= warning_threshold else "ok",
        "message": _tilt_message(label, normalized, warning_threshold),
    }


def _torso_alignment_metric(landmarks: Landmarks) -> Metric:
    needed = ("left_shoulder", "right_shoulder", "left_hip", "right_hip")
    if not _visible(landmarks, *needed):
        return _unavailable("Alineacion hombros-cadera")

    shoulder_mid_x = mean([landmarks["left_shoulder"]["x"], landmarks["right_shoulder"]["x"]])
    hip_mid_x = mean([landmarks["left_hip"]["x"], landmarks["right_hip"]["x"]])
    shoulder_width = abs(landmarks["left_shoulder"]["x"] - landmarks["right_shoulder"]["x"])
    # El ancho de hombros como referencia hace que el porcentaje sea independiente
    # de la distancia de la persona a la cámara (normalización por escala).
    reference = max(shoulder_width, 1.0)  # evita división por cero en vistas laterales donde los hombros se superponen
    offset_percent = abs(shoulder_mid_x - hip_mid_x) / reference * 100

    return {
        "label": "Alineacion hombros-cadera",
        "value": offset_percent,
        "unit": "%",
        "level": "warning" if offset_percent >= 18 else "ok",
        "message": _message_for_metric("torso_alignment", offset_percent),
    }


def _angle_metric(label: str, landmarks: Landmarks, a_name: str, b_name: str, c_name: str) -> Metric:
    if not _visible(landmarks, a_name, b_name, c_name):
        return _unavailable(label)

    a = landmarks[a_name]
    b = landmarks[b_name]
    c = landmarks[c_name]
    angle = _angle_between_points(a, b, c)
    return {
        "label": label,
        "value": angle,
        "unit": "grados",
        "level": "info",
        "message": "Angulo articular estimado desde tres landmarks visibles.",
    }


def _angle_between_points(a: dict[str, float], b: dict[str, float], c: dict[str, float]) -> float:
    # Vectores desde el vértice b hacia cada extremo de la articulación
    ba_x, ba_y = a["x"] - b["x"], a["y"] - b["y"]
    bc_x, bc_y = c["x"] - b["x"], c["y"] - b["y"]
    # La diferencia entre los ángulos polares de cada vector da el ángulo en b
    angle = abs(degrees(atan2(bc_y, bc_x) - atan2(ba_y, ba_x)))
    # Si el resultado supera 180° se toma el suplemento para obtener siempre el ángulo menor
    return 360 - angle if angle > 180 else angle


def _visible(landmarks: Landmarks, *names: str) -> bool:
    # .get con default 0 trata como invisible cualquier punto sin campo "visibility"
    return all(name in landmarks and landmarks[name].get("visibility", 0) >= MIN_VISIBILITY for name in names)


def _unavailable(label: str) -> Metric:
    return {
        "label": label,
        "value": None,
        "unit": "",
        "level": "unknown",
        "message": "No disponible por baja visibilidad de los puntos necesarios.",
    }


def _normalize_horizontal_angle(angle: float) -> float:
    # atan2 devuelve valores en [-180°, 180°]; una línea horizontal puede ser 0° o ±180°.
    # Los bucles colapsan cualquier ángulo a [-90°, 90°], donde 0° = horizontal,
    # de modo que el valor absoluto expresa la inclinación real sin importar la orientación.
    while angle > 90:
        angle -= 180
    while angle < -90:
        angle += 180
    return angle


def _tilt_message(label: str, value: float, threshold: float) -> str:
    if value >= threshold:
        return f"{label} marcada para el umbral educativo de {threshold:.0f} grados."
    return f"{label} leve o dentro del umbral educativo definido."


def _message_for_metric(key: str, value: float) -> str:
    if key == "torso_alignment":
        if value >= 18:
            return "La linea media de hombros y cadera aparece desplazada en la imagen."
        return "La linea media de hombros y cadera aparece relativamente alineada."
    if key in {"shoulder_tilt", "hip_tilt"}:
        return _tilt_message("Inclinacion", value, 8.0)
    return "Promedio estimado en los frames con landmarks visibles."


def _level_for_metric(key: str, value: float) -> str:
    if key in {"shoulder_tilt", "hip_tilt"}:
        return "warning" if value >= 8 else "ok"
    if key == "torso_alignment":
        return "warning" if value >= 18 else "ok"
    return "info"
