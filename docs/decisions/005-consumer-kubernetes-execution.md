# Decisión 005: ejecución del consumer en Kubernetes

- **Estado:** cerrada.
- **Ámbito:** Layer 1.
- **Decisión:** ejecutar el consumer como un `Job` de Kubernetes de una sola
  ejecución, utilizando una imagen local cargada directamente en kind.

## Qué es y qué contiene la imagen local

La imagen `cmdp-consumer:0.1.0` es el entorno ejecutable del consumer. Se
construirá localmente desde el repositorio y se cargará en el clúster kind; no
se publicará en Docker Hub ni en otro registro para esta PoC.

Contendrá únicamente:

- una base Linux compatible con la arquitectura del nodo;
- Python y las dependencias fijadas necesarias para descargar el bundle,
  descifrarlo y cargar MiniLM;
- el código del consumer y su configuración no sensible.

No contendrá el modelo, el bundle cifrado, la clave, tokens de Hugging Face,
contenido descifrado ni cachés de modelos. El bundle se descarga en tiempo de
ejecución y la clave llega exclusivamente mediante el volumen del Secret.

## Workload, estado y recursos

Se usará un `Job` porque la demostración termina al obtener y validar el
embedding. No se necesita un proceso permanente ni la semántica de un
`Deployment`.

El Job tendrá `restartPolicy: Never` y `backoffLimit: 0`. Un fallo se expone
como resultado del Job y no reutiliza estado ni reintenta automáticamente.

Los recursos iniciales serán solicitudes de `1` CPU y `1Gi` de memoria, con
límites de `2` CPU y `2Gi` de memoria. Se revisarán según las mediciones reales
de la prueba, no por anticipación.

## Volúmenes, red y limpieza

El Secret de la decisión 003 se montará solo lectura. Un `emptyDir` efímero
albergará el bundle descargado y los ficheros descifrados durante esa ejecución.
El consumer realizará limpieza lógica del directorio temporal en un bloque de
limpieza tanto en éxito como en fallo; esto no equivale a una garantía de
borrado seguro del almacenamiento subyacente.

La red se usará para descargar el bundle cifrado público. Antes de cargar el
modelo recuperado, el consumer deshabilitará la red de la librería, usará una
caché vacía por ejecución y prohibirá `trust_remote_code`. Las pruebas deberán
demostrar que ningún archivo faltante se obtiene de Internet.

## Alternativas descartadas

- **Deployment:** añade semántica de servicio y reinicios permanentes que no
  aportan a la demostración de un pipeline finito.
- **Registro de imágenes remoto:** amplía credenciales, superficie operativa y
  dependencias sin aportar valor a esta PoC local con kind.
- **Incluir el modelo o el bundle en la imagen:** ocultaría la descarga del
  artefacto cifrado y podría filtrar el modelo en claro.
- **Variables de entorno para la clave:** contradice la decisión 003 de usar
  un montaje de Secret como archivo.

## Consecuencias

No quedan decisiones importantes pendientes para Layer 1. El siguiente paso
del flujo SDD es crear un plan verificable y dividirlo en tareas antes de
implementar.
