# Tareas 002: Layer 2

Estado: completada y verificada. [Spec](../specs/002-layer2.md) y
[plan](../plans/002-layer2-plan.md).

- [x] L2-00: rama publicada y Layer 1 preservada por etiqueta.
- [x] L2-01: redactar borrador de spec, decisiones y criterios de aceptación.
- [x] L2-02: D1–D4 aprobadas por Jose; contrato y alternativas en decisión 006.
- [x] L2-03: claves/firmas y pruebas de formato, fallos y no sobrescritura.
- [x] L2-04: Producer y Consumer firmado; orden verificación-descifrado,
  mismos bytes, errores y compatibilidad con Layer 1.
- [x] L2-05: imagen/Jobs y ConfigMap dedicado; cinco casos con fixtures locales.
- [x] L2-06: publicación inmutable, positivo y negativos Kubernetes.
- [x] L2-07: evidencias, revisión acotada de secretos y cierre documental/Notion.

L2-06 usa la revisión Hub `11eefa27b9f320b95263e1b00c09f2d2cbe36181`.
Los cinco Jobs descargaron la misma pareja: positivo salida 0; cuatro negativos
salida 2. L2-07 sincroniza la evidencia y documentación. Informe 006; 84 tests.

Evidencia L2-03: [informe 003](../reports/003-layer2-signing-module.md):
56 tests correctos (36 previos y 20 nuevos), cryptography 46.0.7.

Evidencia L2-04: 73 tests correctos; Producer firmado sobre MiniLM real y
Consumer firmado local con embedding finito `(1, 384)`. Informe 004.

Validación de L2-02: confirmación explícita de Jose, consulta de documentación
oficial de ConfigMaps, Secrets y RBAC, y sincronización de Notion. En ese
checkpoint aún no había ConfigMap de firma ni permisos verificados en el clúster.

Validación de L2-01: revisión del Consumer actual y referencias de la API
Ed25519; enlaces locales y `git diff --check`. No se cambió código ejecutable
ni se repitieron las pruebas de Layer 1 por este cambio documental.
