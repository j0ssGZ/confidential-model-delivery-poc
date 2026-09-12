# Decisión 007: entorno y contrato de attestation de Layer 3

Estado: pendiente de aclaración. Las decisiones siguientes bloquean la
implementación de [Layer 3](../specs/003-layer3.md).

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

Pendiente de Jose: confirmar qué Ubuntu está instalado y facilitar las salidas
saneadas de `uname -m`, versión del sistema y comprobación de `/dev/kvm`.

## D2 — Combinación de versiones

**Recomendación:** evaluar primero CoCo chart 0.22.0 y una release etiquetada de
Trustee, sin usar `latest` ni clonar `main` en el procedimiento final. Se aprobará
la pareja únicamente después de arrancar el Pod mínimo y completar una petición
de recurso de prueba. Si falla, se elige una matriz documentada por una release
de CoCo; no se mezclan fragmentos del tutorial 0.10.0 con APIs actuales.

Pendiente: registrar Kubernetes, containerd, Helm, CoCo, Kata, Trustee y protocolo
KBS que realmente se ejecuten.

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

Pendiente: confirmar la sintaxis exacta de la release elegida y si Trustee vive
en el mismo clúster o en un host/namespace separado accesible desde la VM Kata.

## Respuesta oral defendible

«Layer 3 conserva la autenticidad de Layer 2 y cambia cómo llega la AES. Primero
verifico el artefacto público; después CDH inicia attestation y KBS solo libera el
recurso si la evidencia satisface su política. En `coco-dev` pruebo el protocolo,
no una TEE real. Por eso separo la demostración funcional de la garantía de
hardware y fijo todas las versiones comprobadas.»
