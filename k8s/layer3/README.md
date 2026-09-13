# Layer 3: runtime CoCo y Trustee sintético

Estado: L3-06–L3-09 comprobadas: Consumer attested E2E desde Hub, clave por CDH
y positivo/negativos en Kata. L3-10 se cerró en `layer3-complete` (`b0fb7b6`).
Esta revisión posterior mejora documentación de reproducción y entrega.
Ejecutar en el servidor Ubuntu con su kubeconfig, desde un checkout de `layer3`.
No usar los contextos kind de Layer 1/2 para este ensayo.

## Comprobar y ejecutar

```sh
kubectl config current-context
kubectl get nodes -o wide
kubectl rollout status -n coco-system daemonset/kata-as-coco-runtime --timeout=45s
kubectl get runtimeclass kata-qemu-coco-dev
kubectl apply -f k8s/layer3/namespace.yaml
kubectl create --dry-run=server -f k8s/layer3/runtime-smoke.yaml
runtime_smoke_pod=$(kubectl create -f k8s/layer3/runtime-smoke.yaml -o name)
kubectl -n secure-ai-layer3 wait --for=jsonpath='{.status.phase}'=Succeeded "$runtime_smoke_pod" --timeout=300s
kubectl -n secure-ai-layer3 logs "$runtime_smoke_pod"
kubectl -n secure-ai-layer3 get "$runtime_smoke_pod" -o jsonpath='{.status.containerStatuses[0].state.terminated.exitCode}{"\n"}'
uname -r
```

Confirmar previamente que el contexto apunta al nodo Ubuntu `secure-ai-node`.
El Pod debe finalizar en `Succeeded`, código 0, con `kata_smoke_ok=true` en logs.
Su salida incluye el kernel guest. En esta ejecución fue 6.18.35 frente al
5.15.0-191-generic del host. Un Pod completado no permanece en condición Ready.

Se usa BusyBox 1.37.0 fijado por digest, UID/GID 10001, raíz de solo lectura,
sin capabilities adicionales ni token de ServiceAccount montado. No monta
claves/modelos ni solicita recursos KBS. `generateName` evita reemplazar el
ensayo anterior y el límite de 300 s acota el Pod. Los objetos y sus logs se
conservan; no se eliminan automáticamente.

Si falla o agota el tiempo, consultar `kubectl describe` del Pod concreto y sus
logs; no reinstalar CoCo ni reiniciar el clúster sin diagnosticar la causa.
Una RuntimeClass existente solo prueba que se creó el objeto. La ejecución del
Pod y el DaemonSet disponible comprueban además la instalación funcional.

## Instalar Trustee fijado

Trustee v0.21.0 declara compatibilidad con CoCo 0.22.0. Se usa su checkout
exacto y no `main`; el values file sustituye los tags `latest` predeterminados
de KBS, AS y RVPS por el commit de la release. El chart genera identidades demo
y usa LocalFs sobre `emptyDir`: D4 lo acepta para este laboratorio de host
confiable, no como almacenamiento durable o servicio de producción.

```sh
git clone --branch v0.21.0 --depth 1 \
  https://github.com/confidential-containers/trustee.git /tmp/trustee-v0.21.0
test "$(git -C /tmp/trustee-v0.21.0 rev-parse HEAD)" = \
  258ea4acb7b9bd865fce5c63a539f2120dba8298
helm dependency update /tmp/trustee-v0.21.0/deployment/helm-chart
helm upgrade --install trustee /tmp/trustee-v0.21.0/deployment/helm-chart \
  --namespace coco-trustee --create-namespace \
  -f k8s/layer3/trustee-values.yaml --wait --timeout 10m
kubectl -n coco-trustee wait --for=condition=available \
  deployment/trustee-kbs deployment/trustee-as deployment/trustee-rvps \
  --timeout=180s
helm -n coco-trustee get values trustee
```

El chart de esa release muestra `trustee-0.18.0` como versión interna; la fuente
aprobada sigue siendo el tag v0.21.0 y commit comprobado. Confirmar que los tres
tags efectivos terminan en
`258ea4acb7b9bd865fce5c63a539f2120dba8298-x86_64`.

Tras instalar con Helm, aplicar la corrección pública de audience. Este script
guarda configuración, logs y repositorio KBS en backup privado antes de reiniciar
solo KBS y restaurar sus datos; no regenera las identidades existentes:

```sh
python3 scripts/layer3_configure_audience.py --backup-parent /tmp/cmdp-l3-private-backups
python3 scripts/layer3_trustee_admin.py \
  --client /tmp/kbs-client-v0.21.0/kbs-client --check-audience --fixture
```

Esperado: admin válido 200, token con audiencia distinta 401 y fixture pública
`default/test/wrong-aes` registrada (32 ceros, no una clave de la demo).

## Obtener el cliente y repetir allow/deny

