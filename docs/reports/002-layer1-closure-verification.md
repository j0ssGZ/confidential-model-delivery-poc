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
