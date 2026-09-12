# Verificación de cierre correctivo · 11-09-2026

## Alcance y versiones

Código corregido en `b9c3e92`; runbook/imagen/manifiestos en `89af1e6` y soporte
de clúster aislado/auditoría en `238db8d`. Son referencias anteriores a este
informe. No se implementaron Layers 2/3 ni se volvió a publicar el bundle.

## Resultados obtenidos

- Suite local: **36 passed** (2,53 s). Incluye temporal exclusivo, preservación
  de datos anteriores, limpieza al fallar carga, identidad autenticada,
  rechazo de revisión mutable, errores de descarga saneados, metadata/TAR
  inválidos, rutas conflictivas, caché excluida y generación exclusiva de clave.
- Modelo existente pero incompleto: se instrumentaron `socket.connect`,
  `create_connection` y DNS; falla sin intentos de conexión. No es una
  NetworkPolicy ni una prueba exhaustiva de todas las rutas de las librerías.
- Descarga nueva de 13 archivos de MiniLM en `models/reproduction-20260911`,
  clave nueva y bundle local nuevo: Producer y Consumer correctos,
  `model_loaded=true embedding_shape=(1, 384)`.
- SHA-256 de ese bundle nuevo:
  `3a1c9cf19365e50e6f8f8c1e8373d51d1e5d4fd3c07a5013d83309e93d4b789b`.
  No se publica: el bundle de Hugging Face y su clave original se conservaron.
- Checkout limpio en `/private/tmp/cmdp-clean-leOU5S/repo`, clonado desde el
  commit local: `uv sync --locked` creó una nueva `.venv`; **36 passed**
  (27,81 s). El Consumer de ese entorno cargó el nuevo bundle local correcto.
  La clonación usó el repo local ya publicado, no una nueva descarga de GitHub.
- Imagen construida con base fijada por digest, `uv sync --locked --no-dev`
  y contexto Docker de 24,22 kB. Inspección en contenedor `--network none`:
  `image_payload_check=passed` (sin rutas de claves/modelos/artefactos/Git del
  proyecto ni pesos safetensors en `/app`; no es auditoría completa de capas).

## Kubernetes: repetición en dos clústeres

Se repitieron los tres Jobs en el laboratorio `kind-secure-ai`. Se creó además
`kind-secure-ai-repro` desde la imagen de nodo fijada en README, sin recursos
previos. Se cargó la imagen, se crearon namespace, ConfigMap y Secret con la
clave original, y se ejecutaron los mismos tres manifiestos.

Clúster nuevo:

```text
model-consumer            Complete  1/1  exit=0
model-consumer-wrong-key  Failed    0/1  exit=2
model-consumer-tampered   Failed    0/1  exit=2
```

Log positivo: `model_loaded=true embedding_shape=(1, 384)`.
Logs negativos: `cmdp-consumer: error: bundle authentication failed`.
El positivo tardó 15 s en el clúster nuevo (17 s en el original).
Los negativos no registran carga del modelo. No se sustituyó el Secret positivo.

Identidad de imagen Docker:
`sha256:4cc31c266d9810857327382fe3722801f1c6998955617c29e61aad66ef23fb23`.
Los tres Pods del clúster nuevo reportan el mismo imageID importado por kind:
`sha256:6e4318af1279dd288d1e9f63250d1cbf437e26b1633fa6b1bdcdc86137aa9b21`.
El identificador del índice Docker y el de la importación containerd no son
necesariamente iguales; no se presentan como hashes del mismo objeto.

Comandos: seguir README, variante `secure-ai-repro`. Las instalaciones
requirieron acceso de red fuera del sandbox; se registran los resultados tras
resolver esos permisos, no los fallos de DNS como fallos del producto.
La publicación manual no se repitió porque ya existe la referencia inmutable.

## Historial y límites

`scripts/audit_history.py --key-file secrets/model-key.bin --key-file
secrets/reproduction-20260911.bin`: **97 blobs**, dos claves conocidas,
**0 hallazgos** al commit `238db8d`. Examina bytes/hex/Base64 de las claves,
patrones de tokens HF/GitHub y cabeceras de claves privadas en referencias
locales. No demuestra ausencia de cualquier otro secreto, reflogs o ramas
no descargadas. No imprime valores sensibles.

Permanecen: confianza en host/clúster, modelo original público, metadata visible,
nonce aleatorio sin registro, procesamiento en RAM, limpieza no segura y
procedencia confiada del directorio local del Producer. La prueba de forma
del embedding no es una firma criptográfica de identidad.

## Recursos conservados y preparación humana

README, spec, decisiones, plan, tareas e informes sincronizados. Se releyeron
las dos páginas de Notion tras las correcciones: checks y flujos actualizados,
enlaces de AGENTS corregidos y subpágina de presentación conservada. Los bloques
Mermaid se revisaron en el contenido recuperado; no se afirma una comprobación
visual de su renderizado. `git diff --check` pasó antes del commit documental.
El artículo de CoCo está resumido en la página principal. Jose confirma que el
enunciado ya está recogido en la spec y que no hace falta revisar el PDF aparte.

Se conservaron los dos clústeres y los Jobs con sus logs, la clave original,
la clave nueva en `secrets/`, descargas/bundles en rutas ignoradas y el checkout
temporal con su `.venv`. El usuario puede reproducir o inspeccionar la demo.
No se hizo una eliminación general del laboratorio ni del historial.
El contexto creado por kind es `kind-secure-ai-repro`; los comandos usan contexto
explícito para evitar confusiones.

