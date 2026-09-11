# Evidencia L2-03: módulo Ed25519

Fecha: 11-09-2026. Rama `layer2`, base documental `ad07a2a`.

`python -m pytest -q` desde `.venv`: **56 passed in 5.86s**, incluidos los
36 tests previos de Layer 1 y 20 nuevos. Biblioteca instalada: cryptography
46.0.7. `git diff --check` correcto. No se cambiaron dependencias.

## Funciones

- `generate_signing_keys`: genera un par PEM Ed25519 en rutas nuevas con
  permisos 0600; ante error de E/S retira los archivos que acaba de crear.
- `load_private_key` / `load_public_key`: cargan PEM, exigen Ed25519 y
  convierten errores de lectura/formato en mensajes controlados.
- `sign_bundle`: firma los bytes recibidos; el llamador debe asegurar origen.
- `verify_bundle`: exige firma de 64 bytes y verifica los bytes exactos.
- `main`: CLI de generación, sin imprimir material criptográfico.

Generación operativa disponible (usar rutas nuevas):

```sh
uv run python -m confidential_model_delivery_poc.signing \
  --private-key secrets/signing-private.pem \
  --public-key keys/signing-public.pem
```

Esperado: `signing_keys_created=true`. No se ha generado aún la pareja real
del laboratorio; los tests usaron claves efímeras en temporales.

## Cobertura y límites

Round-trip, permisos de privada, firma/bundle cambiados, pública incorrecta,
longitudes de firma inválidas, PEM ausente/malformado, algoritmo incorrecto,
privada cifrada no admitida, archivos existentes, rutas iguales, symlink,
fallo al crear segunda ruta y salida CLI sin material privado.

La creación del par no es transacción atómica frente a interrupción del proceso:
puede quedar un par incompleto. Revisar las rutas y no sobrescribir al reintentar.
Permisos locales no protegen contra el administrador del host. Los directorios
de salida se consideran controlados por el operador.

La verificación previa al descifrado aún no está integrada: no se atribuyen a
esta prueba garantías del pipeline firmado, publicación Hub ni Kubernetes.
README/spec/plan/tareas y Notion Layer 2 se sincronizan con este avance. Las
evidencias y la página de defensa de Layer 1 conservan su alcance anterior.
