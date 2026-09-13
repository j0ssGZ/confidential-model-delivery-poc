# Reproducción del entregable

Ejecutar desde la raíz del checkout de entrega (o de una futura exportación).
Python 3.12 y uv 0.12.12 son la referencia. Docker solo es necesario para imágenes
y kind; Layer 3 requiere además Linux x86_64/KVM y el entorno CoCo.

## 1. Tests sin claves del autor

```sh
uv sync --locked
uv run pytest -q
uv run cmdp-producer --help
uv run cmdp-consumer --help
uv run cmdp-consumer-signed --help
uv run cmdp-consumer-attested --help
```

Resultado de cierre: 138 tests en Layer 3. La instalación descarga dependencias.
Los tests usan fixtures/temporales y no requieren claves del autor ni el servidor
CoCo. No reemplazan el E2E real registrado en los informes.

Si se clona desde GitHub, el checkout predeterminado es `main` (Layer 1).
Para revisar las tres capas, seleccionar explícitamente `layer3` o el SHA de
entrega. `layer3-complete` fija el código verificado; documentación de entrega
posterior está en el commit de entrega indicado en el resumen de publicación.

## 2. Crear una pareja propia y probar Layer 1/2 localmente

Hacerlo en la copia descomprimida/laboratorio propio. Estas órdenes generan
claves NUEVAS en rutas exclusivas, nunca para intentar abrir el bundle del autor.

```sh
umask 077
mkdir -p secrets keys models artifacts
review_keys=$(mktemp -d "$PWD/secrets/reviewer.XXXXXX")
review_public=$(mktemp -d "$PWD/keys/reviewer.XXXXXX")
review_model=$(mktemp -d "$PWD/models/reviewer.XXXXXX")
review_output=$(mktemp -d "$PWD/artifacts/reviewer.XXXXXX")

uv run python scripts/generate_key.py "$review_keys/aes.bin"
uv run python -m confidential_model_delivery_poc.signing \
  --private-key "$review_keys/signing.pem" --public-key "$review_public/public.pem"
uv run cmdp-producer --download-model --model-dir "$review_model" \
  --key-file "$review_keys/aes.bin" --signing-key-file "$review_keys/signing.pem" \
  --output "$review_output/minilm-l6-v2.bundle.enc"

uv run cmdp-consumer --bundle "$review_output/minilm-l6-v2.bundle.enc" \
  --key-file "$review_keys/aes.bin" --work-dir "$review_output/layer1-check"
uv run cmdp-consumer-signed --bundle "$review_output/minilm-l6-v2.bundle.enc" \
  --signature "$review_output/minilm-l6-v2.bundle.enc.sig" \
  --public-key "$review_public/public.pem" --key-file "$review_keys/aes.bin" \
  --work-dir "$review_output/layer2-check"
```

Esperado: Layer 1 `model_loaded=true embedding_shape=(1, 384)`; Layer 2 añade
`signature_verified=true`. Producer descarga MiniLM público de revisión fija;
los Consumers cargan el modelo recuperado localmente. La creación requiere red
y espacio para dependencias, modelo y copias temporales. Los archivos privados
permanecen bajo custodia; no publicar las carpetas de trabajo.

Estos comandos documentan la secuencia de APIs/CLI existentes. Esta preparación
de entrega no generó otra pareja ni repitió la publicación del autor.

## 3. Reproducir el bundle publicado

El repositorio no contiene AES ni pública de confianza de la demo. Para la pareja
firmada publicada se necesita:
- AES exacta correspondiente a la revisión `11eefa27b9f320b95263e1b00c09f2d2cbe36181`,
  entregada por canal privado.
- Pública Ed25519 obtenida de forma independiente/confiada. No hace falta
  entregar la privada del Producer.

No reutilizar sin comprobar la AES del bundle histórico Layer 1: las parejas
de artefacto/clave son distintas. Una firma válida con otra AES falla en GCM.

Una vez aprovisionados los archivos en las rutas de ejemplo:

```sh
uv run cmdp-consumer-signed \
  --repo-id j0ssGZ/confidential-model-delivery-artifacts \
  --revision 11eefa27b9f320b95263e1b00c09f2d2cbe36181 \
  --public-key keys/reviewer-public.pem --key-file secrets/reviewer-aes.bin \
  --work-dir artifacts/hub-review
```

