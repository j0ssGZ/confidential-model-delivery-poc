# Layer 2: Jobs aislados

Namespace `secure-ai-layer2`, imagen `cmdp-consumer:layer2`, ServiceAccount
`signed-consumer` sin token montado. `job.json` es una plantilla: usar el
renderizador, no aplicarla directamente porque aún no tiene argumentos.

## Preparación

Desde la raíz, con `uv sync --locked`, modelo/pareja cifrada firmada local y
las claves correspondientes. No generar claves nuevas para abrir otro bundle.

```sh
docker build -f Dockerfile.consumer -t cmdp-consumer:layer2 .
kind load docker-image --name secure-ai-repro cmdp-consumer:layer2
kubectl --context kind-secure-ai-repro apply -f k8s/layer2/namespace.yaml
uv run python scripts/provision_layer2.py --context kind-secure-ai-repro \
  --public-key keys/signing-public.pem --aes-key secrets/reproduction-20260911.bin
```

La ruta AES anterior corresponde al bundle de `artifacts/layer2` de esta
sesión. En otra reproducción, sustituirla por la clave usada por su Producer.
El script valida las claves y crea/actualiza ConfigMap y Secret SOLO en el
namespace Layer 2. La representación del Secret pasa en memoria entre procesos;
no se imprime. La privada de firma nunca se entrega a Kubernetes.

## Ensayo local verificado, sin Hub

Se usa un directorio dedicado del nodo kind, montado de solo lectura. Es un
hostPath de laboratorio; no se usa en la variante Hub ni se presenta como
despliegue de producción. La prueba incluye claves, firma, GCM y carga en Pod,
pero no verifica publicación/descarga desde Hub.

```sh
docker exec secure-ai-repro-control-plane mkdir -p /tmp/cmdp-layer2-fixtures
tar -C artifacts/layer2 -cf - minilm-l6-v2.bundle.enc minilm-l6-v2.bundle.enc.sig | \
  docker exec -i secure-ai-repro-control-plane tar -xf - -C /tmp/cmdp-layer2-fixtures
for case_name in positive tampered-bundle tampered-signature wrong-public wrong-aes; do
  uv run python scripts/layer2_jobs.py --case "$case_name" \
    --fixture-path /tmp/cmdp-layer2-fixtures | \
    kubectl --context kind-secure-ai-repro create -f -
done
kubectl --context kind-secure-ai-repro -n secure-ai-layer2 get jobs,pods
kubectl --context kind-secure-ai-repro -n secure-ai-layer2 logs job/signed-fixture-positive
```

La transferencia tar se usó porque `docker cp` no resolvía el directorio,
aunque `docker exec ls` sí lo veía. Se copiaron únicamente esos dos archivos.
Si los Jobs ya existen, `create` falla: inspeccionar/conservar sus logs antes
de decidir si se eliminan y recrean. El script no borra recursos previos.

Esperado: positivo Complete, salida 0; tres negativos de firma salida 2 con
`bundle signature verification failed`; AES incorrecta salida 2 con
`bundle authentication failed`. Cada negativo altera una copia en `/work`,
sin cambiar las fixtures ni los recursos de claves.

## Variante Hub: pendiente de publicación

Subir SOLO `minilm-l6-v2.bundle.enc` y `.enc.sig` al repositorio de artefactos,
en un nuevo commit, conservando el commit histórico de Layer 1. Copiar la
revisión completa y reemplazar el placeholder siguiente; no ejecutar literalmente:

```sh
uv run python scripts/layer2_jobs.py --case positive --revision COMMIT_COMPLETO_DE_40_HEX | \
  kubectl --context kind-secure-ai-repro create -f -
```

Repetir con los cuatro casos negativos. El renderizador rechaza revisiones
mutables/incompletas y no añade hostPath en modo Hub. Ambos archivos se
descargan de la misma revisión. Nombres `signed-hub-*`, distintos del ensayo
local. No existe todavía una revisión publicada de Layer 2 verificada.

## Confianza y permisos

El ConfigMap monta `public.pem` en `/etc/model-signing`; la AES llega por
Secret. La cuenta del Pod no necesita acceder a la API para leer esos archivos.
Se comprobó `auth can-i update configmaps` para esa ServiceAccount: `no`.
Esto no acredita todos los permisos posibles, otros usuarios ni seguridad del
host. Sigue siendo necesario confiar en el operador que aprovisiona la pública
y en quien puede modificar Jobs, imágenes y permisos.

No se retiran automáticamente Jobs, fixtures, claves ni namespace. El contenido
en `/work` es efímero; no se promete borrado seguro. Evidencia en
[informe 005](../../docs/reports/005-layer2-kubernetes-fixtures.md).
