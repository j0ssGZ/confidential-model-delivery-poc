# Plan 003: Layer 3

Estado: bootstrap del host y Kubernetes completado; instalación CoCo en curso.
El código del Consumer continúa bloqueado por D2–D4 de la
[decisión 007](../decisions/007-layer3-attestation.md). Contrato en la
[spec](../specs/003-layer3.md).

1. **Cerrar entorno y versiones.** Inspeccionar el PC Ubuntu sin mostrar datos
   sensibles, aprobar host y fijar Kubernetes/containerd/Helm/CoCo/Trustee.
2. **Validar infraestructura mínima.** Instalar CoCo por Helm, comprobar la
   RuntimeClass y arrancar un Pod inocuo con `kata-qemu-coco-dev`.
3. **Validar Trustee aislado.** Desplegar KBS/AS/RVPS por un método fijado,
   comprobar conectividad desde la VM Kata, cargar una política y un recurso
   sintético no secreto, y verificar permiso/denegación.
4. **Implementar el proveedor CDH.** Añadir recuperación de bytes, límites,
   timeout, validación de longitud, errores saneados y tests sin red real.
5. **Integrar Consumer attested.** Reutilizar snapshot firmado de Layer 2;
   asegurar orden firma → CDH → GCM mediante instrumentación y mantener las CLI
   anteriores intactas.
6. **Empaquetar y desplegar separado.** Imagen/entrypoint Layer 3 y recursos bajo
   `k8s/layer3/`, sin Secret AES y con referencias inmutables.
7. **Verificar positivos y negativos.** Éxito end-to-end, firma inválida sin
   petición, política/recurso denegados y AES incorrecta tras liberación.
8. **Cerrar con evidencia.** Suite completa, builds, inspección de imagen,
   escaneo acotado, informe, README/spec/plan/tareas/Notion y tag final solo si
   todos los criterios están demostrados.

Cada fase debe terminar con validación proporcional y un commit atómico
publicado en `layer3`. Los fallos de infraestructura no se ocultarán con mocks:
las pruebas unitarias validan el código; el criterio end-to-end exige el PC CoCo.

Checkpoint 13-09-2026: fase 1 completada para host/Kubernetes; fase 2 llega a
release Helm creada y RuntimeClass presente. Tras el reinicio se comprueba el
DaemonSet y se ejecuta el Pod mínimo antes de avanzar a Trustee.
