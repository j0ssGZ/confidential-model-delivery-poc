# Plan 002: Layer 2

Estado: completado. D1–D4 de la [spec](../specs/002-layer2.md), módulo de
claves/firma, integración, fixtures locales y los cinco recorridos Hub están
verificados. Cierre y revisión inmutable en el informe 006.

1. Cerrar decisiones con Jose y actualizar spec/Notion.
2. Añadir módulo de claves y firma, generación exclusiva y tests criptográficos.
3. Integrar firma opcional en Producer y Consumer firmado obligatorio; reutilizar
   descifrado sobre bytes ya verificados, evitando una segunda lectura del archivo.
4. Añadir imagen/Jobs separados y aprovisionamiento de clave pública confiada.
5. Publicar firma y bundle en nueva revisión, conservar Layer 1 y probar el
   recorrido completo y negativos sin modificar sus recursos.
6. Registrar evidencia con commit, revisión, pruebas y límites; actualizar
   README, specs, tareas y las páginas de Notion afectadas.

Cada paso tiene commit pequeño, validación proporcional y publicación en
`layer2`. Layer 2 permanece en su rama; `main` continúa como Layer 1 canónica.
