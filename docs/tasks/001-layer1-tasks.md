# Tareas 001: Layer 1

- **Estado:** T01–T08 con evidencia histórica; T09–T12 verificadas en informe 002.
- **Plan asociado:** [`001-layer1-plan.md`](../plans/001-layer1-plan.md).

## T01 · Dependencias, estructura y pruebas base

**Estado:** completada.

**Resultado:** paquete Python con dependencias fijadas mediante `uv.lock`,
estructura de producer/consumer y marco de pruebas.

**Verificación:** instalación reproducible; pruebas base ejecutables; revisión
de Git confirma que no se incluyen `.venv`, secretos, modelos ni artefactos.

**Evidencia:** `uv run pytest` pasó con una prueba; el comando de paquete
`uv run confidential-model-delivery-poc` respondió correctamente. El lock fija,
entre otras dependencias directas, `cryptography 46.0.7`,
`huggingface-hub 1.31.0`, `sentence-transformers 5.7.0` y `pytest 9.1.1`.

## T02 · Bundle v1 y extracción segura

**Estado:** completada.

**Resultado:** creación y lectura de `CMDP1ENC`, metadata canónica, AAD,
AES-256-GCM y TAR determinista con validación previa a extracción.

**Verificación:** round-trip exacto; rechazos de clave errónea, cabecera,
metadata, nonce, hash, ciphertext y tag alterados; rechazo de rutas peligrosas;
ningún archivo parcial queda disponible.

**Evidencia:** `uv run pytest` pasó con nueve pruebas. Cubre el recorrido
correcto, clave errónea, cabecera, modelo, revisión, hash, nonce, ciphertext y
tag alterados, además de TAR con path traversal. La extracción se materializa
desde un directorio de staging sólo tras validar todos los miembros del TAR.

## T03 · Producer local

**Estado:** completada.

**Resultado:** descarga de MiniLM en la revisión fijada, inventario de archivos
necesarios, comprobación de carga previa y generación de bundle cifrado.

**Verificación:** el producer no deja modelo ni clave en rutas versionadas y
emite sólo bundle + metadata no sensible; el bundle se puede validar localmente.

**Evidencia:** se descargaron los 13 archivos permitidos de la revisión fijada,
la carga local offline de MiniLM terminó correctamente y se generó el bundle.
Tamaños locales: modelo 87 MiB y bundle 87 MiB. SHA-256 del bundle local:
`f88c4205b748c88380da9d6e85182370649f38e740811d8d6fa93df82b5fa76b`.
La clave (`secrets/`), modelo (`models/`) y bundle (`artifacts/`) fueron
confirmados como ignorados por Git.

## T04 · Consumer aislado

**Estado:** completada.

**Resultado:** consumer que recibe URL/revisión del bundle y ruta de clave,
descarga, valida, descifra, extrae y carga sólo desde el temporal recuperado.

**Verificación:** carga offline, caché vacía y sin código remoto; embedding de
texto fijo con shape `(1, 384)` y valores finitos; logs saneados.

**Evidencia:** `uv run pytest` pasó con 12 pruebas. La ejecución real contra
el bundle local informó `model_loaded=true embedding_shape=(1, 384)` y confirmó
la retirada del directorio recuperado. El caso de clave incorrecta aborta antes
de que exista un directorio recuperado.

## T05 · Imagen y manifiestos de Kubernetes

**Estado:** completada.

**Resultado:** Dockerfile de la imagen local, manifiesto de `Job`, montaje del
Secret y `emptyDir`, recursos acordados y comandos locales no versionados para
crear/actualizar el Secret.

**Verificación:** inspección de imagen confirma ausencia de modelo, bundle,
clave y token; validación de manifiestos; imagen cargable en kind.

**Evidencia:** manifiestos validados con `kubectl apply --dry-run=client`; el
script de Secret pasó `sh -n`. Se cambió PyTorch al índice oficial CPU, retirando
las dependencias CUDA/NVIDIA del lock. Imagen local `cmdp-consumer:0.1.0`:
`sha256:9d95116793291f48f6c5398c390b79d79984952985d7af902685efa99c2ace36`,
321.9 MB, cargada en el nodo Ready de kind. No se creó ningún Secret ni Job.

