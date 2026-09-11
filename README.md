# Confidential Model Delivery PoC

Challenge de Capacity Secure AI. El repositorio sigue Specification-Driven
Development; las reglas están en [`AGENTS.md`](AGENTS.md).

## Estado

Layer 1 ha cerrado su especificación y clarificación; el siguiente paso es
aprobar el plan y las tareas verificables ya preparados. La especificación, el
alcance, los criterios de aceptación, las amenazas y las decisiones quedan en
[`docs/specs/001-layer1.md`](docs/specs/001-layer1.md); el plan está en
[`docs/plans/001-layer1-plan.md`](docs/plans/001-layer1-plan.md) y las tareas
en [`docs/tasks/001-layer1-tasks.md`](docs/tasks/001-layer1-tasks.md). La
implementación no comenzará hasta que plan y tareas estén aprobados.

Todavía no hay pipeline implementado ni artefactos publicados. `uv.lock` se
mantiene bajo control de Git para reproducibilidad; los entornos, secretos,
claves, cachés y artefactos locales se excluyen mediante `.gitignore`.
