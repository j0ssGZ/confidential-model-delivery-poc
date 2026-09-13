# Evidencia L3-04: runtime Kata/CoCo operativo

Fecha: 13-09-2026, desde 02:32 UTC. Base del repositorio: `ebe72b4`.

## Resultado

CoCo chart 0.22.0 terminó de instalar Kata 4.0.0. Los logs registran la
finalización a las 02:25:44 UTC; DaemonSet `kata-as-coco-runtime` disponible
1/1 y nodo `secure-ai-node` Ready. `id -nG` y comprobación de permisos confirman
que el operador pertenece a `kvm` y puede leer/escribir `/dev/kvm`.

Dos Pods del namespace nuevo `secure-ai-layer3` ejecutaron
`runtimeClassName: kata-qemu-coco-dev`:

- `kata-runtime-smoke-hpmxt`: BusyBox 1.37.0, Succeeded, exit 0.
- `kata-runtime-smoke-pfsfv`: mismo ensayo con digest fijado en el manifiesto,
  Succeeded, exit 0.

Ambos mostraron:

```text
6.18.35
kata_smoke_ok=true
```

El host devolvió `5.15.0-191-generic`. El proceso comprobó UID 10001 y la API
registró UID/GID 10001. El manifiesto configura raíz de solo lectura, elimina
capabilities y desactiva el montaje del token Kubernetes. No contiene volúmenes
de claves ni modelos. Digest observado y probado en el segundo Pod:

```text
docker.io/library/busybox@sha256:9db7b59979c38555a39def84a31fb98b5296952f9e3afd4f6f11f05b07adfab0
```

## Verificación

- `kubectl get nodes`, `get pods -A`, `get daemonset -n coco-system` y
  `get runtimeclass kata-qemu-coco-dev`: nodo/servicios/runtime disponibles.
- `kubectl logs -n coco-system daemonset/kata-as-coco-runtime --tail=70`:
  instalación terminada y reinicio de containerd completado por el instalador.
- `kubectl create --dry-run=server -f -`: API acepta el smoke inicial.
- `kubectl create -f -`: ensayo inicial y después manifiesto con digest;
  el YAML versionado se transmitió por stdin, sin copiar credenciales.
- `kubectl -n secure-ai-layer3 wait --for=jsonpath='{.status.phase}'=Succeeded
  pod/<nombre> --timeout=45s`: ambos completados.
- `kubectl logs` y `kubectl get pod -o json/jsonpath`: salida, identidad,
  runtime, digest y código 0 comprobados.
- [Runbook](../../k8s/layer3/README.md) y manifiestos permiten repetir el ensayo.
- `UV_CACHE_DIR=/private/tmp/cmdp-uv-cache uv run pytest -q`: 84 tests pasan
  en 3,09 s; regresión existente de Layer 1/2, no tests de attestation.
- `git diff --check`: salida 0, sin errores de whitespace.

README, spec, decisión, plan y tareas reflejan este checkpoint. Se actualizaron
y releyeron las páginas Notion principal, Layer 3 y defensa/flujo, conservando
subpáginas y diagramas; los checks solo acreditan el runtime, no la capa completa.

## Límites y siguiente fase

Hubo timeouts al conectar por SSH y el acceso se recuperó durante los
reintentos; no se ha diagnosticado la causa de esa intermitencia.
`uptime -s` seguía indicando el arranque de 12-09-2026 23:39:15: esta evidencia
no es una validación después de reiniciar el servidor.

L3-04 satisface el criterio de Pod mínimo, pero no demuestra una TEE real,
attestation ni liberación de clave. Trustee, políticas y Consumer attested
siguen pendientes. Los dos Pods completados se conservan como evidencia.
No se leyeron ni modificaron AES, privadas Ed25519, bundle publicado o tags.
Los cambios versionados se limitan al ensayo Layer 3 y su documentación;
no cambian Python, Dockerfiles ni manifests de Layer 1/2.