## T06 · Publicación inmutable en Hugging Face

**Estado:** completada.

**Resultado:** repositorio público `j0ssGZ/confidential-model-delivery-artifacts`
con bundle y metadata permitidos; referencia por commit exacto.

**Verificación:** inspección del repositorio confirma que no hay contenido en
claro ni secretos; el token no aparece en historial, archivos ni logs.

**Evidencia:** el repositorio público `J0ssGZ/confidential-model-delivery-artifacts`
contiene únicamente `.gitattributes` y `minilm-l6-v2.bundle.enc` (91,7 MB).
La referencia inmutable fijada para el consumer es
`c6d037b94a2f9e1072198a9c8de94540ada55edc`.

## T07 · Recorrido positivo en kind

**Estado:** completada.

**Resultado:** Job ejecutado en el contexto `kind-secure-ai` con Secret
`model-decryption-key` en `secure-ai-poc` y bundle de la revisión inmutable.

**Verificación:** Job completado; logs no sensibles muestran descarga,
descifrado, carga y embedding válidos; no hay descarga del modelo original.

**Evidencia:** Job `model-consumer` completado (`1/1`) en `kind-secure-ai`.
Sus logs informan `model_loaded=true embedding_shape=(1, 384)`. La imagen se
ajustó para que `TMPDIR` y `HF_HOME` residan en `/work`, el `emptyDir` efímero,
manteniendo el root filesystem de solo lectura. Kubernetes no permite ejecutar
una comprobación dentro de un Pod ya terminado; la limpieza lógica del modelo
recuperado se realiza en el `finally` del consumer y el `emptyDir` desaparece
con el Pod.

## T08 · Recorridos negativos integrados

**Estado:** completada.

**Resultado:** ejecuciones con clave incorrecta y bundle manipulado.

**Verificación:** ambos fallan con salida distinta de cero antes de cargar;
los logs no revelan secretos ni plaintext y el temporal se limpia lógicamente.

**Evidencia:** clave incorrecta y un byte alterado dentro de un Job separado
fallaron con `bundle authentication failed` antes de cargar el modelo.

## T09 · Documentación y cierre de evidencia

**Estado:** completada tras reapertura. El cierre anterior no acreditaba
reproducción; ahora hay runbook, checkout limpio y clúster nuevo (informe 002).

**Resultado:** README y spec reflejan comandos, entradas, resultados esperados,
límites y evidencias de T01–T08.

**Verificación:** una repetición desde cero siguiendo README reproduce el caso
positivo y los dos negativos; batería de pruebas completa y `git diff --check`
sin errores.

**Evidencia:** informe de estudio en
[`docs/reports/001-layer1-final-report.md`](../reports/001-layer1-final-report.md),
12 pruebas locales pasando y documentación sincronizada.

## Cierre correctivo autorizado el 11-09-2026

- [x] T09: README reproducible, spec y decisiones coherentes con el código.
- [x] T10: temporal exclusivo, revisión/identidad validadas, errores saneados,
  formato robusto y pruebas de faltantes offline y limpieza.
- [x] T11: imagen base fijada, negativos aislados, repetición local y kind;
  conservar resultados en un informe de verificación sin secretos.
- [x] T12: revisión del historial con alcance explícito, informe final y Notion
  actualizados; commits pequeños publicados.

El ensayo personal de Jose no se marca como hecho automáticamente. Es un paso
de preparación que necesita su participación, no una tarea de implementación.

Evidencia actual: [informe 002](../reports/002-layer1-closure-verification.md).
Los resultados de 12 tests anteriores se conservan como historia. El cierre
actual tiene 36 tests, tres Jobs en clúster nuevo y revisión acotada del historial.
Pendiente adicional: contrastar el PDF original cuando Jose comparta su enlace.

## Orden y regla de finalización

T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 → T09. Cada tarea debe tener un
commit atómico, una comprobación proporcional y evidencia enlazable antes de
empezar la siguiente. Un fallo de verificación detiene la cadena hasta quedar
explicado y corregido.
