# Layer 3: liberación de clave condicionada a attestation

Estado: infraestructura CoCo, Trustee, proveedor CDH y Consumer separado
comprobados. Tras revalidar el host después de reboot, el Consumer obtuvo por
CDH la AES ya asociada al bundle firmado y cargó MiniLM desde Hugging Face en
`kata-qemu-coco-dev`. Los negativos firma/CDH/GCM también se ejecutaron en el
entorno real. Queda auditoría y cierre documental; no se declara aún el tag
final. Ver la [decisión 007](../decisions/007-layer3-attestation.md) y el
[informe 012](../reports/012-layer3-e2e.md).

## Objetivo

Sustituir la entrega directa de la clave AES al workload mediante Kubernetes
Secret por una recuperación a través del Confidential Data Hub (CDH) y Trustee
KBS, condicionada por attestation y una política. Conservar la firma Ed25519 de
Layer 2: el nuevo Consumer debe verificar bundle y firma antes de solicitar la
clave y descifrar.

La primera demostración usará `kata-qemu-coco-dev`. Ese runtime permite ensayar
la arquitectura sin hardware confidencial, pero usa un attester/verificador de
muestra y **no demuestra confidencialidad frente al host ni attestation de una
TEE real**.

## Base preservada

- `main` continúa como Layer 1 canónica.
- `layer1-complete` continúa como hito histórico original.
- `layer2-complete` fija Layer 2 en
  `e9234b991603c5161fb1f6a623934ae5e3441ab3`.
- La rama `layer3` añade recursos y documentación separados. No cambia las CLI,
  imágenes, Jobs ni evidencias reproducibles de Layer 1 y Layer 2.
- Se reutilizan el bundle firmado, la revisión inmutable de Hugging Face y la
  clave pública Ed25519 confiada. No se vuelve a publicar el artefacto.

## Amenaza y frontera de confianza

Layer 2 todavía entrega la AES directamente desde un Secret montado. Un actor
con control suficiente del nodo o plano de control puede acceder a ese secreto,
al filesystem del contenedor o a su memoria.

Layer 3 pretende demostrar la separación arquitectónica siguiente: Trustee es
el custodio del recurso; el workload lo solicita mediante componentes CoCo; KBS
evalúa evidencia y política antes de liberarlo. En un despliegue con TEE real,
políticas y cadena de confianza adecuadas, esto puede reducir la confianza en el
host. En `coco-dev`, el host y la infraestructura de laboratorio siguen dentro
de la frontera de confianza y el resultado solo valida el protocolo.

Trustee, sus credenciales administrativas, el canal de aprovisionamiento, la
política, las imágenes, la clave pública Ed25519 y la definición del workload
continúan siendo raíces de confianza. Attestation no certifica la calidad ni la
seguridad del modelo y no añade por sí sola protección antirrollback.

## Flujo propuesto

1. El operador conserva localmente la AES ya asociada al bundle positivo.
2. El operador registra esos 32 bytes como recurso de KBS sin guardarlos en Git,
   imágenes, ConfigMaps, manifiestos ni logs.
3. El Job arranca con `runtimeClassName: kata-qemu-coco-dev` y configura la URI
   de KBS para el Attestation Agent/CDH. KBS debe ser accesible desde la VM Kata;
   `localhost` no es válido para esa dirección.
4. El Consumer descarga bundle y firma de la misma revisión inmutable y valida
   Ed25519 con la pública aprovisionada independientemente.
5. Solo después de validar la firma solicita al CDH local el recurso de clave.
   CDH se ocupa del recorrido KBC → evidencia → KBS → política → recurso.
6. El Consumer exige exactamente 32 bytes, descifra con AES-256-GCM, valida la
   identidad MiniLM, extrae en su temporal, carga localmente y comprueba un
   embedding finito `(1, 384)`.
7. El Consumer retira su temporal propio. Esta limpieza no equivale a borrado
   seguro de memoria ni de los almacenes de Trustee.

## Requisitos funcionales

Contrato de implementación: CLI `cmdp-consumer-attested` separada, proveedor
CDH local sin proxy/redirect, timeout y lectura acotados, clave exactamente de
32 bytes en memoria. Orden observable: firma → petición CDH → clave válida →
GCM/hash/identidad → extracción → carga. Se mantienen los comportamientos L1/L2.
El despliegue de laboratorio conserva almacenamiento KBS efímero y transporte
interno HTTP; la política limita Sample y rutas, no prueba identidad exclusiva
del workload. Ver las decisiones D3/D4 para la justificación y sus límites.

- **L3-F1:** añadir una CLI explícita de Layer 3, sin fallback a `--key-file` ni
  al Secret directo de Layer 1/2.
- **L3-F2:** reutilizar el camino firmado de Layer 2 y verificar los mismos bytes
  que después se descifran.
- **L3-F3:** obtener la AES mediante CDH usando un identificador de recurso
  configurado; validar longitud y traducir fallos a errores controlados sin
  imprimir material secreto.
- **L3-F4:** mantener la clave privada Ed25519 fuera del clúster. La pública puede
  seguir en ConfigMap de confianza; la AES no se monta en el Job Layer 3.
- **L3-F5:** usar manifiestos, namespace, nombre de imagen y runbook separados en
  `k8s/layer3/`.