Instalar ORAS 1.3.0 verificando el checksum publicado. El artefacto `sample_only`
debe resolver al manifiesto esperado antes de extraerlo:

```sh
kbs_client_ref=ghcr.io/confidential-containers/staged-images/kbs-client:sample_only-258ea4acb7b9bd865fce5c63a539f2120dba8298-x86_64
test "$(oras resolve "$kbs_client_ref")" = \
  sha256:429be62c527e766a9854f9dac37f878010069c4aa6745d3d555d2bf393b9e82e
mkdir -p /tmp/kbs-client-v0.21.0
oras pull \
  ghcr.io/confidential-containers/staged-images/kbs-client@sha256:429be62c527e766a9854f9dac37f878010069c4aa6745d3d555d2bf393b9e82e \
  -o /tmp/kbs-client-v0.21.0
chmod 700 /tmp/kbs-client-v0.21.0/kbs-client
kubectl apply -f k8s/layer3/namespace.yaml
KBS_CLIENT=/tmp/kbs-client-v0.21.0/kbs-client \
TRUSTEE_CHECKOUT=/tmp/trustee-v0.21.0 \
  sh scripts/layer3_trustee_smoke.sh
```

El script copia el token administrativo a un directorio `mktemp` con umask 077,
sin imprimirlo; registra únicamente `cmdp-l3-synthetic-ok-v1` en
`default/test/l3-synthetic`. Crea dos Pods Kata desde los manifiestos, comprueba
marcadores y exige que KBS registre respectivamente HTTP 200 y 401. Finalmente
restaura `sample-resource-policy.rego`, cierra el port-forward y retira token y recurso local
temporales. Los Pods y sus logs permanecen como evidencia. Salida final:

```text
trustee_allow_ok=true
trustee_allow_kbs_http=200
trustee_deny_ok=true
trustee_deny_kbs_http=401
trustee_policy_restored=sample_resource_allowlist
trustee_synthetic_allow_deny_ok=true
```

CDH presenta el rechazo al `wget` como HTTP 500, mientras el registro
autoritativo de KBS muestra 401 para
`GET /kbs/v0/resource/default/test/l3-synthetic`. No considerar válido un
negativo si solo falló el contenedor, la red o el filesystem. Consultar ambos
logs y el código de salida.

## Imagen y Job del Consumer attested

Imagen AMD64 construida desde `0581d0c`, disponible públicamente sin credenciales:
`docker.io/jfanjul/confidential-model-delivery-consumer-attested@sha256:5ec1d732edfb5cb7a2efcbcdfadbba4f310759f1cd1d0ca309d64f36ce2238b6`.
El runtime descarga la imagen dentro de la VM; importar solo al containerd del
host no basta. Build y ayuda local comprobados:

```sh
docker build --platform linux/amd64 -f Dockerfile.consumer-attested \
  -t cmdp-consumer-attested:0581d0c .
docker run --rm --platform linux/amd64 --network none --read-only \
  --tmpfs /work:rw,nosuid,nodev,size=256m,mode=1777 \
  cmdp-consumer-attested:0581d0c --help
```

`/work` debe ser escribible incluso para la ayuda: las librerías ML utilizan
temporales durante su importación. No se montan modelo ni AES en la imagen.
La auditoría de todas las capas se ejecuta sobre `docker save` mediante
`scripts/audit_layer3_image.py --known-secret <archivo-privado>`; imprime rutas
y recuentos, no coincidencias. Los marcadores genéricos requieren revisión.

Configurar únicamente las entradas públicas con la pública confiada existente:

```sh
kubectl apply -f k8s/layer3/public-config.yaml
kubectl -n secure-ai-layer3 create configmap attested-signing-public \
  --from-file=public.pem=keys/signing-public.pem --dry-run=client -o yaml \
  | kubectl apply -f -
```

La definición JSON es una plantilla, no se aplica directamente. El renderer
exige imagen por digest e IPv4 interna de KBS, y genera Jobs nuevos. El caso
`synthetic` utiliza exclusivamente la fixture pública `default/test/wrong-aes`
de 32 ceros, previamente registrada con `layer3_trustee_admin.py --fixture`.
La fixture sintética debe demostrarse antes de aprovisionar la AES real.

```sh
layer3_image=docker.io/jfanjul/confidential-model-delivery-consumer-attested@sha256:5ec1d732edfb5cb7a2efcbcdfadbba4f310759f1cd1d0ca309d64f36ce2238b6
layer3_kbs_ip=$(kubectl -n coco-trustee get svc trustee-kbs -o jsonpath='{.spec.clusterIP}')
python3 scripts/layer3_jobs.py --case synthetic \
  --image "$layer3_image" --kbs-ip "$layer3_kbs_ip" | kubectl create -f -
python3 scripts/layer3_verify_job.py --job <nombre-devuelto> --case synthetic \
  --evidence-dir /tmp/cmdp-l3-evidence
```

