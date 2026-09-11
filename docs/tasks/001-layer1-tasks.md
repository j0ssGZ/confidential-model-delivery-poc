# Tareas 001: Layer 1

- **Estado:** propuestas; no iniciar implementación sin aprobación del plan.
- **Plan asociado:** [`001-layer1-plan.md`](../plans/001-layer1-plan.md).

## T01 · Dependencias, estructura y pruebas base

**Resultado:** paquete Python con dependencias fijadas mediante `uv.lock`,
estructura de producer/consumer y marco de pruebas.

**Verificación:** instalación reproducible; pruebas base ejecutables; revisión
de Git confirma que no se incluyen `.venv`, secretos, modelos ni artefactos.

## T02 · Bundle v1 y extracción segura

**Resultado:** creación y lectura de `CMDP1ENC`, metadata canónica, AAD,
AES-256-GCM y TAR determinista con validación previa a extracción.

**Verificación:** round-trip exacto; rechazos de clave errónea, cabecera,
metadata, nonce, hash, ciphertext y tag alterados; rechazo de rutas peligrosas;
ningún archivo parcial queda disponible.

## T03 · Producer local

**Resultado:** descarga de MiniLM en la revisión fijada, inventario de archivos
necesarios, comprobación de carga previa y generación de bundle cifrado.

**Verificación:** el producer no deja modelo ni clave en rutas versionadas y
emite sólo bundle + metadata no sensible; el bundle se puede validar localmente.

## T04 · Consumer aislado

**Resultado:** consumer que recibe URL/revisión del bundle y ruta de clave,
descarga, valida, descifra, extrae y carga sólo desde el temporal recuperado.

**Verificación:** carga offline, caché vacía y sin código remoto; embedding de
texto fijo con shape `(1, 384)` y valores finitos; logs saneados.

## T05 · Imagen y manifiestos de Kubernetes

**Resultado:** Dockerfile de la imagen local, manifiesto de `Job`, montaje del
Secret y `emptyDir`, recursos acordados y comandos locales no versionados para
crear/actualizar el Secret.

**Verificación:** inspección de imagen confirma ausencia de modelo, bundle,
clave y token; validación de manifiestos; imagen cargable en kind.

## T06 · Publicación inmutable en Hugging Face

**Resultado:** repositorio público `j0ssGZ/confidential-model-delivery-artifacts`
con bundle y metadata permitidos; referencia por commit exacto.

**Verificación:** inspección del repositorio confirma que no hay contenido en
claro ni secretos; el token no aparece en historial, archivos ni logs.

## T07 · Recorrido positivo en kind

**Resultado:** Job ejecutado en el contexto `kind-secure-ai` con Secret
`model-decryption-key` en `secure-ai-poc` y bundle de la revisión inmutable.

**Verificación:** Job completado; logs no sensibles muestran descarga,
descifrado, carga y embedding válidos; no hay descarga del modelo original.

## T08 · Recorridos negativos integrados

**Resultado:** ejecuciones con clave incorrecta y bundle manipulado.

**Verificación:** ambos fallan con salida distinta de cero antes de cargar;
los logs no revelan secretos ni plaintext y el temporal se limpia lógicamente.

## T09 · Documentación y cierre de evidencia

**Resultado:** README y spec reflejan comandos, entradas, resultados esperados,
límites y evidencias de T01–T08.

**Verificación:** una repetición desde cero siguiendo README reproduce el caso
positivo y los dos negativos; batería de pruebas completa y `git diff --check`
sin errores.

## Orden y regla de finalización

T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 → T09. Cada tarea debe tener un
commit atómico, una comprobación proporcional y evidencia enlazable antes de
empezar la siguiente. Un fallo de verificación detiene la cadena hasta quedar
explicado y corregido.
