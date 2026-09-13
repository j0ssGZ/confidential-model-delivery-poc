# Tareas 003: Layer 3

Estado: aclaración. [Spec](../specs/003-layer3.md),
[decisión](../decisions/007-layer3-attestation.md) y
[plan](../plans/003-layer3-plan.md).

- [x] L3-00: cerrar Layer 2 con tag anotado `layer2-complete` y crear/publicar
  la rama `layer3` desde ese commit.
- [x] L3-01: contrastar el tutorial histórico con las rutas oficiales actuales;
  elegir Helm como instalación candidata y registrar límites de `coco-dev`.
- [ ] L3-02: D1 aprobada con evidencia y D2 parcialmente validada; falta aprobar
  Trustee, contrato del Consumer y política.
- [x] L3-03: verificar Ubuntu x86_64, KVM, containerd, Kubernetes y Helm; clúster
  kubeadm de un nodo y CNI fijada llegaron a `Ready`.
- [ ] L3-04: CoCo chart 0.22.0 desplegado y RuntimeClass creada; falta esperar el
  DaemonSet y arrancar un Pod mínimo con
  `kata-qemu-coco-dev`.
- [ ] L3-05: desplegar Trustee fijado y demostrar recurso sintético autorizado y
  denegado desde una VM Kata.
- [ ] L3-06: implementar y probar cliente/proveedor CDH sin secretos en logs.
- [ ] L3-07: integrar `cmdp-consumer-attested` conservando firma previa a clave y
  todas las regresiones Layer 1/2.
- [ ] L3-08: añadir imagen y manifiestos separados, sin Secret AES.
- [ ] L3-09: ejecutar positivo y negativos end-to-end desde Hub en CoCo.
- [ ] L3-10: auditar, documentar, sincronizar Notion y cerrar la capa con evidencia
  y tag, sin modificar los hitos anteriores.

D2–D4 bloquean el código. L3-04 bloquea Trustee; L3-05 bloquea afirmar que el
Consumer integrado es reproducible. No marcar checks por tests simulados si el
criterio exige infraestructura real. Evidencia del bootstrap en el
[informe 007](../reports/007-layer3-bootstrap.md).
