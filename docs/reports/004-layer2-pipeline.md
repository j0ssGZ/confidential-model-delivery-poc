# Evidencia L2-04: pipeline firmado local

Actualización: publicación y Kubernetes desde Hub cerrados en el
[informe 006](006-layer2-hub-closure.md). Lo siguiente conserva el checkpoint local.

11-09-2026, rama `layer2`, base L2-03 `f11ccc3`.

- Suite: **73 passed in 3.02s**, incluidos los tests anteriores.
- `uv sync --locked` instala el entrypoint nuevo sin cambiar dependencias.
- Generación operativa de PEM en `secrets/signing-private.pem` y
  `keys/signing-public.pem`, excluidos de Git.
- Producer: modelo local previamente descargado en
  `models/reproduction-20260911`, AES de esa reproducción y salida nueva
  `artifacts/layer2/minilm-l6-v2.bundle.enc` más `.sig`.
- Consumer firmado real: `signature_verified=true model_loaded=true
  embedding_shape=(1, 384)`.

Los tests instrumentan descifrado/extracción/carga: nunca se invocan tras firma
inválida. Sustituir el archivo después de verificar no altera los bytes
entregados al descifrado. Firma válida con AES incorrecta llega a GCM y falla.
Las descargas usan una misma revisión inmutable para bundle y firma.
Producer preserva salidas existentes y no publica salidas si falla la firma.

Flujo: `producer.produce` → modelo local → cifrado → firma → salidas nuevas.
`signed_consumer.main` → descarga o archivos locales → `consume_signed_bundle`
→ `verify_bundle` → `consume_bundle_bytes` → GCM → extracción → embedding.
Layer 1 sigue usando `consume_bundle`, que delega sobre bytes al mismo núcleo.

No hay todavía evidencia de publicación firmada o Kubernetes. La biblioteca
Hub no tiene token configurado; se comprobará la sesión de navegador existente.
La publicación original y los recursos de Layer 1 se conservaron.
