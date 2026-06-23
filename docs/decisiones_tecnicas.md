# Decisiones tecnicas

## Eleccion de MediaPipe Pose

MediaPipe Pose permite detectar landmarks corporales sin entrenar un modelo desde cero. Para
este proyecto es una buena eleccion porque el objetivo academico es integrar vision artificial,
procesamiento de imagenes e interfaz web, no construir un detector propio.

## Separacion de responsabilidades

- `app.py` define la interfaz Gradio y conecta los modos de entrada.
- `src/pose_detector.py` concentra la inicializacion de MediaPipe y el dibujo de landmarks.
- `src/posture_metrics.py` calcula metricas geometricas simples e interpretables.
- `src/video_processing.py` procesa videos cortos con muestreo de frames.

Esta separacion hace que el codigo sea mas facil de leer, explicar y modificar.

## Interfaz en Gradio

La interfaz se organiza en tres pestanas para separar claramente los modos de entrada:

- imagen subida manualmente;
- captura desde webcam;
- video corto.

El modo webcam ejecuta el analisis cuando cambia la imagen capturada y tambien conserva un boton
manual para repetir el procesamiento. Esta decision mejora la experiencia porque algunos navegadores
no hacen evidente si la foto ya fue enviada al backend.

## Formatos RGB y BGR

Gradio y MediaPipe trabajan comodamente con imagenes RGB. OpenCV, en cambio, suele leer y
escribir en BGR. Por eso el proyecto convierte de forma explicita entre RGB y BGR cuando
procesa videos. Esta decision evita colores invertidos en las salidas.

## Metricas elegidas

Las metricas son geometricas y simples:

- inclinacion de hombros;
- inclinacion de cadera;
- alineacion entre centro de hombros y centro de cadera;
- angulos estimados de brazos y piernas.

Estas mediciones son utiles para una lectura educativa de la imagen, pero no alcanzan para
emitir diagnosticos medicos ni conclusiones profesionales.

## Procesamiento de video

Los videos se limitan a una duracion recomendada de 5 a 10 segundos y se muestrean a un FPS
objetivo. Esto reduce el costo computacional y mejora la probabilidad de que la app funcione
correctamente en Hugging Face Spaces.

La salida de video se transcodifica a MP4 con H.264 y `yuv420p`. OpenCV puede generar archivos
MP4 validos con otros codecs, pero algunos navegadores no los reproducen dentro de Gradio. Esta
conversion prioriza compatibilidad para la visualizacion web.

## Dependencias fijadas

El proyecto fija versiones de `gradio_client`, `huggingface_hub`, `fastapi` y `pydantic` porque
Gradio 4.44.0 puede instalar dependencias transitivas mas nuevas que rompen el arranque local.
Fijar versiones mejora la reproducibilidad del entorno y reduce diferencias entre Windows,
GitHub y Hugging Face Spaces.

## Limitaciones

La deteccion puede fallar con baja iluminacion, cuerpos parcialmente tapados, varias personas
en escena, baja resolucion o poses muy complejas. Por eso la interfaz comunica que el resultado
es orientativo y educativo.
