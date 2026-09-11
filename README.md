# Confidential Model Delivery PoC

Challenge de Capacity Secure AI. El repositorio sigue Specification-Driven
Development; las reglas están en [`AGENTS.md`](AGENTS.md).

## Estado

Layer 1 ha cerrado su especificación y clarificación; el siguiente paso es
preparar el plan y dividirlo en tareas verificables. La especificación, el
alcance, los criterios de aceptación, las amenazas y las decisiones quedan en
[`docs/specs/001-layer1.md`](docs/specs/001-layer1.md). La implementación no
comenzará hasta que el plan y las tareas estén documentados y aprobados.

Todavía no hay pipeline implementado ni artefactos publicados. `uv.lock` se
mantiene bajo control de Git para reproducibilidad; los entornos, secretos,
claves, cachés y artefactos locales se excluyen mediante `.gitignore`.
