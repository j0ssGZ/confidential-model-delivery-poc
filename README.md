# Confidential Model Delivery PoC

Challenge de Capacity Secure AI. El repositorio sigue Specification-Driven
Development; las reglas están en [`AGENTS.md`](AGENTS.md).

## Estado

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
uv sync --locked
uv run pytest -q
```

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
docker build --tag cmdp-consumer:0.1.0 .
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
- `.gitignore` no es un escáner de secretos. Layer 2/3 no están implementadas.

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
