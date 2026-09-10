# Layer 1: entrega de un modelo cifrado

Estado: especificación inicial; implementación pendiente.

Esta spec se gestiona bajo el ciclo Specification-Driven Development definido
en [`AGENTS.md`](../../AGENTS.md). Mientras queden decisiones importantes en
la sección correspondiente, la implementación de Layer 1 está bloqueada.

## Objetivo y alcance

Demostrar un recorrido reproducible en el que un producer descarga un modelo
pequeño de Hugging Face, cifra los archivos necesarios para cargarlo y publica
el artefacto cifrado en Hugging Face. Un consumer ejecutado en Kubernetes
descarga ese artefacto, monta la clave desde un Secret, descifra los archivos
y carga el modelo recuperado.

El entorno de partida comunicado es macOS Apple Silicon ARM64, Python 3.12.14,
uv 0.12.12, Docker y kind 0.33.0, con Kubernetes 1.36.4 en el clúster
`secure-ai`, contexto `kind-secure-ai` y nodo Ready. Esta especificación no
constituye una nueva validación del entorno.

Esta fase de preparación documenta el contrato y las decisiones cerradas de
Layer 1. No implementa el pipeline, no instala dependencias ni publica
artefactos del modelo.

La futura implementación incluye producer, consumer, ejecución en Kubernetes,
instrucciones reproducibles y comprobaciones del recorrido correcto y sus
fallos. Quedan fuera de Layer 1 la atestación, los entornos de ejecución
confiables, un gestor externo de claves y el endurecimiento de producción.
Un Secret proporciona la clave al proceso; por sí solo no demuestra protección
frente a un administrador del clúster ni confidencialidad durante la ejecución.

## Criterios de aceptación

1. El producer descarga `sentence-transformers/all-MiniLM-L6-v2` en la revisión
   fija `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, con preferencia por los
   pesos `model.safetensors`. Se registra qué archivos son necesarios para
   cargarlo, incluidos configuración y archivos auxiliares cuando correspondan.
2. El producer empaqueta los archivos en un TAR determinista sin compresión y
   cifra el resultado con AES-256-GCM. Publica el bundle autocontenido
   `minilm-l6-v2.bundle.enc` y únicamente metadatos no sensibles acordados.
   No publica claves, tokens ni archivos del modelo en claro.
3. El consumer se ejecuta en el clúster previsto, descarga el artefacto
   publicado y lee la clave desde un volumen de Secret montado como solo
   lectura. La clave no se incorpora a la imagen ni a manifiestos versionados.
4. Con la clave correcta y el artefacto íntegro, el consumer recupera los
   archivos y carga el modelo con `sentence-transformers` exclusivamente desde
   el directorio descifrado. La carga no puede descargar el modelo original,
   resolver archivos faltantes por red ni aprovechar una copia previa en caché;
   debe ejecutarse sin red y sin `trust_remote_code`.
5. La ejecución genera un embedding para un texto fijo y comprueba que su shape
   es `(1, 384)` y que todos sus valores son finitos. Descargar o descifrar
   archivos no basta como evidencia de carga funcional.
6. Una clave incorrecta provoca un fallo explícito, salida distinta de cero y
   ausencia de carga del modelo. No se continúa con archivos parcialmente
   descifrados ni se recurre al modelo original.
7. Manipular la cabecera, metadata, nonce, modelo, revisión, hash, ciphertext
   o tag provoca el rechazo del bundle, salida distinta de cero y ausencia de
   carga. La validación de autenticidad/integridad debe completarse antes de
   extraer o entregar archivos al cargador; no basta con que este falle al
   interpretar los datos.
8. Los errores no exponen claves, tokens ni contenido descifrado en los logs.
   Los archivos parciales de un intento fallido no quedan disponibles para
   una carga posterior; su retirada se documentará sin prometer borrado seguro.
9. Las instrucciones permiten repetir el recorrido y los dos casos negativos,
   indicando entradas, comandos, resultados esperados y evidencias. `uv.lock`
   se conserva como archivo versionable para reproducir las dependencias.

## Convenciones locales y motivo de las exclusiones

- `.venv/`, `venv/` y `env/`: entornos regenerables, ajenos al código entregable.
- `.env` y sus variantes: valores locales potencialmente sensibles. Se permiten
  `.env.example` y `.env.*.example` con placeholders, nunca credenciales reales.
- `secrets/`, `keys/`, `.credentials/`, `.huggingface/` y `.kube/` en la raíz:
  ubicaciones reservadas para secretos, claves y configuración local sensible.
  Los manifiestos con valores reales deben ir en `secrets/` o usar el sufijo
  `.local.secret.yaml` / `.local.secret.yml`.
- `artifacts/`, `models/` y `.cache/` en la raíz: descargas, artefactos cifrados,
  archivos descifrados y cachés locales regenerables.
- Las exclusiones existentes de compilación se conservan y se añaden cachés
  de herramientas. No se ignoran globalmente JSON, YAML, binarios o archivos
  de bloqueo: configuración, manifiestos y pequeñas fixtures pueden ser parte
  de la entrega. `uv.lock` permanece explícitamente permitido.

Estas reglas son convenciones de ubicación, no detección automática de secretos.
Antes de versionar habrá que revisar el contenido; `.gitignore` no protege
archivos ya seguidos por Git ni credenciales guardadas fuera de estas rutas.

## Decisiones cerradas

### Selección del modelo

- **Modelo:** `sentence-transformers/all-MiniLM-L6-v2`.
- **Revisión:** `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
- **Licencia:** Apache-2.0.
- **Arquitectura:** BERT encoder.
- **Parámetros:** aproximadamente 22,7 millones.
- **Formato de pesos preferido:** `model.safetensors`.
- **Librería de carga:** `sentence-transformers`.
- **Verificación funcional:** generar un embedding para un texto fijo,
  comprobar shape `(1, 384)` y que todos sus valores sean finitos.
