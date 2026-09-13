# Decisión 007: entorno y contrato de attestation de Layer 3

Estado: D1–D4 cerradas para la PoC el 13-09-2026. Audience y política acotada
verificadas en Trustee real. El aprovisionamiento AES espera comprobar el nuevo
proveedor Python dentro de Kata con la fixture pública de 32 bytes.

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

**Decisión D3:** `cmdp-consumer-attested`, basado en el Consumer firmado. Sus
entradas serán bundle/firma local o revisión Hub, pública Ed25519, workdir y un
identificador de recurso CDH; no aceptará `--key-file`. Orden: verificar firma →
pedir recurso → validar 32 bytes → GCM/extraer/cargar. Una firma inválida no debe
provocar una petición de clave.

El proveedor `retrieve_key(resource, timeout)` usa exclusivamente HTTPConnection
a `127.0.0.1:8006/cdh/resource/<repositorio>/<tipo>/<identificador>`, sin proxies,
redirecciones ni URL configurable. Los tres segmentos admiten letras, números,
guiones y guiones bajos; no traversal ni query strings. Timeout finito positivo,
respuesta HTTP 200, lectura acotada a 33 bytes y exactamente 32 bytes exigidos.
No registra cuerpo, clave ni errores remotos. Una función callable pequeña
permite instrumentar el proveedor en tests. La clave permanece en memoria de
Python; no se escribe un archivo para reutilizar el Consumer Layer 1.

Se reutilizan descarga firmada, validación Ed25519, GCM/TAR y carga local
existentes. La nueva orquestación conserva una única instantánea de bytes y un
temporal propio. Marcadores públicos de etapa permiten correlacionar los
negativos; la salida final mantiene los campos de aceptación de la spec.

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

**Decisión D4 para la entrega:** el usuario autorizó evaluar los controles según
el challenge, manteniendo el host/clúster en la frontera de confianza. Se
conservan HTTP interno ClusterIP, LocalFs/emptyDir e identidades del laboratorio;
no se requiere PKI ni base de datos durable para demostrar la PoC. El operador
aprovisiona mediante SSH y port-forward autenticado de Kubernetes, con token y
AES en archivos privados temporales. Nunca se expone un NodePort/Ingress de KBS.
El reinicio/reemplazo del Pod KBS puede perder recursos: el runbook exige volver
a aprovisionar desde la AES original. No se afirma persistencia tras reboot sin
ejecutarlo. Una migración con adversario de red/host necesita TLS y TEE reales.

La política final deniega por defecto y exige plugin `resource`, query vacío,
evidencia `sample` en `submods.cpu0.ear.veraison.annotated-evidence`, y una lista
explícita de rutas: `default/key/minilm-l6-v2`, `default/test/l3-synthetic` y
`default/test/wrong-aes`. Una ruta `default/test/denied` queda fuera de la lista.
Esto acota recursos, pero Sample no autentica la identidad exclusiva de nuestro
workload: cualquier cliente capaz de producir esa evidencia puede satisfacerla.
No se atribuye aislamiento por identidad ni integridad del código a esta política.

El warning de audience pertenece a **autenticación administrativa de KBS**, no
a AS ni a la evidencia Sample. En `kbs/src/admin/authentication/bearer_jwt.rs`
del commit fijado, un `audience` ausente omite esa comprobación aunque siga
validando firma/issuer/rol. El chart genera `aud=KBS` pero omite `audience` en
`identity_providers`; se añadirá `audience="KBS"` a la configuración pública.
Se conservarán las identidades existentes y la evidencia antes de reiniciar
solo KBS. Se comprobará admin válido y rechazo de un token con audience distinta,
sin imprimir tokens ni claves. Esta corrección debe reaplicarse tras Helm si
el chart vuelve a renderizar su configuración predeterminada.

Verificación D4: admin válido HTTP 200 y otro token firmado por la misma identidad
pero con `aud=cmdp-wrong-audience` HTTP 401. No aparece el warning de audience
ausente. La política acotada pasó recurso sintético 200 y deny 401 en Kata;
el script la restauró al terminar. Logs y datos anteriores se conservaron en
un backup privado del operador antes de reiniciar únicamente el Deployment KBS.

Fuentes: [políticas oficiales](https://confidentialcontainers.org/docs/attestation/policies/),
[CDH](https://confidentialcontainers.org/docs/features/get-resource/) y código
[bearer_jwt.rs fijado](https://github.com/confidential-containers/trustee/blob/258ea4acb7b9bd865fce5c63a539f2120dba8298/kbs/src/admin/authentication/bearer_jwt.rs).

## Respuesta oral defendible

«Layer 3 conserva la autenticidad de Layer 2 y cambia cómo llega la AES. Primero
verifico el artefacto público; después CDH inicia attestation y KBS solo libera el
recurso si la evidencia satisface su política. En `coco-dev` pruebo el protocolo,
no una TEE real. Por eso separo la demostración funcional de la garantía de
hardware y fijo todas las versiones comprobadas.»
