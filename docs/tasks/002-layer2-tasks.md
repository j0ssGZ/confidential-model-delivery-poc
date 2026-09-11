# Tareas 002: Layer 2

Estado: preparación documental. [Spec](../specs/002-layer2.md) y
[plan propuesto](../plans/002-layer2-plan.md).

- [x] L2-00: rama publicada y Layer 1 preservada por etiqueta.
- [x] L2-01: redactar borrador de spec, decisiones y criterios de aceptación.
- [x] L2-02: D1–D4 aprobadas por Jose; contrato y alternativas en decisión 006.
- [x] L2-03: claves/firmas y pruebas de formato, fallos y no sobrescritura.
- [ ] L2-04: Producer y Consumer firmado; orden verificación-descifrado,
  mismos bytes, errores y compatibilidad con Layer 1.
- [ ] L2-05: imagen/Jobs y ConfigMap dedicado de clave pública.
- [ ] L2-06: publicación inmutable, positivo y negativos Kubernetes.
- [ ] L2-07: evidencias, revisión acotada de secretos y cierre documental/Notion.

L2-04 es el siguiente paso. Los checks de integración y verificación
permanecen abiertos hasta contar con pruebas.

Evidencia L2-03: [informe 003](../reports/003-layer2-signing-module.md):
56 tests correctos (36 previos y 20 nuevos), cryptography 46.0.7.

Validación de L2-02: confirmación explícita de Jose, consulta de documentación
oficial de ConfigMaps, Secrets y RBAC, y sincronización de Notion. No hay aún
ConfigMap de firma ni permisos verificados para Layer 2 en el clúster.

Validación de L2-01: revisión del Consumer actual y referencias de la API
Ed25519; enlaces locales y `git diff --check`. No se cambió código ejecutable
ni se repitieron las pruebas de Layer 1 por este cambio documental.