La defensa oral requiere ensayo con Jose. No se marca como terminada por estos
resultados. Las capas opcionales se deciden después, bajo SDD.

## Anexo T13 · Dockerfile Producer · 12-09-2026

Corrección literal autorizada: el entregable exige Dockerfiles de Producer y
Consumer. Se añade `Dockerfile.producer`; el Dockerfile raíz, código Python,
dependencias, claves, publicación y manifiestos Kubernetes quedan intactos.
Base de esta corrección: `5371dda` en la rama existente `layer2`. La presencia
de código previo de Layer 2 en esa rama no implica implementación adicional
en esta tarea. La etiqueta histórica `layer1-complete` no se mueve.

Misma base Python por digest, uv 0.12.12, lock y UID/GID 10001. Producer usa
`--no-cache` al instalar; `TMPDIR=/tmp` solo durante build, `/work` en runtime.
El primer build falló porque uv sin caché intentaba usar `/work` inexistente;
se corrigió ese directorio temporal de build y la repetición terminó bien.
Se mantienen COPY explícitos; `.dockerignore` y AGENTS ya cubren el proceso
y no requieren cambios. Los entornos del operador nunca se copian: `/app/.venv`
es el entorno Linux instalado desde el lock dentro de la imagen.

Comandos ejecutados desde la raíz del proyecto (operador no root):

```sh
.venv/bin/python -m pytest -q
docker build -f Dockerfile.producer -t cmdp-producer:0.1.0 .
docker run --rm --network none cmdp-producer:0.1.0 --help
docker image inspect cmdp-producer:0.1.0 --format '{{.Id}} user={{.Config.User}} entrypoint={{json .Config.Entrypoint}}'
mktemp -d /private/tmp/cmdp-producer-smoke.XXXXXX
docker run --rm --network none --read-only --user "$(id -u):$(id -g)" \
  --tmpfs /work:rw,nosuid,nodev,size=256m,mode=1777 \
  --mount "type=bind,src=$PWD/models/minilm-l6-v2,dst=/model,readonly" \
  --mount "type=bind,src=$PWD/secrets/model-key.bin,dst=/key.bin,readonly" \
  --mount type=bind,src=/private/tmp/cmdp-producer-smoke.Py7KED,dst=/output \
  cmdp-producer:0.1.0 --model-dir /model --key-file /key.bin \
  --output /output/minilm-l6-v2.bundle.enc
.venv/bin/cmdp-consumer --bundle /private/tmp/cmdp-producer-smoke.Py7KED/minilm-l6-v2.bundle.enc \
  --key-file secrets/model-key.bin --work-dir /private/tmp/cmdp-producer-smoke.Py7KED/consumer-check
docker image save -o /private/tmp/cmdp-producer-smoke.Py7KED/image.tar cmdp-producer:0.1.0
docker history --no-trunc cmdp-producer:0.1.0
.venv/bin/python /private/tmp/cmdp-producer-smoke.Py7KED/audit_layers.py
shasum -a 256 artifacts/minilm-l6-v2.bundle.enc
git diff -- Dockerfile pyproject.toml uv.lock src k8s AGENTS.md
git diff --check
```

Resultados:

- Suite existente: **84 passed in 3.34s**. No se añadieron tests de código
  porque solo se añadió empaquetado; su validación se hizo sobre la imagen real.
- Build correcto; imagen
  `sha256:dfa3372f2590e1e043faf205b5b4ab86cb41e8b7febab14ab234ed0211db1b9c`.
  CLI ayuda salida 0, incluye `--download-model`; usuario `10001:10001` y
  entrypoint `["cmdp-producer"]` comprobados.
- Smoke sin red, raíz read-only, modelo/clave read-only y salida nueva:
  `bundle_created=/output/minilm-l6-v2.bundle.enc`. Consumer carga el resultado:
  `model_loaded=true embedding_shape=(1, 384)`.
- Escáner temporal de las nueve capas exportadas y configuración/historial:
  27.779 archivos, cero rutas de datos prohibidas y cero coincidencias con
  AES conocidas y PEM privada local (bytes/hex/Base64). Sin safetensors,
  bundles ni cachés pip/uv/Hugging Face del operador. Revisión acotada, no una
  garantía de ausencia de todo secreto desconocido o vulnerabilidad.
- Bundle positivo anterior conserva SHA-256
  `f88c4205b748c88380da9d6e85182370649f38e740811d8d6fa93df82b5fa76b`,
  comprobado antes y después. Clave positiva solo montada read-only; no se
  regeneró ni escribió. Sin publicación Hub ni operaciones Kubernetes.
- Diff de código, lock, Dockerfile Consumer, k8s y AGENTS vacío.
  `git diff --check`: correcto.

El temporal de smoke y la exportación de imagen se conservan en
`/private/tmp/cmdp-producer-smoke.Py7KED`. No contienen una copia de la clave.
La descarga de red no se repitió: se conserva la CLI existente y README muestra
el montaje escribible requerido para `--download-model`. Imagen probada en
Linux ARM64; otros hosts requieren build para su arquitectura y permisos de
montaje apropiados. La publicación sigue siendo responsabilidad del operador.
Notion principal y defensa se actualizan solo en sus referencias al Dockerfile
Producer; no cambian el alcance ni las evidencias de las capas opcionales.