Descarga anónima de artefactos públicos: puede estar limitada por disponibilidad
o rate limits. No incluir tokens en comandos registrados o entregables.

## 4. Docker y Kubernetes Layer 1/2

```sh
docker build -f Dockerfile.producer -t cmdp-producer:0.1.0 .
docker build -f Dockerfile.consumer -t cmdp-consumer:0.1.0 .
docker build --platform linux/amd64 -f Dockerfile.consumer-attested \
  -t cmdp-consumer-attested:review .
```

[README raíz](../../README.md) contiene montajes Producer/Consumer y el
[runbook Layer 2](../../k8s/layer2/README.md) separa fixtures locales y Hub.
Sustituir rutas por la pareja elegida y comprobar explícitamente el contexto
Kubernetes. Crear un clúster propio cuando se quiera reproducir desde cero.
Los scripts de provisión modifican únicamente sus recursos documentados;
no eliminar Jobs existentes sin conservar su evidencia.

Publicación: si el evaluador crea su propia pareja y quiere probar desde Hub,
debe publicar SOLO bundle cifrado y firma en su propio repositorio, registrar
la revisión de 40 caracteres y configurar la pública/AES correspondientes.
Producer no publica automáticamente.

## 5. Layer 3 con CoCo/Trustee

Entorno probado: Ubuntu Server 22.04.5 bare metal x86_64/KVM, Kubernetes 1.36.4,
containerd 2.2.1, Helm 3.18.6, Flannel 0.28.8, CoCo 0.22.0/Kata 4.0.0 y Trustee
v0.21.0 (commit compatible fijado). No extrapolarlo a kind en Mac.
Preparación y fuentes: [bootstrap](../reports/007-layer3-bootstrap.md),
[runtime](../reports/008-layer3-runtime-smoke.md) y
[runbook](../../k8s/layer3/README.md).

Orden:
1. Inspeccionar host/KVM, clúster y RuntimeClass. Reutilizar una instalación
   compatible ya funcional; diagnosticar antes de reinstalar.
2. Configurar Trustee según ADR 007 y el runbook: audience administrativa,
   política Sample allowlist y fixture sintética. Demostrar allow/deny.
3. Demostrar el proveedor CDH Python con la fixture de 32 ceros.
4. Aprovisionar por el cliente oficial la AES que corresponde al bundle firmado
   bajo `default/key/minilm-l6-v2`; token y archivo temporal privados, nunca YAML
   ni Secret AES del workload. El script administrativo se ejecuta con Python
   que tenga `cryptography` instalado y kubeconfig autorizado.
5. Aprovisionar pública Ed25519 confiada y revisión HF en ConfigMaps separados.
   Para una pareja propia, cambiar ambos y el recurso KBS de manera coherente
   en el laboratorio propio.
6. Ejecutar un Job cada vez: positivo → firma inválida → positivo → denegado →
   positivo → AES incorrecta → positivo. Usar el renderer y verificador del
   runbook, que guardan logs y códigos de salida.
7. Confirmar salida 0, cuatro etapas y embedding; en negativos salida 2 en la
   frontera esperada, junto a accesos KBS 401/200 según el caso.

La imagen publicada usada en el E2E está fijada por digest en el runbook.
Una build local solo en containerd del host no basta: el guest descarga la imagen.
Los timeouts Kata (300 s) y kubelet (10 minutos) están justificados; el script
de ajuste guarda backup y no debe aplicarse sin inspeccionar configuración.

Reboot no garantiza persistencia del recurso KBS. `emptyDir` perdió los recursos
en el ensayo: repetir sintético y reaprovisionar desde la AES original bajo
custodia antes del modelo. No regenerar claves para corregir un fallo GCM.

## 6. Evidencia y limpieza

Guardar nombre del Job, exit code, etapas, ruta/status KBS e imagen/revisión.
No volcar recursos KBS, Secrets ni tokens. Los informes versionados distinguen
tests unitarios de la ejecución real.

Los scripts no eliminan automáticamente todos los Jobs, Secrets ni archivos del
operador. La limpieza de temporales del Consumer no equivale a borrado seguro.
En el laboratorio propio, retirar solo recursos creados por la reproducción
después de guardar la evidencia; no borrar el clúster del autor.
