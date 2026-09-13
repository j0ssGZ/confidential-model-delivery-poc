# Secure AI challenge — guía del evaluador

Implementación de Jose Fanjul: distribución cifrada y firmada de
`sentence-transformers/all-MiniLM-L6-v2`, con tres recorridos de Consumer.

## Qué se entrega

Código Python, dependencias bloqueadas, Dockerfiles de Producer y Consumer,
manifiestos Kubernetes separados, tests, specs, decisiones y evidencias.
La entrega se prepara en GitHub. Por petición del autor no se genera ZIP en
esta revisión. Si se añade más adelante, debe exportarse desde un commit Git,
sin `.git`, modelos, claves, credenciales ni artefactos locales.

- [Repositorio GitHub](https://github.com/j0ssGZ/confidential-model-delivery-poc/tree/layer3).
- Hito técnico inmutable:
  [layer3-complete](https://github.com/j0ssGZ/confidential-model-delivery-poc/tree/layer3-complete),
  commit `b0fb7b6a4073f41e9dda2329e6d4605862e4b836`.
- La revisión de entrega añade esta guía y correcciones documentales posteriores;
  no cambia código ni mueve el tag técnico. Al entregar, enlazar el commit exacto
  indicado en el resumen de publicación para evitar depender de una rama mutable.
- [Bundle y firma publicados](https://huggingface.co/J0ssGZ/confidential-model-delivery-artifacts/tree/11eefa27b9f320b95263e1b00c09f2d2cbe36181).

## Qué he construido

**Layer 1, obligatoria.** Producer valida el modelo local, crea un TAR
determinista y cifra con AES-256-GCM. El operador publica el bundle en Hugging
Face y aprovisiona la clave como Kubernetes Secret. Consumer descarga el bundle,
autentica/descifra, valida identidad y hash, extrae con controles de rutas y carga
el modelo exclusivamente desde archivos locales. Dockerfiles explícitos:
`Dockerfile.producer` y `Dockerfile.consumer`.

**Layer 2, opcional realizada.** Producer firma todos los bytes cifrados con
Ed25519. Consumer verifica con una pública aprovisionada independientemente,
antes de leer AES y descifrar. Poseer AES no concede capacidad de firma.

**Layer 3, opcional realizada.** `cmdp-consumer-attested` conserva la firma como
primer filtro y obtiene AES por CDH local → Attestation Agent/KBC → Trustee KBS
→ política. El Job final no monta AES mediante Kubernetes Secret. El recurso
de clave es `default/key/minilm-l6-v2`; se exige una respuesta de 32 bytes antes
de GCM. `Dockerfile.consumer-attested` y `k8s/layer3/` separan este recorrido.

Producer termina con el bundle local (y su firma cuando se solicita). La
publicación en Hugging Face y el aprovisionamiento de claves son operaciones
explícitas del operador. Se empleó desarrollo guiado por especificación y
asistencia de IA; requisitos, decisiones, código y resultados están disponibles
para revisión. La defensa personal del candidato no se presenta como ya ensayada.

## Evidencia y alcance

- Layer 1 corregida: 36 tests y positivo/negativos en kind.
- Layer 2: 84 tests, cinco Jobs con fixtures y cinco desde Hub; positivo 0,
  tres rechazos en firma y uno en GCM, todos con salida 2.
- Layer 3: suite completa de 138 tests. Positivo real en Kata: firma válida,
  AES recuperada por CDH/KBS 200, GCM válido y
  `signature_verified=true key_retrieved=true model_loaded=true embedding_shape=(1, 384)`,
  salida 0.
- Negativos Layer 3: firma manipulada antes de CDH; recurso denegado KBS 401
  antes de GCM; clave de prueba incorrecta obtenida con KBS 200 y rechazada
  por GCM antes de extracción/carga. Se repitió positivo tras cada negativo.
- Escaneos acotados de historial e imágenes: resultados y falsos positivos
  revisados se explican en el informe 013. No es una certificación de seguridad.

Evidencias: [Layer 1](../reports/002-layer1-closure-verification.md),
[Layer 2](../reports/006-layer2-hub-closure.md),
[Layer 3 E2E](../reports/012-layer3-e2e.md),
[auditoría](../reports/013-layer3-closure-audit.md).
Los informes son snapshots históricos; su fecha y checkpoint delimitan sus afirmaciones.

## Reproducir y revisar

Empezar por [REPRODUCTION.md](REPRODUCTION.md). Distingue tests sin credenciales,
modelo propio con claves nuevas y reproducción de la pareja publicada. El
recorrido Kubernetes/CoCo necesita su entorno y aprovisionamiento; descomprimir
el repositorio no los crea automáticamente.

Para revisar código: `producer.py` → `bundle.py` → `signed_consumer.py` →
`attested_consumer.py`/`cdh.py` bajo `src/confidential_model_delivery_poc/`.
Los tests instrumentan el orden crítico; la evidencia E2E usa el servidor real.

## Límites de seguridad

`kata-qemu-coco-dev` usa evidencia Sample. Demuestra arquitectura, protocolo
y liberación según política; no una TEE real ni confidencialidad frente a un
host malicioso. La allowlist limita rutas y Sample, no identifica de forma
exclusiva nuestro código. Host, operador, pública de firma y administración de
Trustee siguen siendo de confianza.

Trustee usa HTTP interno, identidades demo y LocalFs sobre `emptyDir`. Tras
reboot se comprobó recuperación de servicios y pérdida de recursos KBS, que
necesitaron reaprovisionamiento. TLS de producción, persistencia durable,
rotación y anti-rollback quedan fuera del alcance.

MiniLM es público en origen. Se cifra nuestra copia para demostrar el
mecanismo. La API GCM procesa el bundle completo en RAM; es una decisión de
PoC para un modelo pequeño. La carga usa `local_files_only=True` y
`trust_remote_code=False`; esto no equivale a bloquear la red del Pod.

## Material para enviar

Enlace a la revisión exacta de GitHub + [mensaje de entrega](MESSAGE.md).
ZIP aplazado por petición del autor; el vídeo se omite. Notion es material complementario de estudio y no una
dependencia de acceso para el evaluador. No se ha identificado un canal/formato
obligatorio en el material disponible: usar el canal del contacto del challenge.
