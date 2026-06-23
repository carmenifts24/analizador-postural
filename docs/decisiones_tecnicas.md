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

## Limitaciones

La deteccion puede fallar con baja iluminacion, cuerpos parcialmente tapados, varias personas
en escena, baja resolucion o poses muy complejas. Por eso la interfaz comunica que el resultado
es orientativo y educativo.
