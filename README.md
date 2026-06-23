---
title: Analizador Postural
emoji: 🧍
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
---

# Analizador Postural - PoseCheck

Analizador Postural, tambien presentado como **PoseCheck**, es una aplicacion web educativa
desarrollada en Python que permite analizar imagenes y videos cortos de una persona utilizando
**MediaPipe Pose**. La app detecta puntos clave del cuerpo, dibuja el esqueleto corporal y calcula
metricas geometricas simples para interpretar la postura de manera visual.

El proyecto se enmarca en la materia **Procesamiento de Imagenes Digitales (PDI)** del IFTS 24.
No es una herramienta medica ni realiza diagnosticos profesionales.

## Repositorios del proyecto

- Repositorio GitHub: <https://github.com/carmenifts24/analizador-postural>
- Aplicacion en Hugging Face Spaces: <https://huggingface.co/spaces/carmenmarylinrp/analizador-postural>

Estos dos repositorios representan las dos etapas del trabajo:

- **GitHub** conserva el codigo fuente, la documentacion y el historial del proyecto.
- **Hugging Face Spaces** ejecuta la aplicacion Gradio para que pueda probarse desde el navegador.

## Integrantes

- Carmen Rodriguez
- Agregar aqui otros integrantes del equipo, si corresponde.

## Proposito

El objetivo es demostrar conocimientos de:

- procesamiento de imagenes digitales;
- uso de OpenCV y NumPy;
- deteccion de pose con MediaPipe;
- calculo de metricas geometricas;
- construccion de interfaces con Gradio;
- despliegue reproducible en Hugging Face Spaces.

## Funcionalidades

La aplicacion incluye tres modos de uso:

1. **Imagen subida manualmente:** procesa archivos JPG o PNG.
2. **Webcam:** permite capturar una foto desde la camara del navegador y analizarla automaticamente.
3. **Video corto:** procesa videos breves, idealmente de 5 a 10 segundos, y devuelve un MP4 compatible con navegador.

En cada caso, PoseCheck puede devolver:

- imagen o video con landmarks corporales dibujados;
- metricas posturales basicas;
- devolucion textual educativa;
- advertencias si no se detecta una persona con suficiente confianza.

Los tres modos fueron validados localmente desde navegador: imagen, webcam y video corto.

## Metricas posturales

La primera version calcula:

- inclinacion de hombros;
- inclinacion de cadera;
- alineacion entre hombros y cadera;
- angulo de brazo izquierdo y derecho;
- angulo de pierna izquierda y derecha.

Estas metricas se calculan a partir de puntos detectados por MediaPipe. Los umbrales son
educativos y sirven para explorar la imagen, no para evaluar salud ni rendimiento fisico.

## Tecnologias utilizadas

- Python 3.11
- Gradio
- MediaPipe Pose
- OpenCV
- NumPy
- Pillow
- imageio / imageio-ffmpeg
- Hugging Face Spaces
- Docker opcional

## Instalacion local

Crear y activar un entorno virtual:

```powershell
python -m venv venv
venv\Scripts\activate
```

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

El archivo `requirements.txt` fija versiones compatibles de `gradio_client`,
`huggingface_hub`, `fastapi` y `pydantic` porque Gradio 4.44.0 puede fallar con versiones
transitivas demasiado nuevas de esas librerias.

Ejecutar la aplicacion:

```powershell
python app.py
```

Luego abrir:

```text
http://localhost:7860
```

### Nota para Windows

