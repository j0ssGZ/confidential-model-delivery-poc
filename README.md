# Confidential Model Delivery PoC

Challenge de Capacity Secure AI. El repositorio sigue Specification-Driven
Development; las reglas están en [`AGENTS.md`](AGENTS.md).

**Para evaluar la entrega:** consulta la
[guía de reproducción](docs/delivery/REPRODUCTION.md). La entrega está preparada
en GitHub con documentación de las tres capas; no incluye claves, modelos ni
credenciales. El código verificado está fijado en `layer3-complete` (`b0fb7b6`);
`main` conserva Layer 1 canónica.

## Estado

Layer 3 tiene runtime CoCo, Trustee y el recorrido end-to-end comprobados en la rama `layer3`:
[spec](docs/specs/003-layer3.md), [decisiones cerradas para PoC](docs/decisions/007-layer3-attestation.md),
[plan](docs/plans/003-layer3-plan.md) y [tareas](docs/tasks/003-layer3-tasks.md).
Parte de `layer2-complete`, conserva la firma y sustituye la entrega directa
de la AES al workload por CDH + Trustee KBS. El Consumer verifica primero la
firma Ed25519 del bundle de Hugging Face, después recupera la AES por CDH y solo
entonces autentica, extrae y carga MiniLM. D3/D4 están cerradas con audience y
política Sample acotada comprobadas.
`kata-qemu-coco-dev` permite ensayar ese protocolo sin proporcionar
confidencialidad respaldada por una TEE real. Trustee v0.21.0 está fijado al
commit declarado compatible con CoCo 0.22.0. Tras el reboot del host, el
recurso efímero se reaplicó de forma controlada y la AES ya asociada al bundle
firmado se registró temporalmente en KBS bajo `default/key/minilm-l6-v2`, sin
Kubernetes Secret, YAML, imagen ni Git. El positivo termina con
`signature_verified=true key_retrieved=true model_loaded=true
embedding_shape=(1, 384)` y salida 0. Los negativos reales prueban firma
inválida antes de CDH, KBS 401 antes de GCM y AES de prueba errónea rechazada por
GCM; se repitió el positivo tras cada uno. Imagen AMD64 por digest y manifiestos
separados comprobados; la suite final vuelve a pasar con 138 tests. La auditoría
acotada de historial e imagen no encontró claves conocidas, modelos ni artefactos
en las capas; sus marcadores genéricos fueron revisados. No se afirma
protección frente a un host malicioso: `kata-qemu-coco-dev` usa evidencia Sample,
no una TEE real. Notion principal, Layer 3 y presentación fueron releídos y
sincronizados; el tag anotado `layer3-complete` fue publicado en `b0fb7b6`.
[Evidencia CDH 011](docs/reports/011-layer3-cdh-image.md),
[E2E 012](docs/reports/012-layer3-e2e.md) y
[auditoría 013](docs/reports/013-layer3-closure-audit.md).

Bootstrap del laboratorio del 13-09-2026: `secure-ai-node` ejecuta Ubuntu
22.04.5 x86_64, Kubernetes 1.36.4 sobre containerd 2.2.1, Helm 3.18.6 y
Flannel 0.28.8. CoCo chart 0.22.0 terminó de instalar Kata 4.0.0; nodo `Ready`
y DaemonSet `1/1 Running`. Un Pod mínimo con `kata-qemu-coco-dev`, UID 10001 y
BusyBox fijado por digest terminó con salida 0 y `kata_smoke_ok=true`. Kernel
guest 6.18.35 frente a host 5.15.0-191-generic. El reinicio se validó después:
servicios recuperados y recursos KBS efímeros reaprovistos. [Runbook](k8s/layer3/README.md),
[bootstrap 007](docs/reports/007-layer3-bootstrap.md) y
[evidencia del runtime 008](docs/reports/008-layer3-runtime-smoke.md) y
[Trustee sintético 009](docs/reports/009-layer3-trustee-synthetic.md).

Layer 2 completada y verificada en la rama `layer2` y fijada por el tag anotado
`layer2-complete` en `e9234b9`: [spec](docs/specs/002-layer2.md),
[plan](docs/plans/002-layer2-plan.md) y [tareas](docs/tasks/002-layer2-tasks.md).
Firma, Producer/Consumer firmado, Kubernetes con fixtures locales y descarga
desde una revisión inmutable de Hugging Face están verificados. El positivo
carga el modelo; los cuatro negativos fallan con salida 2 según su frontera.
[Runbook Kubernetes Layer 2](k8s/layer2/README.md) y
[cierre Hub 006](docs/reports/006-layer2-hub-closure.md).
Justificación: [firma y confianza de la clave pública](docs/decisions/006-layer2-signing-trust.md).
Cada sección identifica la capa y sus recursos. Las etiquetas `layer1-complete`
y `layer2-complete` conservan los hitos; `main` es la Layer 1 canónica.

