# Decisión 007: entorno y contrato de attestation de Layer 3

Estado: D1–D2 comprobadas el 13-09-2026; D3 pendiente; D4 aprobada para el
ensayo sintético y pendiente para la AES real.
El código de [Layer 3](../specs/003-layer3.md) continúa bloqueado.

## Hechos confirmados

- Layer 2 está cerrada en `layer2-complete`; Layer 3 parte de ese hito.
- Se preservará la firma Ed25519: la opción recomendada es Layer 2 + liberación
  de clave, no volver a un Consumer sin firma.
- El tutorial de diciembre de 2024 pide Ubuntu 22.04, 8 GB, 4 CPU y Kubernetes
  1.30.1+, y usa CoCo 0.10.0 mediante el antiguo Operator.
- La documentación oficial vigente instala el runtime mediante Helm. El
  repositorio del CoCo Operator indica que fue sustituido por el chart.
- A 13-09-2026, la release publicada del chart CoCo es 0.22.0. Trustee tiene
  ciclo propio; no se supondrá compatibilidad por coincidencia de números.
- `kata-qemu-coco-dev` está destinado a desarrollo sin TEE. Necesita ejecutar
  una VM Kata/QEMU; el laboratorio candidato es el PC x86_64 con Ubuntu nativo,
  no el Mac Apple Silicon con una capa adicional de virtualización.

## D1 — Host objetivo

**Recomendación:** PC Intel x86_64, Ubuntu Server 22.04 LTS bare metal, mínimo
8 GB RAM y 4 CPU, KVM visible. Mantiene la base explícitamente probada por el
tutorial, aunque después usemos componentes actuales fijados.

Alternativa: Ubuntu 24.04 LTS, solo si el checkpoint de compatibilidad del chart
y `kata-qemu-coco-dev` pasa antes de programar el Consumer. Una VM anidada en el
Mac aumenta el riesgo de bloqueo y no es el camino recomendado para la entrega.

**Resultado:** opción recomendada confirmada. `secure-ai-node` ejecuta Ubuntu
22.04.5 LTS x86_64 en el PC Intel i5-4670K, con VT-x, módulos `kvm_intel`/`kvm`,
`/dev/kvm`, 4 CPU, 7,7 GiB de RAM y 86 GiB libres en el bootstrap. El nuevo login
confirmó pertenencia a `kvm` y acceso de lectura/escritura al dispositivo.

## D2 — Combinación de versiones

**Recomendación:** evaluar primero CoCo chart 0.22.0 y una release etiquetada de
Trustee, sin usar `latest` ni clonar `main` en el procedimiento final. Se aprobará
la pareja únicamente después de arrancar el Pod mínimo y completar una petición
de recurso de prueba. Si falla, se elige una matriz documentada por una release
de CoCo; no se mezclan fragmentos del tutorial 0.10.0 con APIs actuales.

**Resultado:** Kubernetes/kubeadm/kubelet/kubectl 1.36.4 fijados,
containerd 2.2.1 activo con `SystemdCgroup=true`, Helm 3.18.6 verificado por
checksum, Flannel 0.28.8 y CoCo chart 0.22.0 con digest registrado. El DaemonSet
Kata 4.0.0 terminó y el Pod mínimo con `kata-qemu-coco-dev` pasó (salida 0,
kernel guest 6.18.35). Dos ensayos, el segundo fijado por digest de BusyBox,
están en el [informe 008](../reports/008-layer3-runtime-smoke.md).

**Trustee aprobado para L3-05:** release `v0.21.0`, commit
`258ea4acb7b9bd865fce5c63a539f2120dba8298`, que la release declara como la
versión usada con CoCo 0.22.0. KBS, AS y RVPS usan los tags x86_64 de ese commit;
el cliente `sample_only` usa el mismo commit y el manifiesto OCI
`sha256:429be62c527e766a9854f9dac37f878010069c4aa6745d3d555d2bf393b9e82e`.
El chart contenido en esa release conserva metadatos `trustee-0.18.0`/
`appVersion: 0.18.0`; no se interpretó ese número como otra matriz: se instaló
el chart del checkout exacto y se fijaron las tres imágenes al commit de la
release. El recorrido allow/deny está en el
[informe 009](../reports/009-layer3-trustee-synthetic.md).

## D3 — Contrato del Consumer

**Recomendación:** `cmdp-consumer-attested`, basado en el Consumer firmado. Sus
entradas serán bundle/firma local o revisión Hub, pública Ed25519, workdir y un
identificador de recurso CDH; no aceptará `--key-file`. Orden: verificar firma →
pedir recurso → validar 32 bytes → GCM/extraer/cargar. Una firma inválida no debe
provocar una petición de clave.

Alternativa: adaptar el mismo `cmdp-consumer-signed` con dos proveedores de
clave. Se descarta por defecto porque aumenta combinaciones y hace menos visible
en la demo qué frontera se está verificando.

## D4 — Política y almacenamiento KBS

**Recomendación de PoC:** recurso `default/key/minilm-l6-v2`, backend de prueba
no versionado y política mínima que autorice la evidencia `sample` requerida por
`coco-dev`. Añadir un caso denegatorio. La política permisiva solo prueba el
recorrido; no se describirá como control respaldado por hardware.

**Decisión para el ensayo sintético:** Trustee vive en el mismo clúster, en el
namespace separado `coco-trustee`, y usa LocalFs efímero y las identidades demo
generadas por el chart. El recurso no secreto es `default/test/l3-synthetic`.
Se prueban las políticas `allow_all.rego` y `deny_all.rego` de la release, y se
restaura allow al terminar. Esta decisión solo habilita L3-05; antes de registrar
la AES real se revisarán persistencia, TLS, identidad administrativa y política
mínima ligada al workload como parte de D4. El warning observado sobre
`audience` de trusted issuers también debe resolverse antes de ese paso.

## Respuesta oral defendible

«Layer 3 conserva la autenticidad de Layer 2 y cambia cómo llega la AES. Primero
verifico el artefacto público; después CDH inicia attestation y KBS solo libera el
recurso si la evidencia satisface su política. En `coco-dev` pruebo el protocolo,
no una TEE real. Por eso separo la demostración funcional de la garantía de
hardware y fijo todas las versiones comprobadas.»