El verificador conserva resultados, logs y Pod, y exige salida 0 **más** marcador
del proveedor **más** KBS 200. Un error de arranque no es un negativo válido.
No elimina los Jobs. Ejecutar un caso cada vez. El Job usa UID 10001, raíz de
solo lectura, capabilities vacías, sin escalada ni token de ServiceAccount;
`/work` es `emptyDir` Memory con límite explícito. Los únicos otros volúmenes
son configuración pública. No hay AES Secret.

### Timeouts de guest pull

La imagen completa supera el límite de 60 s observado inicialmente. El renderer
usa la anotación oficial Kata 4.0.0 `create_container_timeout=300`. El segundo
ensayo detectó además la cancelación de kubelet a 120 s. En este host:

```sh
sudo python3 scripts/layer3_kubelet_timeout.py
kubectl get nodes
kubectl -n coco-trustee get pods
```

El script acepta solo el valor original observado `runtimeRequestTimeout: 0s`,
guarda backup privado y lo cambia a `10m0s`, reiniciando solo kubelet. Si el
archivo tiene otro valor, se detiene para diagnosticar. Es idempotente para el
valor nuevo. No ejecutar reinstalaciones ni retirar los Jobs fallidos.

Resultado comprobado: `attested-synthetic-4fmlj` arrancó con estos ajustes,
imprimió `cdh_python_synthetic_ok=true`, KBS respondió 200 y el Pod terminó con
salida 0. [Evidencia 011](../../docs/reports/011-layer3-cdh-image.md).

### Reboot y recorrido E2E comprobados

El reboot del host fue comprobado: nodo, RuntimeClass y despliegues Trustee
volvieron a `Ready`, pero el repositorio LocalFs de KBS respaldado por `emptyDir`
perdió los recursos. Es el comportamiento esperado de D4, no una garantía de
persistencia. Se restauró primero la fixture sintética y se repitió CDH.

Solo entonces el operador registró, mediante `layer3_trustee_admin.py --key-file`
y el cliente KBS fijado, los 32 bytes ya asociados al bundle firmado bajo
`default/key/minilm-l6-v2`. El archivo siguió siendo privado: no se mostró ni se
copió a YAML, Secret Kubernetes, imagen, Git ni logs. No se regeneró ni
republicó ningún artefacto. El procedimiento debe verificar el emparejamiento
bundle/AES localmente antes de escribir el recurso; una clave válida de otro
bundle provoca el negativo GCM, no debe reinterpretarse como fallo de CDH.

Renderizar y verificar un Job por caso, siempre con la imagen digest y ClusterIP
actuales. El verificador conserva logs saneados, código de salida, RuntimeClass,
ausencia de Secret AES y el acceso KBS:

```sh
for case in positive tampered-signature positive denied positive wrong-aes positive; do
  job=$(python3 scripts/layer3_jobs.py --case "$case" --image "$layer3_image" \
    --kbs-ip "$layer3_kbs_ip" | kubectl create -f - -o name)
  job=${job#job.batch/}
  python3 scripts/layer3_verify_job.py --job "$job" --case "$case" \
    --evidence-dir /tmp/cmdp-l3-evidence
done
```

Esperado: `positive` acaba con salida 0 y `signature_verified=true
key_retrieved=true model_loaded=true embedding_shape=(1, 384)`; firma manipulada
termina con salida 2 sin etapas CDH; `denied` llega a `key_requested` y KBS
registra 401, sin GCM; `wrong-aes` llega a `key_retrieved`, KBS registra 200 y
GCM rechaza antes de extracción. Repetir positivo demuestra la restauración del
estado. `layer3-complete` conserva el checkpoint técnico ya publicado.

## Alcance

El patrón de RuntimeClass/anotación sigue el
[workload mínimo oficial](https://confidentialcontainers.org/docs/getting-started/workload/).
La dirección KBS y el endpoint CDH siguen la
[configuración CoCo](https://confidentialcontainers.org/docs/attestation/coco-setup/)
y el [flujo get-resource](https://confidentialcontainers.org/docs/features/get-resource/)
oficiales. `coco-dev` usa evidencia `Sample`: valida integración, attestation de
muestra y enforcement de política, no una TEE real ni protección frente al host.
La política final exige Sample y limita rutas, sin certificar identidad exclusiva
del workload. HTTP interno, identidades demo y LocalFs efímero se aceptan para
el laboratorio de host/clúster confiables; el reinicio de KBS puede exigir
reaprovisionamiento. Ver D4 y [spec](../../docs/specs/003-layer3.md),
[runtime 008](../../docs/reports/008-layer3-runtime-smoke.md) y
[Trustee 009](../../docs/reports/009-layer3-trustee-synthetic.md).