Layer 1 implementada y verificada, incluido el cierre correctivo T09–T12.
La especificación, el alcance, los criterios
de aceptación, las amenazas y las decisiones quedan en
[`docs/specs/001-layer1.md`](docs/specs/001-layer1.md); el plan está en
[`docs/plans/001-layer1-plan.md`](docs/plans/001-layer1-plan.md) y el progreso
de tareas en [`docs/tasks/001-layer1-tasks.md`](docs/tasks/001-layer1-tasks.md).
T01 (fundación Python), T02 (bundle v1 y extracción segura) y T03 (producer
local), T04 (consumer aislado) y T05 (imagen y manifiestos de Kubernetes) están
completas; T06 (publicación inmutable en Hugging Face) también está completa y
T07 (recorrido positivo en kind) y T08 (recorridos negativos integrados) tienen
evidencia histórica. T09 se reabrió y completó con reproducción en un clúster
nuevo y 36 tests. La evidencia actual está en
[`verificación 002`](docs/reports/002-layer1-closure-verification.md).
El informe de estudio está en
[`docs/reports/001-layer1-final-report.md`](docs/reports/001-layer1-final-report.md).

El bundle cifrado está publicado y funcionó en Kubernetes. `uv.lock` se
mantiene bajo control de Git para reproducibilidad; los entornos, secretos,
claves, cachés y artefactos locales se excluyen mediante `.gitignore`.

## Preparación desde cero

Requisitos: Python 3.12, uv, Docker iniciado, kind y kubectl; CPU, sin GPU.
Referencia: Mac ARM64, uv 0.12.12, kind 0.33.0 y Kubernetes 1.36.4.
Todos los comandos siguientes se ejecutan desde la raíz del repositorio.

```sh
git clone https://github.com/j0ssGZ/confidential-model-delivery-poc.git
cd confidential-model-delivery-poc
git switch layer3
uv sync --locked
uv run pytest -q
```

## Layer 2: recorrido firmado local y publicado

Disponible en la rama `layer2`. Generar una pareja NUEVA una sola vez:

```sh
uv run python -m confidential_model_delivery_poc.signing \
  --private-key secrets/signing-private.pem --public-key keys/signing-public.pem
uv run cmdp-producer --model-dir models/minilm-l6-v2 \
  --key-file secrets/model-key.bin --signing-key-file secrets/signing-private.pem \
  --output artifacts/signed-demo/minilm-l6-v2.bundle.enc
uv run cmdp-consumer-signed --bundle artifacts/signed-demo/minilm-l6-v2.bundle.enc \
  --signature artifacts/signed-demo/minilm-l6-v2.bundle.enc.sig \
  --public-key keys/signing-public.pem --key-file secrets/model-key.bin \
  --work-dir artifacts/signed-demo/check
```

Preparar antes el modelo y la clave AES siguiendo Layer 1. Si las claves de
firma ya existen, omitir generación. Producer firmado exige rutas de salida
nuevas y produce bundle más `.sig`; errores normales retiran salidas propias.
Una interrupción puede dejar un par incompleto: revisar, no sobrescribir.
Publicar SOLO bundle y firma en un commit nuevo; la privada permanece local.
CLI firmada exige la firma y pública; no hay fallback sin firma. Para descarga
se omiten `--bundle`/`--signature` y se pasan `--repo-id` y `--revision` completa.
Salida correcta: `signature_verified=true model_loaded=true embedding_shape=(1, 384)`.
Un fallo de firma ocurre antes de leer la AES o descifrar. Verificación y
descifrado consumen la misma instantánea de bytes.

