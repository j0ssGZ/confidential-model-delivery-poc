# Layer 1: entrega de un modelo cifrado

Estado: implementación aprobada; T01–T06 completadas, T07 pendiente.

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

### Ciclo de vida y entrega de la clave

- **Generación:** el producer genera una clave cruda aleatoria de 32 bytes y
  la conserva localmente en `secrets/model-key.bin`, con permisos `0600`.
- **Control de versiones:** esa ruta está ignorada por Git. La clave no se
  incorpora a imágenes, manifiestos versionados, variables de entorno ni logs.
- **Separación de responsabilidades:** el producer recibe la ruta de la clave
  como parámetro y no necesita acceso a la API de Kubernetes.
- **Secret:** una operación local de despliegue crea o actualiza el Secret
  `model-decryption-key` en el namespace `secure-ai-poc`, con una entrada
  llamada `key`.
- **Montaje:** el consumer recibe el Secret como un archivo de solo lectura en
  `/var/run/secrets/model-delivery/key` y lee de él los 32 bytes de clave.
- **Rotación:** rotar la clave exige cifrar y publicar de nuevo el bundle y
  actualizar el Secret; una clave nueva no descifra un bundle anterior.

Kubernetes forma parte explícita de la frontera de confianza de Layer 1:
entrega la clave al workload, pero esta decisión no pretende protegerla frente
a un administrador privilegiado del clúster o del host.

La justificación, alternativas y consecuencias quedan registradas en
[`docs/decisions/003-key-lifecycle-and-secret-delivery.md`](../decisions/003-key-lifecycle-and-secret-delivery.md).

### Publicación en Hugging Face

- **Repositorio:** `j0ssGZ/confidential-model-delivery-artifacts`.
- **Visibilidad:** público y dedicado únicamente a artefactos cifrados de la
  PoC. La confidencialidad del modelo depende de AES-256-GCM y de la clave, no
  de ocultar el repositorio.
- **Contenido permitido:** el bundle `minilm-l6-v2.bundle.enc` y metadatos no
  sensibles necesarios para identificarlo. Quedan prohibidos claves, tokens,
  modelos en claro y datos descifrados.
- **Autenticación:** el producer usará un token local de Hugging Face con el
  alcance mínimo de escritura necesario para ese repositorio. No se guardará
  en Git, imágenes ni manifiestos versionados.
- **Referencia del consumer:** tras publicar, se registrará el commit exacto
  del repositorio y el consumer descargará esa revisión inmutable; no usará
  `main` ni etiquetas mutables como `latest`.

La creación del repositorio y la publicación se harán durante la
implementación aprobada, una vez cerradas todas las decisiones bloqueantes.
La justificación, alternativas y consecuencias quedan registradas en
[`docs/decisions/004-hugging-face-publication.md`](../decisions/004-hugging-face-publication.md).

### Ejecución del consumer en Kubernetes

- **Workload:** un `Job` de ejecución única. Demuestra el recorrido finito de
  descarga, descifrado, carga y verificación funcional; no se necesita un
  `Deployment` de servicio permanente.
- **Imagen:** `cmdp-consumer:0.1.0`, construida localmente desde el repositorio
  para la arquitectura del clúster y cargada directamente en kind. Contendrá
  una base Linux/Python, dependencias fijadas y el código del consumer; no
  contendrá el modelo, bundle cifrado, clave, token ni contenido descifrado.
- **Repetición de fallos:** `restartPolicy: Never` y `backoffLimit: 0`, para
  que cada fallo quede visible sin reutilizar estado ni encadenar reintentos.
- **Volúmenes:** la clave se monta solo lectura conforme a la decisión 003; un
  `emptyDir` efímero guarda el bundle descargado y los archivos de trabajo
  descifrados durante la ejecución.
- **Recursos iniciales:** solicitud de `1` CPU y `1Gi` de memoria; límites de
  `2` CPU y `2Gi` de memoria. Se ajustarán únicamente si la evidencia de
  ejecución lo justifica.
- **Limpieza:** el consumer elimina lógicamente su directorio temporal en un
  bloque de limpieza tras éxito o fallo. No se promete borrado seguro del
  almacenamiento subyacente.
- **Red:** se permite únicamente descargar el bundle cifrado público. Después,
  la carga del modelo se fuerza sin red, sin caché y sin `trust_remote_code`.

La justificación, alternativas y consecuencias quedan registradas en
[`docs/decisions/005-consumer-kubernetes-execution.md`](../decisions/005-consumer-kubernetes-execution.md).

## Decisiones pendientes

No hay decisiones importantes pendientes. La carga aislada se realizará en el
mismo proceso después de descargar el bundle cifrado: se deshabilita la red de
la librería de carga, se usa un directorio de caché vacío por ejecución y se
prohíbe `trust_remote_code`. Las pruebas demostrarán que faltantes locales no
se resuelven desde Internet.

## Plan y tareas

El diseño de ejecución y las comprobaciones previstas están en
[`docs/plans/001-layer1-plan.md`](../plans/001-layer1-plan.md). La división
concreta, orden y evidencia por tarea están en
[`docs/tasks/001-layer1-tasks.md`](../tasks/001-layer1-tasks.md).

La implementación permanece pendiente de aprobación explícita del plan y las
tareas. Las tareas que creen recursos externos, como el repositorio de Hugging
Face o el Secret de Kubernetes, se ejecutarán solo dentro de la fase de
implementación aprobada y sin versionar secretos.
