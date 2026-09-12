# Informe final de estudio · Layer 1

Actualización: el cierre correctivo, 36 tests y reproducción en un clúster nuevo
están en [verificación 002](002-layer1-closure-verification.md). Los 12 tests
citados más abajo son el resultado histórico inicial.

## Qué construimos

Un producer descarga `sentence-transformers/all-MiniLM-L6-v2` en una revisión
fija, lo empaqueta en un TAR determinista y lo cifra con AES-256-GCM. Publicamos
solo el bundle cifrado en Hugging Face. Un consumer corre como Job en
Kubernetes, recibe la clave desde un Secret montado como archivo, descarga por
commit inmutable, descifra, extrae de forma segura y carga MiniLM con opciones
locales y una caché temporal nueva. El Pod conserva acceso a la red.

Se entregan `Dockerfile.producer` y `Dockerfile.consumer`. La imagen Producer
ejecuta la misma CLI con modelo/clave/salida montados en runtime; no incorpora
esos datos ni publica en Hugging Face. Build, montajes y modo de descarga están
en README; evidencia del complemento en el anexo T13 del informe 002.

## Por qué esas decisiones

- AES-GCM aporta confidencialidad e integridad autenticada; la metadata forma
  parte del AAD.
- TAR determinista hace reproducible el plaintext y su hash.
- `safetensors` evita formatos de pesos basados en pickle, aunque no cifra.
- Secret como archivo reduce exposiciones accidentales y separa producer de la
  API de Kubernetes.
- Job e imagen local CPU mantienen el recorrido finito, pequeño y reproducible.

## Evidencia

- 12 pruebas locales pasan antes de Kubernetes.
- Job positivo: `Complete`, `1/1`, `model_loaded=true`, embedding `(1, 384)`.
- Clave incorrecta en Kubernetes: `bundle authentication failed`.
- Bundle manipulado dentro de Kubernetes: `bundle authentication failed`.
- Hugging Face contiene únicamente `.gitattributes` y el bundle cifrado en el
  commit `c6d037b94a2f9e1072198a9c8de94540ada55edc`.

## Qué protege y qué no

Protege los archivos de nuestro bundle frente a quien no tenga la clave.
MiniLM sigue siendo público en su repositorio original.
No protege frente a un administrador privilegiado de Kubernetes o del host,
porque Layer 1 confía en Kubernetes para entregar el Secret. Confidential
computing y attestation pertenecen a Layer 3.

## Respuesta de defensa en 30 segundos

“Fijo un modelo público y su revisión, lo empaqueto de forma reproducible y lo
cifro con AES-256-GCM. Publico solo el ciphertext. El consumer en Kubernetes
recibe la clave como Secret montado, verifica autenticidad antes de extraer,
carga únicamente los archivos recuperados con opciones locales y demuestra
un embedding de 384 dimensiones. También pruebo clave incorrecta y manipulación del bundle.
La limitación es que Kubernetes y el host siguen dentro de mi frontera de
confianza; una protección frente al host requeriría una TEE real, attestation
y una política de confianza adecuada.”
