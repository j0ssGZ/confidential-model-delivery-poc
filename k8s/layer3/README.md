# Layer 3: checkpoint del runtime CoCo

Estado: L3-04 verificada; todavía no hay Trustee ni Consumer attested.
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

## Alcance

El patrón de RuntimeClass/anotación sigue el
[workload mínimo oficial](https://confidentialcontainers.org/docs/getting-started/workload/).
El smoke sustituye nginx por un proceso finito y no privilegiado. `coco-dev`
no proporciona la garantía de una TEE real. Este ensayo no valida aún
attestation, políticas KBS ni entrega de AES. Ver [spec](../../docs/specs/003-layer3.md)
y [evidencia](../../docs/reports/008-layer3-runtime-smoke.md).
