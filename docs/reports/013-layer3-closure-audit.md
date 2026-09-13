# Evidencia 013: auditoría de cierre de Layer 3

Fecha: 13-09-2026. Rama `layer3`, posterior a `c8c7e80`. Esta evidencia cubre
la auditoría técnica de L3-10; la sincronización de Notion y el tag permanecen
condicionados y no se dan por hechos en este informe.

## Verificación repetida

```sh
.venv/bin/pytest
docker build --platform linux/amd64 -f Dockerfile.consumer-attested \
  -t cmdp-consumer-attested:l3-closure .
docker run --rm --platform linux/amd64 --network none --read-only \
  --tmpfs /work:rw,nosuid,nodev,size=256m,mode=1777 \
  cmdp-consumer-attested:l3-closure --help
git diff --check
```

Resultados: **138 passed in 3.15s**. La imagen se reconstruyó desde base Python
por digest, `pyproject.toml` y `uv.lock`; la ayuda arrancó sin red y con raíz de
solo lectura. La reconstrucción local produjo el ID
`sha256:6e75d6a7911cde3f9f3a2e68bac78f3840466dc06658964db29d728af6ea6bdc`.
No sustituye la referencia inmutable utilizada en Kata, que sigue siendo
`jfanjul/confidential-model-delivery-consumer-attested@sha256:5ec1d732edfb5cb7a2efcbcdfadbba4f310759f1cd1d0ca309d64f36ce2238b6`.

## Auditoría acotada y resultados

```sh
.venv/bin/python scripts/audit_history.py \
  --key-file secrets/model-key.bin \
  --key-file secrets/reproduction-20260911.bin
.venv/bin/python scripts/audit_layer3_image.py \
  /private/tmp/cmdp-consumer-attested-l3-closure.tar \
  --known-secret secrets/model-key.bin \
  --known-secret secrets/reproduction-20260911.bin \
  --known-secret secrets/signing-private.pem
```

- Historial: 246 blobs examinados. El script señaló un blob del módulo
  `signing.py`; revisión manual saneada confirmó que es la cadena literal
  `-----BEGIN PRIVATE KEY-----` con la que el código reconoce formato PEM, no
  una privada ni ninguna de las dos AES conocidas. Las comprobaciones separadas
  de representación cruda, hexadecimal y Base64 de ambas AES no coincidieron.
- Imagen: 27.621 archivos regulares en todas las capas; **0** coincidencias de
  secretos conocidos, rutas de secretos/modelos/artefactos o cachés. Cinco
  marcadores genéricos se revisaron: validación PEM del proyecto, serialización
  SSH de `cryptography`, binarios `hf_xet`/SciPy y fixture de tests upstream de
  `transformers`. No son credenciales del operador.
- Contexto de build: `.dockerignore` excluye `.git`, `.venv`, `secrets`, `keys`,
  `models`, `artifacts`, cachés y archivos `.env`; el contexto observado fue
  16,57 kB. El Dockerfile copia solamente `pyproject.toml`, `uv.lock`, README y
  `src` antes de instalar dependencias bloqueadas.
- Manifiestos Layer 3: el Job usa `kata-qemu-coco-dev`, `automountServiceAccountToken: false`,
  raíz de solo lectura, `allowPrivilegeEscalation: false`, capabilities `ALL`
  eliminadas y no define volumen Secret, `secretKeyRef`, `--key-file` ni
  `model-decryption-key`. La pública Ed25519 llega por ConfigMap; AES llega
  únicamente por CDH en el ensayo E2E.

La auditoría es deliberadamente acotada a secretos conocidos, patrones comunes,
historial Git alcanzable e imagen construida. No demuestra que no exista ningún
secreto desconocido ni reemplaza SBOM, análisis de vulnerabilidades o revisión
de infraestructura de producción.

## Custodia y límites

No se regeneraron claves ni se alteraron la AES positiva, privada Ed25519,
bundle/firma de Hugging Face, tags `layer1-complete`/`layer2-complete` ni los
artefactos de capas previas. La AES correcta solo se introdujo temporalmente en
KBS LocalFs por el canal administrativo del laboratorio; no entra en Git,
Notion, YAML ni la imagen. La evidencia E2E está en el
[informe 012](012-layer3-e2e.md). `kata-qemu-coco-dev` sigue siendo Sample: no
se declara confidencialidad frente al host malicioso ni una TEE real.
