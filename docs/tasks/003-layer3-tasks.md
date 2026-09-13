# Tareas 003: Layer 3

Estado: L3-05 completada; Consumer attested pendiente. [Spec](../specs/003-layer3.md),
[decisión](../decisions/007-layer3-attestation.md) y
[plan](../plans/003-layer3-plan.md).

- [x] L3-00: cerrar Layer 2 con tag anotado `layer2-complete` y crear/publicar
  la rama `layer3` desde ese commit.
- [x] L3-01: contrastar el tutorial histórico con las rutas oficiales actuales;
  elegir Helm como instalación candidata y registrar límites de `coco-dev`.
- [ ] L3-02: D1–D2 aprobadas y D4 aprobada solo para el recurso sintético; falta
  cerrar el contrato D3 y los controles D4 antes de registrar la AES real.
- [x] L3-03: verificar Ubuntu x86_64, KVM, containerd, Kubernetes y Helm; clúster
  kubeadm de un nodo y CNI fijada llegaron a `Ready`.
- [x] L3-04: CoCo chart 0.22.0/Kata 4.0.0 listo; dos Pods mínimos
  `kata-qemu-coco-dev` terminaron con salida 0. El segundo usa digest fijo;
  kernel guest 6.18.35, UID 10001 y `kata_smoke_ok=true`.
- [x] L3-05: Trustee v0.21.0 fijado; recurso sintético autorizado (KBS 200) y
  denegado (KBS 401) desde Pods Kata, con allow restaurada al terminar.
- [ ] L3-06: implementar y probar cliente/proveedor CDH sin secretos en logs.
- [ ] L3-07: integrar `cmdp-consumer-attested` conservando firma previa a clave y
  todas las regresiones Layer 1/2.
- [ ] L3-08: añadir imagen y manifiestos separados, sin Secret AES.
- [ ] L3-09: ejecutar positivo y negativos end-to-end desde Hub en CoCo.
- [ ] L3-10: auditar, documentar, sincronizar Notion y cerrar la capa con evidencia
  y tag, sin modificar los hitos anteriores.

D3 y el cierre de D4 para la AES real bloquean el código. L3-05 habilita la
siguiente aclaración, pero no acredita el Consumer integrado. No marcar checks por tests simulados si el
criterio exige infraestructura real. Evidencia del bootstrap en el
[informe 007](../reports/007-layer3-bootstrap.md), y runtime comprobado en el
[informe 008](../reports/008-layer3-runtime-smoke.md); Trustee sintético en el
[informe 009](../reports/009-layer3-trustee-synthetic.md). Reinicio del host pendiente.
