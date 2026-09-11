# Confidential Model Delivery PoC

Challenge de Capacity Secure AI. El repositorio sigue Specification-Driven
Development; las reglas están en [`AGENTS.md`](AGENTS.md).

## Estado

Layer 1 está en implementación. La especificación, el alcance, los criterios
de aceptación, las amenazas y las decisiones quedan en
[`docs/specs/001-layer1.md`](docs/specs/001-layer1.md); el plan está en
[`docs/plans/001-layer1-plan.md`](docs/plans/001-layer1-plan.md) y el progreso
de tareas en [`docs/tasks/001-layer1-tasks.md`](docs/tasks/001-layer1-tasks.md).
T01 (fundación Python), T02 (bundle v1 y extracción segura) y T03 (producer
local), T04 (consumer aislado) y T05 (imagen y manifiestos de Kubernetes) están
completas; T06 (publicación inmutable en Hugging Face) también está completa y
T07 (recorrido positivo en kind), T08 (recorridos negativos integrados) y T09
(documentación y evidencia) están completas. El informe de estudio está en
[`docs/reports/001-layer1-final-report.md`](docs/reports/001-layer1-final-report.md).

El bundle cifrado está publicado; el recorrido integrado en Kubernetes sigue
pendiente. `uv.lock` se
mantiene bajo control de Git para reproducibilidad; los entornos, secretos,
claves, cachés y artefactos locales se excluyen mediante `.gitignore`.
