# Layer 3: runtime CoCo y Trustee sintético

Estado: L3-05 verificada; todavía no hay Consumer attested ni AES real en KBS.
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
y usa LocalFs sobre `emptyDir`: es adecuado solo para este recurso sintético.

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
restaura `allow_all.rego`, cierra el port-forward y retira token y recurso local
temporales. Los Pods y sus logs permanecen como evidencia. Salida final:

```text
trustee_allow_ok=true
trustee_allow_kbs_http=200
trustee_deny_ok=true
trustee_deny_kbs_http=401
trustee_policy_restored=allow_all
trustee_synthetic_allow_deny_ok=true
```

CDH presenta el rechazo al `wget` como HTTP 500, mientras el registro
autoritativo de KBS muestra 401 para
`GET /kbs/v0/resource/default/test/l3-synthetic`. No considerar válido un
negativo si solo falló el contenedor, la red o el filesystem. Consultar ambos
logs y el código de salida.

## Alcance

El patrón de RuntimeClass/anotación sigue el
[workload mínimo oficial](https://confidentialcontainers.org/docs/getting-started/workload/).
La dirección KBS y el endpoint CDH siguen la
[configuración CoCo](https://confidentialcontainers.org/docs/attestation/coco-setup/)
y el [flujo get-resource](https://confidentialcontainers.org/docs/features/get-resource/)
oficiales. `coco-dev` usa evidencia `Sample`: valida integración, attestation de
muestra y enforcement de política, no una TEE real ni protección frente al host.
HTTP interno, identidades demo, LocalFs efímero y `allow_all` impiden usar la AES
real. Ver [spec](../../docs/specs/003-layer3.md),
[runtime 008](../../docs/reports/008-layer3-runtime-smoke.md) y
[Trustee 009](../../docs/reports/009-layer3-trustee-synthetic.md).
