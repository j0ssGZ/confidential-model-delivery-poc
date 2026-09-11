# Plan 001: Layer 1

- **Estado:** ejecutado T01–T08; cierre correctivo autorizado en curso.
- **Fuente de alcance:** [`001-layer1.md`](../specs/001-layer1.md).
- **Objetivo:** entregar y demostrar el recorrido reproducible de un bundle
  cifrado desde Hugging Face hasta un Job de Kubernetes que recupera MiniLM y
  genera un embedding válido.

## Principios de ejecución

El cierre sigue este orden: corregir documentación y contrato (T09), corregir
limpieza/validaciones y ampliar tests (T10), reproducir local y Kubernetes con
imagen nueva (T11), revisar historial y sincronizar informe/Notion (T12).
No incluye capas opcionales ni una nueva publicación innecesaria del bundle.

- Mantener claves, tokens, modelos descargados, bundles y directorios
  descifrados fuera de Git y de las imágenes.
- Fijar dependencias, revisión del modelo y revisión de Hugging Face antes de
  cada ejecución verificable.
- Separar pruebas locales unitarias del recorrido integrado en Kubernetes.
- Tratar cualquier fallo de autenticidad como terminal: no extraer, no cargar,
  no reintentar con estado parcial y no registrar secretos.
- Publicar únicamente el bundle cifrado y metadatos no sensibles.

## Secuencia

1. Preparar el paquete Python, dependencias bloqueadas y el esqueleto de
   pruebas. Verificar que no se introducen secretos ni rutas ignoradas bajo
   control de Git.
2. Implementar el formato de bundle v1 y utilidades de TAR determinista,
   descifrado autenticado y extracción segura. Cubrirlo con pruebas unitarias
   positivas y de manipulación.
3. Implementar el producer: descarga la revisión fijada, selecciona los
   archivos requeridos, crea el TAR, cifra y emite sólo bundle + metadata no
   sensible. Verificar la carga local del modelo original antes de cifrar.
4. Implementar el consumer para obtener el bundle, leer los 32 bytes del
   archivo de Secret, validar/descifrar/extractar y cargar exclusivamente del
   directorio recuperado. Forzar carga offline, caché vacía y
   `trust_remote_code=False`; comprobar embedding `(1, 384)` y valores finitos.
5. Implementar la imagen `cmdp-consumer:0.1.0`, manifiestos y comandos locales
   de Secret/Job. Construir para la arquitectura del clúster y cargarla en
   kind, sin incorporar modelo ni secretos.
6. Crear el repositorio acordado de Hugging Face y publicar el bundle con un
   token local de alcance mínimo. Registrar su commit exacto como referencia
   inmutable de la ejecución integrada.
7. Ejecutar el Job con la clave correcta en `kind-secure-ai`; conservar sólo
   logs no sensibles como evidencia. Confirmar limpieza lógica del temporal.
8. Ejecutar los dos recorridos negativos: clave incorrecta y bundle alterado.
   Confirmar salida no cero, ausencia de carga/extracción y ausencia de datos
   sensibles en logs.
9. Actualizar README, spec, instrucciones y evidencias para que una persona
   pueda repetir los recorridos desde cero. Ejecutar la batería completa y
   dejar los resultados trazables.

## Puntos de control

| Punto | Condición para avanzar | Evidencia |
|---|---|---|
| P1: bundle | Pruebas unitarias de cifrado, parseo y extracción segura pasan. | Salida de tests sin secretos. |
| P2: producer/consumer local | El modelo se carga desde archivos recuperados y produce `(1, 384)`. | Test o log estructurado local. |
| P3: publicación | El repositorio contiene sólo el bundle cifrado y metadatos permitidos; hay commit inmutable. | URL y SHA de Hugging Face, sin token. |
| P4: Kubernetes | El Job correcto termina y genera la evidencia funcional. | Estado del Job y logs saneados. |
| P5: fallos seguros | Clave errónea y bundle alterado abortan antes de cargar. | Códigos de salida y logs saneados. |
| P6: entrega | README reproduce P3–P5 y toda la batería pasa. | Comandos documentados y resultados. |

## Riesgos y mitigación

- **Dependencias o modelo incompatibles con ARM64:** validar la carga local
  antes de construir imagen o publicar el bundle.
- **Memoria insuficiente:** partir de los recursos acordados y registrar una
  medición antes de ajustarlos.
- **Falta de token o permisos de Hugging Face:** detener antes de publicar; no
  crear sustitutos con credenciales más amplias ni dejar tokens en archivos.
- **Conectividad del Job:** permitir sólo la descarga inicial del bundle y
  comprobar que la carga no usa red ni caché.
- **Artefactos locales persistentes:** usar rutas ignoradas y `emptyDir`; la
  limpieza es lógica y se documenta sin alegar borrado seguro.

## Mapa de aceptación

Los criterios 1–2 se cubren en las tareas T01–T03; los criterios 3–5 en
T04–T07; los criterios 6–8 en T02, T05 y T08; y el criterio 9 en T09. Ninguna
tarea se considerará completada sin la evidencia indicada.
