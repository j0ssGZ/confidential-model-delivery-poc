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

Esta fase de preparación solo modifica las exclusiones de Git y documenta
el contrato de Layer 1. No implementa el pipeline, instala dependencias,
selecciona el modelo ni fija los detalles criptográficos. Tampoco publica
artefactos del modelo.

La futura implementación incluye producer, consumer, ejecución en Kubernetes,
instrucciones reproducibles y comprobaciones del recorrido correcto y sus
fallos. Quedan fuera de Layer 1 la atestación, los entornos de ejecución
confiables, un gestor externo de claves y el endurecimiento de producción.
Un Secret proporciona la clave al proceso; por sí solo no demuestra protección
frente a un administrador del clúster ni confidencialidad durante la ejecución.

## Criterios de aceptación

1. El producer descarga un modelo pequeño desde una fuente y revisión
   identificables. Se registra qué archivos son necesarios para cargarlo,
   incluidos configuración y archivos auxiliares cuando correspondan.
2. El producer cifra esos archivos y publica en el repositorio de destino de
   Hugging Face el artefacto cifrado y únicamente los metadatos no sensibles
   acordados. No publica claves, tokens ni archivos del modelo en claro.
3. El consumer se ejecuta en el clúster previsto, descarga el artefacto
   publicado y lee la clave desde un volumen de Secret montado como solo
   lectura. La clave no se incorpora a la imagen ni a manifiestos versionados.
4. Con la clave correcta y el artefacto íntegro, el consumer recupera los
   archivos y carga el modelo exclusivamente desde el directorio descifrado.
   La carga no puede descargar el modelo original, resolver archivos faltantes
   por red ni aprovechar una copia previa en caché. La comprobación parte de
   una caché vacía y se realiza con la carga en modo local/sin red.
5. La ejecución aporta evidencia verificable de que el modelo se ha cargado;
   descargar o descifrar archivos no basta. La comprobación concreta de carga
   o inferencia mínima se definirá al elegir el modelo.
6. Una clave incorrecta provoca un fallo explícito, salida distinta de cero y
   ausencia de carga del modelo. No se continúa con archivos parcialmente
   descifrados ni se recurre al modelo original.
7. Un ciphertext manipulado provoca un fallo de autenticidad/integridad,
   salida distinta de cero y ausencia de carga. Se comprobará alterando bytes
   del artefacto válido. La validación debe completarse antes de entregar
   archivos al cargador; no basta con que este falle al interpretar los datos.
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

## Decisiones pendientes

- Modelo, licencia, tamaño, revisión exacta, librería de carga y comprobación
  mínima que evidencie su funcionamiento en ARM64.
- Esquema de cifrado con autenticidad/integridad, librería, parámetros, formato
  del artefacto y tratamiento de nonces y metadatos. Los casos negativos son
  requisitos del resultado, no una elección anticipada de algoritmo.
- Generación, formato y suministro de la clave al producer y al Secret;
  nombre del Secret, ruta de montaje y ciclo de vida local de la clave.
- Repositorio de Hugging Face de destino, visibilidad, autenticación y permisos
  mínimos; identificación de la versión exacta que consumirá Kubernetes.
- Empaquetado de los archivos, metadatos públicos permitidos y cómo comprobar
  que los archivos recuperados corresponden a los originales.
- Forma de ejecución del consumer (por ejemplo, Job), imagen, recursos,
  almacenamiento temporal y limpieza del texto claro tras éxito o fallo.
- Mecanismo para verificar la carga sin acceso a red y sin cachés previas,
  distinguiéndola de la descarga inicial del artefacto cifrado.
