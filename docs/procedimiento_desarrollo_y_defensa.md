# Procedimiento de desarrollo y guia para defensa

## Objetivo del proyecto

El objetivo de Analizador Postural - PoseCheck es construir una aplicacion web educativa capaz de
recibir imagenes, capturas de webcam y videos cortos para detectar pose corporal con MediaPipe
Pose. La aplicacion dibuja landmarks sobre el cuerpo, calcula metricas geometricas simples y
devuelve una interpretacion textual clara.

El proyecto no busca diagnosticar problemas medicos. Su valor esta en demostrar contenidos de
Procesamiento de Imagenes Digitales: representacion de imagenes, uso de OpenCV y NumPy, deteccion
de landmarks, calculos geometricos, interfaz web con Gradio y despliegue reproducible.

## Estructura creada

La aplicacion se organizo en archivos separados para que el codigo sea defendible y facil de
explicar:

- `app.py`: define la interfaz Gradio y conecta los tres modos de entrada.
- `src/pose_detector.py`: contiene la integracion con MediaPipe Pose.
- `src/posture_metrics.py`: calcula e interpreta metricas posturales.
- `src/video_processing.py`: procesa videos cortos frame por frame.
- `requirements.txt`: fija dependencias de Python.
- `packages.txt`: declara dependencias del sistema para Hugging Face Spaces.
- `Dockerfile`: permite ejecutar el proyecto en un entorno reproducible opcional.
- `docs/decisiones_tecnicas.md`: resume decisiones tecnicas principales.

Esta separacion evita tener toda la logica mezclada en un unico archivo. Para una defensa oral,
permite explicar primero la interfaz, luego la deteccion, despues las metricas y finalmente el
despliegue.

## Flujo general de procesamiento

El flujo de trabajo es el mismo para imagen, webcam y video:

1. El usuario carga una entrada visual.
2. Gradio recibe la imagen o el archivo de video.
3. El backend procesa la entrada con OpenCV y MediaPipe Pose.
4. MediaPipe devuelve landmarks corporales.
5. El sistema dibuja el esqueleto corporal sobre la imagen o frame.
6. Se calculan metricas geometricas simples.
7. La interfaz muestra salida visual, tabla de metricas y texto interpretativo.

En imagen y webcam se procesa una sola imagen. En video se procesa una muestra de frames para
reducir costo computacional.

## Por que se eligio MediaPipe Pose

MediaPipe Pose es adecuado para este proyecto porque permite detectar puntos corporales sin
entrenar una red neuronal propia. Eso permite concentrar el trabajo en el procesamiento de imagen,
la interpretacion geometrica y la integracion con una interfaz.

Desde el punto de vista academico, esta decision es importante: el proyecto no intenta competir
con modelos profesionales de analisis biomecanico, sino usar un modelo preentrenado para construir
una aplicacion clara, reproducible y explicable.

## Por que se uso Gradio

Gradio permite crear una interfaz web simple directamente en Python. Es una buena herramienta para
proyectos de vision artificial porque acepta imagenes, webcam y videos como componentes de entrada.

Ademas, Hugging Face Spaces soporta Gradio de forma directa. Por eso `app.py` funciona como punto
de entrada tanto localmente como en el despliegue.

## Modo imagen

En el modo imagen, el usuario sube un archivo JPG o PNG. Gradio entrega esa imagen como un arreglo
NumPy en formato RGB. El sistema la procesa con MediaPipe Pose, dibuja landmarks y devuelve:

- imagen anotada;
- tabla de metricas;
- devolucion textual educativa.

Este modo es el mas simple y sirve para comprobar que la deteccion de pose funciona correctamente.

## Modo webcam

En el modo webcam, el navegador pide permiso para usar la camara. Gradio captura una foto y la
envia al backend como una imagen estatica. El procesamiento es el mismo que en el modo imagen.

Durante las pruebas, el boton de webcam podia no mostrar actividad de forma clara. Para resolverlo,
se agrego un evento automatico: cuando cambia la imagen capturada, se dispara el analisis. Tambien
se conserva el boton **Analizar captura** para repetir el procesamiento manualmente.

Esta mejora se hizo para que la experiencia sea mas confiable en distintos navegadores.

## Modo video corto

En el modo video, el usuario sube un archivo breve. OpenCV abre el video, lee sus propiedades y
procesa una muestra de frames. No se procesa necesariamente cada frame, porque eso puede ser
costoso en Hugging Face Spaces.

Por cada frame analizado:

1. OpenCV lee el frame en BGR.
2. Se convierte a RGB para MediaPipe.
3. MediaPipe detecta landmarks corporales.
4. Se dibuja el esqueleto.
5. Se guardan metricas del frame.
6. El frame anotado se escribe en un video de salida.

Al final se calcula un promedio de metricas sobre los frames donde hubo pose detectada.

## Por que se convirtio el video de salida

