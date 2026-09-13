# Plan 003: Layer 3

Estado: host, Kubernetes, runtime CoCo y Trustee sintético comprobados
(L3-05). D3/D4 cerradas con audience y política acotada verificadas; proveedor
y Consumer implementados y probados unitariamente, según la
[decisión 007](../decisions/007-layer3-attestation.md). Contrato en la
[spec](../specs/003-layer3.md).

1. **Cerrar entorno y versiones.** Inspeccionar el PC Ubuntu sin mostrar datos
   sensibles, aprobar host y fijar Kubernetes/containerd/Helm/CoCo/Trustee.
2. **Validar infraestructura mínima.** Instalar CoCo por Helm, comprobar la
   RuntimeClass y arrancar un Pod inocuo con `kata-qemu-coco-dev`.
   Ensayo L3-04: `k8s/layer3/runtime-smoke.yaml`, BusyBox 1.37.0, UID 10001,
   raíz de solo lectura y sin token Kubernetes. Debe terminar con salida 0 y
   `kata_smoke_ok=true`; comparar el kernel guest con el host como evidencia
   adicional. No solicita recursos a CDH ni valida attestation todavía.
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

Checkpoint 13-09-2026: fases 1–3 completadas. Trustee v0.21.0 está fijado al
commit compatible con CoCo 0.22.0 y el recurso sintético pasó allow/deny desde
Pods Kata, incluida la decisión HTTP 200/401 observada en KBS y la restauración
de allow. La prueba no incluyó reinicio del host ni una TEE real. Siguiente fase:
ejecutar el proveedor Python sintético en Kata, seguido de AES original y E2E.
D3/D4 se cerraron: admin 200/401, política Sample acotada 200/401, suite 123 tests.

Checkpoint posterior: proveedor Python comprobado en Kata con fixture de 32
bytes, imagen por digest y manifiestos separados; suite 138 tests. Se ajustaron
timeouts de creación guest con evidencia y backup, sin cambiar versiones.
Antes de continuar se revalidará el reinicio que anunció el operador. No se
aprovisionó la AES original ni se ejecutó aún el Consumer E2E con MiniLM.
Siguiente: comprobar servicios/política/fixture tras reboot, recuperar el último
checkpoint si es necesario, luego fases 7–8 con la AES original.