La pareja comprobada está publicada en el
[commit inmutable de Hugging Face](https://huggingface.co/J0ssGZ/confidential-model-delivery-artifacts/tree/11eefa27b9f320b95263e1b00c09f2d2cbe36181)
`11eefa27b9f320b95263e1b00c09f2d2cbe36181`. El operador publicó únicamente
el bundle cifrado y su firma; la privada Ed25519 y la AES permanecen fuera.
Los cinco Jobs Hub y sus resultados están en el
[runbook](k8s/layer2/README.md).

## Claves y Producer: crear un bundle nuevo

El operador genera la clave; Producer solo la lee. El script siguiente crea
un archivo NUEVO de 32 bytes con permisos 0600 y rechaza sobrescrituras.

```sh
uv run python scripts/generate_key.py secrets/new-model-key.bin
uv run cmdp-producer --download-model --model-dir models/reproduction \
  --key-file secrets/new-model-key.bin --output artifacts/new/minilm-l6-v2.bundle.enc
uv run cmdp-consumer --bundle artifacts/new/minilm-l6-v2.bundle.enc \
  --key-file secrets/new-model-key.bin --work-dir artifacts/local-check
```

Esperado: `bundle_created=...` y `model_loaded=true embedding_shape=(1, 384)`.
La carga verifica que todos los valores sean finitos. Sin `--download-model`,
se usan archivos locales de confianza; la metadata no certifica su procedencia.

## Dockerfiles de Producer y Consumer (Layer 1)

El entregable incluye ambos workloads: `Dockerfile.producer` tiene entrypoint
`cmdp-producer`; `Dockerfile.consumer` tiene `cmdp-consumer`. Ambos usan
Python por digest, uv 0.12.12, `pyproject.toml` + `uv.lock` y UID/GID 10001.
Solo se copian manifiestos del paquete, README y código; modelos, claves,
credenciales y artefactos se proporcionan en runtime. Los builds no conservan
caché de pip/uv.

Desde la raíz, con modelo y clave AES ya existentes, crear una salida nueva:

```sh
docker build -f Dockerfile.producer -t cmdp-producer:0.1.0 .
docker run --rm --network none cmdp-producer:0.1.0 --help
mkdir -p artifacts
producer_output=$(mktemp -d "$PWD/artifacts/producer-docker.XXXXXX")
docker run --rm --network none --read-only \
  --user "$(id -u):$(id -g)" \
  --tmpfs /work:rw,nosuid,nodev,size=256m,mode=1777 \
  --mount "type=bind,src=$PWD/models/minilm-l6-v2,dst=/model,readonly" \
  --mount "type=bind,src=$PWD/secrets/model-key.bin,dst=/key.bin,readonly" \
  --mount "type=bind,src=$producer_output,dst=/output" \
  cmdp-producer:0.1.0 --model-dir /model --key-file /key.bin \
  --output /output/minilm-l6-v2.bundle.enc
```

El operador debe ser un usuario no root con permiso para leer modelo/clave y
escribir la salida. `--user` adapta los permisos de bind mounts en Linux sin
relajar el 0600 de la clave; por defecto la imagen usa 10001. `/work` es temporal
y escribible, mientras modelo/clave y raíz del contenedor son de solo lectura.
Esperado: `bundle_created=/output/minilm-l6-v2.bundle.enc`; el archivo queda en
`$producer_output`. No cambiar la clave de la demo ni reutilizar su ruta de salida.

Para descargar el modelo público en runtime, crear un directorio vacío y
montarlo escribible; habilitar la red omitiendo `--network none`:

```sh
mkdir -p models
producer_model=$(mktemp -d "$PWD/models/producer-download.XXXXXX")
producer_output=$(mktemp -d "$PWD/artifacts/producer-download.XXXXXX")
docker run --rm --read-only --user "$(id -u):$(id -g)" \
  --tmpfs /work:rw,nosuid,nodev,size=256m,mode=1777 \
  --mount "type=bind,src=$producer_model,dst=/model" \
  --mount "type=bind,src=$PWD/secrets/model-key.bin,dst=/key.bin,readonly" \
  --mount "type=bind,src=$producer_output,dst=/output" \
  cmdp-producer:0.1.0 --download-model --model-dir /model \
  --key-file /key.bin --output /output/minilm-l6-v2.bundle.enc
```

Se conserva la revisión MiniLM fijada por la CLI. No hacen falta credenciales
para ese modelo público. Las descargas y su caché auxiliar permanecen en el
directorio montado, no en la imagen. El operador publica el bundle por separado
como se describe abajo. No se añade un Job Producer ni se cambia el Job Consumer.

## Publicación y pareja bundle/clave

Producer no sube a Hugging Face. El operador abre su repositorio en el Hub,
Files → Add file → Upload files, sube SOLO `minilm-l6-v2.bundle.enc`, confirma
el commit y copia su SHA de 40 caracteres. No subir claves, modelos en claro,
cachés ni carpetas de trabajo. Para un bundle nuevo, actualizar repositorio y
SHA en `k8s/bundle-source.yaml`, y entregar su clave correspondiente al Secret.

La demo existente usa [este commit público](https://huggingface.co/j0ssGZ/confidential-model-delivery-artifacts/tree/c6d037b94a2f9e1072198a9c8de94540ada55edc):
`c6d037b94a2f9e1072198a9c8de94540ada55edc`. Requiere su clave ORIGINAL,
entregada por canal privado y guardada en `secrets/model-key.bin`.
Una clave nueva NO abre ese bundle. No regenerarla para intentar resolver
un error de autenticación. No hace falta volver a publicar para repetirlo.

## Consumer en Kubernetes

Si ya existe `secure-ai`, omitir `kind create cluster`; no borrar el clúster.

```sh
kind create cluster --name secure-ai --image kindest/node:v1.36.4@sha256:099e049362a1526b2db71494e1947aae99bd16290d7c895f2b7ea312e3cbfaed --wait 5m
kubectl --context kind-secure-ai get nodes
docker build -f Dockerfile.consumer -t cmdp-consumer:0.1.0 .
kind load docker-image --name secure-ai cmdp-consumer:0.1.0
kubectl --context kind-secure-ai apply -f k8s/namespace.yaml -f k8s/bundle-source.yaml
sh scripts/create_model_secret.sh secrets/model-key.bin
kubectl --context kind-secure-ai apply -f k8s/consumer-job.yaml
kubectl --context kind-secure-ai -n secure-ai-poc wait --for=condition=complete job/model-consumer --timeout=180s
kubectl --context kind-secure-ai -n secure-ai-poc logs job/model-consumer
```

Esperado: Job Complete y `model_loaded=true embedding_shape=(1, 384)`.
El Secret contiene `key`; se monta como archivo de solo lectura en
`/var/run/secrets/model-delivery/key`. ConfigMap contiene repositorio y SHA.
La imagen solo contiene código/dependencias; el bundle se descarga al ejecutar.

## Dos negativos sin alterar la clave positiva

Para verificar en un clúster vacío sin tocar el laboratorio, usar el nombre
`secure-ai-repro` en `kind create` y `kind load`, sustituir el contexto por
`kind-secure-ai-repro` en todos los comandos y pasar ese contexto como segundo
argumento a `scripts/create_model_secret.sh`. Namespace y manifiestos son iguales.

```sh
kubectl --context kind-secure-ai apply -f k8s/wrong-key-job.yaml -f k8s/tampered-job.yaml
kubectl --context kind-secure-ai -n secure-ai-poc wait --for=condition=failed job/model-consumer-wrong-key --timeout=180s
kubectl --context kind-secure-ai -n secure-ai-poc wait --for=condition=failed job/model-consumer-tampered --timeout=180s
kubectl --context kind-secure-ai -n secure-ai-poc logs job/model-consumer-wrong-key
kubectl --context kind-secure-ai -n secure-ai-poc logs job/model-consumer-tampered
```

Ambos deben quedar Failed, salir con código distinto de cero y mostrar
`bundle authentication failed`, sin `model_loaded=true`. El primero genera
una clave temporal; el segundo altera el último byte del tag. Los tests
unitarios también alteran ciphertext y metadata.

Para repetir Jobs terminados, guardar primero sus logs y eliminar únicamente
los Jobs de la demo antes de aplicar otra vez:

```sh
kubectl --context kind-secure-ai -n secure-ai-poc delete job model-consumer model-consumer-wrong-key model-consumer-tampered --ignore-not-found
```

Esto elimina esos Pods y sus volúmenes temporales; no borra el Secret. Los
logs dejarán de estar disponibles en Kubernetes: conservar evidencia antes.

## Diagnóstico y límites

- Error de descarga: revisar acceso a Internet, repositorio y SHA completo.
- `ImagePullBackOff`/`ErrImageNeverPull`: cargar la imagen en el mismo kind.
- Error de configuración: comprobar namespace, ConfigMap y existencia del
  Secret sin volcar su contenido; usar `kubectl describe job model-consumer`
  con el contexto y namespace anteriores.
- MiniLM es público en origen; la PoC cifra nuestra copia, no vuelve secreto
  el modelo original. Metadata visible y autenticada; AES-GCM no firma al autor.
- Descarga online, carga local (`local_files_only=True`), caché nueva y sin
  código remoto. No hay NetworkPolicy de egress ni TEE. El host es confiable.
- La clave local/Secret persisten. El Consumer retira solo su temporal;
  `emptyDir` desaparece al retirar el Pod. No es borrado seguro ni RAM exclusiva.
- AESGCM/TAR completos en RAM. Nonce aleatorio sin registro de colisiones.
- `.gitignore` no es un escáner de secretos. Layer 2 está implementada y
  verificada; Layer 3 solo llega hasta el recorrido sintético L3-05, sin
  Consumer attested ni AES real.

El ensayo personal de defensa requiere participación de Jose y no se da por
terminado al pasar las pruebas automáticas.

## Revisión acotada del historial

```sh
uv run python scripts/audit_history.py --key-file secrets/model-key.bin
```

Recorre blobs de todas las referencias Git locales y busca la clave conocida
(bytes/hex/Base64), patrones de tokens HF/GitHub y cabeceras de claves privadas.
Solo muestra conteos e identificadores de blobs; no imprime coincidencias.
Cero hallazgos no prueba ausencia de todo secreto imaginable ni analiza
reflogs, ramas remotas no descargadas o infraestructura de producción.
