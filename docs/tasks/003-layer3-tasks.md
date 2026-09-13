# Tareas 003: Layer 3

Estado: L3-06–L3-10 comprobadas; tag `layer3-complete` publicado en `b0fb7b6`.
[Spec](../specs/003-layer3.md),
[decisión](../decisions/007-layer3-attestation.md) y
[plan](../plans/003-layer3-plan.md).

- [x] L3-00: cerrar Layer 2 con tag anotado `layer2-complete` y crear/publicar
  la rama `layer3` desde ese commit.
- [x] L3-01: contrastar el tutorial histórico con las rutas oficiales actuales;
  elegir Helm como instalación candidata y registrar límites de `coco-dev`.
- [x] L3-02: D3/D4 cerradas; audience administrativa 200/401 y política
  acotada sintética verificadas en Trustee real.
- [x] L3-03: verificar Ubuntu x86_64, KVM, containerd, Kubernetes y Helm; clúster
  kubeadm de un nodo y CNI fijada llegaron a `Ready`.
- [x] L3-04: CoCo chart 0.22.0/Kata 4.0.0 listo; dos Pods mínimos
  `kata-qemu-coco-dev` terminaron con salida 0. El segundo usa digest fijo;
  kernel guest 6.18.35, UID 10001 y `kata_smoke_ok=true`.
- [x] L3-05: Trustee v0.21.0 fijado; recurso sintético autorizado (KBS 200) y
  denegado (KBS 401) desde Pods Kata, con allow restaurada al terminar.
- [x] L3-06: proveedor Python CDH ejecutado dentro de Kata con fixture pública
  de 32 bytes; salida 0 y KBS 200, Job `attested-synthetic-4fmlj`.
- [x] L3-07: Consumer conserva el orden firma → clave → GCM; integración real
  con el modelo comprobada desde la revisión Hub fijada.
- [x] L3-08: imagen AMD64 publicada por digest y manifiestos separados,
  sin Secret AES ni token Kubernetes, comprobados mediante el Job sintético.
- [x] L3-09: positivo y negativos end-to-end desde Hub en CoCo; cada negativo
  falló en su frontera y fue seguido de un positivo restaurado.
- [x] L3-10: suite, build, auditoría, informes y sincronización/relectura de
  Notion terminadas; tag anotado publicado, sin tocar hitos anteriores.

D3/D4 cerradas; el Consumer integrado ya acredita infraestructura real. No se
marcaron checks con simulaciones: L3-09 usa Jobs Kata y KBS reales. Evidencia del bootstrap en el
[informe 007](../reports/007-layer3-bootstrap.md), y runtime comprobado en el
[informe 008](../reports/008-layer3-runtime-smoke.md); Trustee sintético en el
[informe 009](../reports/009-layer3-trustee-synthetic.md). Proveedor e imagen en
el [informe 011](../reports/011-layer3-cdh-image.md) y el
[informe 012](../reports/012-layer3-e2e.md). El reboot y la pérdida esperada del
almacén efímero están comprobados. La [auditoría 013](../reports/013-layer3-closure-audit.md)
cubre suite, historial e imagen. Notion principal, Layer 3 y presentación están
sincronizados y releídos; tag final publicado desde Git limpio. La preparación
posterior del ZIP y revisión editorial pertenece al plan 004.