- **Restricción del consumer:** cargar únicamente desde el directorio
  descifrado, sin red, sin caché previa y sin `trust_remote_code`.

La justificación y las alternativas descartadas quedan registradas en
[`docs/decisions/001-model-selection.md`](../decisions/001-model-selection.md).

### Cifrado y formato del bundle

- **Cifrado:** AES-256-GCM de `cryptography`, con clave aleatoria de 32 bytes,
  nonce aleatorio de 12 bytes y tag de autenticación de 16 bytes. Nunca se
  reutiliza una combinación de clave y nonce.
- **Empaquetado:** TAR determinista sin compresión, con archivos ordenados,
  timestamps, UID y GID normalizados y rutas relativas. Se rechazan rutas
  absolutas, path traversal, dispositivos y enlaces; se valida la extracción
  antes de escribir archivos.
- **Nombre previsto:** `minilm-l6-v2.bundle.enc`.
- **Formato binario v1:** magic ASCII `CMDP1ENC` (8 bytes), longitud de metadata
  como `uint32` big-endian, metadata JSON canónica UTF-8 y ciphertext seguido
  del tag de AES-GCM.
- **Metadata:** `schema_version`, `algorithm`, `source_model`,
  `source_revision`, `payload_format`, `plaintext_sha256` y `nonce_b64`.
  Se serializa con claves ordenadas, separadores compactos y sin timestamps ni
  campos variables innecesarios.
- **AAD:** magic, longitud codificada y bytes exactos de la metadata.
- **Limitación aceptada:** AESGCM procesa el TAR completo en memoria. Es
  aceptable para MiniLM y esta PoC; los modelos grandes requerirían cifrado
  autenticado por bloques o streaming con nonces derivados de forma segura y
  autenticación por bloque.

La decisión completa, sus alternativas y consecuencias quedan registradas en
[`docs/decisions/002-encryption-and-bundle-format.md`](../decisions/002-encryption-and-bundle-format.md).

## Decisiones pendientes

- Generación, formato y suministro de la clave al producer y al Secret;
  nombre del Secret, ruta de montaje y ciclo de vida local de la clave.
- Repositorio de Hugging Face de destino, visibilidad, autenticación y permisos
  mínimos; identificación de la versión exacta que consumirá Kubernetes.
- Forma de ejecución del consumer (por ejemplo, Job), imagen, recursos,
  almacenamiento temporal y limpieza del texto claro tras éxito o fallo.
- Mecanismo para verificar la carga sin acceso a red y sin cachés previas,
  distinguiéndola de la descarga inicial del artefacto cifrado.
