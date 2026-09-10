# Confidential Model Delivery PoC

Challenge de Capacity Secure AI. El repositorio sigue Specification-Driven
Development; las reglas están en [`AGENTS.md`](AGENTS.md).

## Estado

Layer 1 está en fase de especificación y clarificación. La especificación,
el alcance, los criterios de aceptación, las amenazas y las decisiones
pendientes están en [`docs/specs/001-layer1.md`](docs/specs/001-layer1.md).
La implementación permanece bloqueada hasta resolver las decisiones
importantes indicadas allí.

Todavía no hay pipeline implementado ni artefactos publicados. `uv.lock` se
mantiene bajo control de Git para reproducibilidad; los entornos, secretos,
claves, cachés y artefactos locales se excluyen mediante `.gitignore`.