Al probar el modo video, las metricas aparecian correctamente, pero el panel de video procesado no
mostraba la reproduccion. Eso indicaba que el procesamiento funcionaba, pero el archivo generado
no era suficientemente compatible con el reproductor del navegador.

OpenCV puede escribir MP4 con codec `mp4v`, pero algunos navegadores o componentes web no lo
reproducen bien. Por eso se agrego una conversion final con `imageio-ffmpeg` a:

- MP4;
- codec H.264;
- formato de pixeles `yuv420p`;
- `faststart` para reproduccion web.

Esta decision no cambia el analisis de pose, pero mejora la compatibilidad visual de la salida.

## Metricas implementadas

Las metricas se calculan a partir de landmarks detectados:

- inclinacion de hombros;
- inclinacion de cadera;
- alineacion entre hombros y cadera;
- angulo de brazo izquierdo;
- angulo de brazo derecho;
- angulo de pierna izquierda;
- angulo de pierna derecha.

La inclinacion se calcula observando la diferencia angular entre dos puntos, por ejemplo hombro
izquierdo y hombro derecho. La alineacion hombros-cadera compara el centro de los hombros con el
centro de la cadera. Los angulos de brazos y piernas se calculan con tres puntos, por ejemplo
hombro, codo y muneca.

Estas metricas son geometricas y educativas. No significan que la postura sea correcta o incorrecta
desde un punto de vista medico.

## Manejo de RGB y BGR

Una parte importante del proyecto es entender los formatos de color:

- Gradio trabaja comodamente con imagenes RGB.
- MediaPipe Pose procesa imagenes RGB.
- OpenCV suele leer y escribir imagenes y videos en BGR.

Por eso, en video se convierten frames de BGR a RGB antes de MediaPipe y luego de RGB a BGR antes
de escribir el video de salida. Sin esa conversion, los colores podrian verse alterados.

## Problemas encontrados y soluciones

Durante la prueba local aparecieron varios problemas reales de entorno:

1. Windows bloqueo `pip.exe`.
   Se resolvio usando `python -m pip`, que ejecuta pip como modulo de Python.

2. Gradio fallo al importar `HfFolder`.
   La causa fue una version demasiado nueva de `huggingface_hub`. Se fijo
   `huggingface_hub==0.25.2`.

3. Gradio tuvo errores por dependencias transitivas nuevas.
   Se fijaron versiones compatibles de `gradio_client`, `fastapi` y `pydantic`.

4. El video procesado no se veia en la interfaz.
   Se agrego conversion a MP4 H.264 con `imageio-ffmpeg`.

5. La webcam no mostraba actividad al presionar el boton.
   Se agrego analisis automatico cuando cambia la captura de webcam.

Estas soluciones son parte importante del proyecto porque muestran reproducibilidad y capacidad de
depuracion, no solo escritura de codigo.

## Validacion realizada

La aplicacion fue validada localmente desde navegador en los tres modos:

- imagen subida manualmente;
- captura desde webcam;
- video corto cargado manualmente.

En las pruebas, el sistema devolvio salida visual, metricas posturales y texto interpretativo. En
video, luego de la conversion a H.264, tambien se mostro correctamente el video procesado.

## Como explicar el proyecto en clase

Una forma clara de presentar el proyecto es seguir este orden:

1. Explicar el problema: analizar visualmente una postura de forma educativa.
2. Aclarar el limite: no es diagnostico medico.
3. Mostrar la interfaz con sus tres entradas.
4. Explicar que MediaPipe detecta landmarks corporales.
5. Mostrar que los landmarks se transforman en metricas geometricas.
6. Explicar una metrica concreta, por ejemplo inclinacion de hombros.
7. Mostrar el modo video y explicar el muestreo de frames.
8. Explicar por que se hizo la conversion a H.264.
9. Mencionar reproducibilidad: requirements, README, Dockerfile y Spaces.
10. Cerrar con limitaciones y posibles mejoras.

## Posibles mejoras futuras

El proyecto puede crecer sin cambiar su objetivo educativo:

- agregar capturas de pantalla al README;
- incluir ejemplos livianos de imagen y video;
- permitir descargar un reporte en texto;
- mostrar graficos de evolucion de metricas en video;
- mejorar umbrales segun distancia a camara o resolucion;
- agregar una pagina de ayuda dentro de la app.

Estas mejoras no son obligatorias para la version base. La prioridad actual es que la aplicacion
sea clara, funcional, reproducible y facil de defender.

## Resumen para defensa oral

Analizador Postural - PoseCheck es una aplicacion educativa de vision artificial. Usa Gradio para
la interfaz, MediaPipe Pose para detectar puntos corporales, OpenCV para leer y escribir imagenes
y videos, y funciones geometricas propias para calcular metricas simples. La aplicacion permite
analizar imagenes, webcam y videos cortos. El resultado incluye una salida visual con esqueleto
corporal, una tabla de metricas y una devolucion textual. El proyecto esta documentado y preparado
para desplegarse en Hugging Face Spaces.