Si Windows bloquea `pip.exe` con un mensaje de Control de aplicaciones, usar:

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
```

Esta variante usa `pip` como modulo de Python y evita ejecutar directamente `pip.exe`.

Si Gradio informa que `localhost` no es accesible por configuracion de red o proxy, se puede
ejecutar temporalmente con enlace publico de Gradio:

```powershell
$env:GRADIO_SHARE="true"
venv\Scripts\python.exe app.py
```

Para volver al modo local:

```powershell
Remove-Item Env:\GRADIO_SHARE
```

## Uso de la aplicacion

### Modo imagen

1. Abrir la pestana **Imagen**.
2. Subir una imagen JPG o PNG.
3. Presionar **Analizar imagen**.
4. Revisar la imagen procesada, la tabla de metricas y la devolucion textual.

### Modo webcam

1. Abrir la pestana **Webcam**.
2. Permitir el uso de la camara en el navegador.
3. Capturar una foto.
4. Esperar el analisis automatico o presionar **Analizar captura** si se desea repetirlo.

### Modo video corto

1. Abrir la pestana **Video corto**.
2. Subir un video breve.
3. Presionar **Analizar video**.
4. Revisar el video anotado y el promedio de metricas.

La salida se convierte a MP4 H.264 para mejorar la reproduccion dentro de Gradio y del navegador.

Para videos se recomienda:

- duracion de 5 a 10 segundos;
- resolucion 720p o menor;
- una sola persona visible;
- buena iluminacion;
- camara estable.

## Guardado en GitHub

El repositorio principal del proyecto es:

```text
https://github.com/carmenifts24/analizador-postural
```

Flujo sugerido para subir cambios:

```powershell
git init
git branch -M main
git remote add origin https://github.com/carmenifts24/analizador-postural.git
git add .
git commit -m "Version inicial de Analizador Postural"
git push -u origin main
```

Si el repositorio local ya estaba inicializado, no hace falta repetir `git init` ni volver a
agregar el remoto. En ese caso alcanza con revisar `git remote -v`, confirmar que apunte al
repositorio correcto y luego hacer `git add`, `git commit` y `git push`.

## Despliegue en Hugging Face Spaces

El Space creado para la aplicacion es:

```text
https://huggingface.co/spaces/carmenmarylin/analizador-postural
```

Para desplegar:

1. Abrir el Space `carmenmarylin/analizador-postural`.
2. Verificar que el SDK sea **Gradio**.
3. Subir o sincronizar los archivos del proyecto:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - carpeta `src/`
   - `packages.txt`, si se usan dependencias del sistema.
4. Verificar que el README conserve el frontmatter de Hugging Face Spaces.
5. Hacer commit y push al repositorio del Space.
6. Esperar el build automatico.
7. Probar la app desde el navegador.

Tambien se puede clonar el Space y subir los archivos por Git:

```powershell
git clone https://huggingface.co/spaces/carmenmarylin/analizador-postural
```

## Ejecucion con Docker

Docker es opcional, pero mejora la reproducibilidad.

Construir la imagen:

```bash
docker build -t analizador-postural .
```

Ejecutar el contenedor:

```bash
docker run -p 7860:7860 analizador-postural
```

Abrir:

```text
http://localhost:7860
```

## Criterios de reproducibilidad

El repositorio incluye:

- `requirements.txt` con versiones fijadas;
- `packages.txt` para dependencias del sistema en Spaces;
- `Dockerfile` opcional;
- separacion de codigo en modulos;
- documentacion de instalacion, ejecucion, decisiones tecnicas y despliegue.

Los videos usados para prueba local no se versionan por defecto para evitar archivos pesados en
GitHub y Hugging Face. Si se desea incluir un ejemplo liviano, conviene comprimirlo y verificar
que el tamano sea razonable.

## Limitaciones conocidas

La aplicacion puede fallar o perder precision si:

- la persona no aparece de cuerpo completo;
- el cuerpo esta parcialmente tapado;
- hay poca iluminacion;
- la imagen tiene baja resolucion;
- aparecen varias personas en escena;
- la pose es muy compleja;
- el video es demasiado largo o pesado;
- el navegador no tiene permisos para usar la camara.

## Relacion con PDI

PoseCheck integra varios contenidos trabajados en la materia:

- representacion digital de imagenes como arreglos numericos;
- conversion entre formatos RGB y BGR;
- lectura y escritura de imagenes y videos con OpenCV;
- extraccion de informacion visual mediante landmarks;
- calculo geometrico sobre puntos de la imagen;
- construccion de una interfaz para experimentar con entradas reales;
- despliegue reproducible de una aplicacion de vision artificial.

## Aviso importante

PoseCheck es una herramienta educativa. Sus resultados son orientativos y dependen de la
calidad de la imagen, la iluminacion, la posicion de la persona y la deteccion de MediaPipe.
No debe usarse para diagnostico medico, rehabilitacion, ergonomia profesional ni evaluacion
clinica.