- **L3-F6:** fijar versiones e imágenes por versión o digest y registrar la
  combinación comprobada de Ubuntu, Kubernetes, containerd, CoCo y Trustee.
- **L3-F7:** preservar los entrypoints y pruebas de Layer 1/2.

## Requisitos de seguridad y reproducibilidad

- No versionar ni publicar AES, privadas, tokens administrativos, credenciales,
  recursos KBS materializados, modelos en claro, cachés o temporales.
- No pasar secretos por argumentos, YAML versionado o variables registrables si
  existe un mecanismo de archivo/stdin controlado. No mostrar el recurso KBS.
- El Job Layer 3 no debe referenciar `model-decryption-key` ni otro Secret con la
  AES. Comprobarlo estática y dinámicamente.
- Fijar la revisión del bundle y su firma; mantener la pública Ed25519 fuera del
  mismo origen sustituible.
- Usar la instalación Helm oficial de CoCo. Los comandos del tutorial 0.10.0 son
  contexto histórico, no instrucciones ejecutables para la versión actual.
- Guardar evidencia de versiones, estados, códigos de salida y logs saneados.

## Criterios de aceptación

1. Entorno x86_64 con KVM, containerd, Kubernetes y Helm comprobados.
2. Instalación CoCo fijada; existe `kata-qemu-coco-dev` y un Pod mínimo arranca.
3. Trustee/KBS fijado y accesible desde la VM Kata; política y recurso se cargan
   sin revelar su contenido.
4. Job positivo sin Secret AES: firma válida, recurso autorizado, GCM válido y
   `signature_verified=true key_retrieved=true model_loaded=true
   embedding_shape=(1, 384)` con salida 0.
5. Firma o bundle manipulados: rechazo antes de pedir la clave y antes de
   descifrar, demostrado con tests instrumentados.
6. Recurso ausente o política denegatoria: no se obtiene la AES, no se descifra,
   salida no cero y logs sin secretos.
7. Clave de 32 bytes incorrecta obtenida mediante un recurso de prueba separado:
   attestation/liberación pasan y AES-GCM rechaza.
8. Suite completa de Layer 1/2 continúa pasando junto a tests nuevos.
9. Escaneo acotado no encuentra la AES conocida, privadas ni tokens en cambios,
   historial, imágenes Layer 3 o logs observados; se documentan sus límites.
10. README, spec, decisión, plan, tareas, informes y Notion están sincronizados.

Resultado al 13-09-2026: criterios 1–7 satisfechos en el laboratorio. Trustee
v0.21.0 se fijó al commit compatible declarado con CoCo 0.22.0. Tras reboot el
nodo, RuntimeClass y servicios Trustee volvieron a `Ready`, mientras que el
backend `emptyDir` de KBS perdió sus recursos, tal como predice D4; se restauró
la fixture sintética y, solo tras ello, el recurso AES existente que corresponde
al bundle firmado. No se generó AES ni se republicó Hugging Face.

`attested-positive-5xx5n` terminó con salida 0, firma validada, clave recuperada
vía CDH, GCM autenticado y embedding `(1, 384)`, sin Secret AES. El negativo de
firma terminó antes de `key_requested`; el de recurso denegado produjo KBS 401
antes de recuperar clave/GCM; y el recurso de prueba de 32 ceros produjo KBS 200
pero falló GCM antes de extracción/carga. Cada negativo se siguió de un positivo
restaurado. Los criterios 8–10 (suite final, auditoría y sincronización total)
siguen abiertos. [Evidencias 008](../reports/008-layer3-runtime-smoke.md),
[009](../reports/009-layer3-trustee-synthetic.md),
[011](../reports/011-layer3-cdh-image.md) y
[012](../reports/012-layer3-e2e.md).

## Fuera de alcance

- Afirmar protección de una TEE real con `kata-qemu-coco-dev`.
- Intel TDX, AMD SEV-SNP, GPU confidencial o una migración a producción.
- Crear una plataforma KMS/PKI, rotación automática o política antirrollback.
- Cifrado de imagen OCI; el objetivo mínimo es liberar la AES del bundle.
- Refirmar o republicar el bundle existente y modificar las capas anteriores.

## Referencias primarias revisadas

- [Instalación actual de CoCo con Helm](https://confidentialcontainers.org/docs/getting-started/installation/).
- [Workload mínimo con `kata-qemu-coco-dev`](https://confidentialcontainers.org/docs/getting-started/workload/).
- [Configuración de CoCo hacia Trustee](https://confidentialcontainers.org/docs/attestation/coco-setup/).
- [Instalación de Trustee](https://confidentialcontainers.org/docs/attestation/installation/).
- [Tutorial sin hardware confidencial](https://confidentialcontainers.org/blog/2024/12/03/confidential-containers-without-confidential-hardware/).
- [Plan](../plans/003-layer3-plan.md) y [tareas](../tasks/003-layer3-tasks.md).
- [Bootstrap del laboratorio](../reports/007-layer3-bootstrap.md).
- [Runbook y smoke CoCo](../../k8s/layer3/README.md).
- [Instalación oficial de Trustee con Helm](https://confidentialcontainers.org/docs/attestation/installation/helm/).
- [Acceso a recursos mediante CDH](https://confidentialcontainers.org/docs/features/get-resource/).
