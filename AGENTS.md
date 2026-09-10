# Norma de desarrollo del challenge

## Contexto del proyecto

- **Nombre:** Confidential Model Delivery PoC.
- Es el technical challenge de Secure AI de Capacity.
- Layer 1 es obligatoria; Layer 2 y Layer 3 son opcionales.
- Repositorio público:
  <https://github.com/j0ssGZ/confidential-model-delivery-poc>.
- Flujo obligatorio: Specification → Clarification → Plan → Tasks →
  Implementation → Verification.
- Las decisiones importantes pendientes bloquean la implementación.
- Nunca deben publicarse tokens, claves, credenciales, modelos descargados ni
  artefactos locales.
- `README.md`, las specs y el comportamiento real deben permanecer
  sincronizados.

## Forma de trabajo

Este repositorio usa Specification-Driven Development durante todo el
challenge. La documentación, el plan y la implementación deben evolucionar
juntos; no se programa contra supuestos que todavía estén pendientes de
decisión.

El ciclo obligatorio es:

1. **Specification:** registrar requisitos, alcance, amenazas, decisiones y
   criterios de aceptación.
2. **Clarification:** resolver conmigo las decisiones importantes antes de
   convertirlas en trabajo técnico.
3. **Plan:** diseñar pasos pequeños y verificables.
4. **Tasks:** dividir el plan en tareas antes de programar.
5. **Implementation:** implementar únicamente lo aprobado.
6. **Verification:** validar los criterios de aceptación y guardar evidencias.

No debe comenzar la implementación mientras existan decisiones importantes
pendientes. La spec de cada capa es la fuente del alcance; `README.md` debe
resumir el estado y enlazarla, y el comportamiento real debe mantenerse
sincronizado con ambos. Si una decisión, requisito o comportamiento cambia,
actualiza primero la documentación correspondiente y deja constancia de la
verificación.

Los commits deben ser pequeños, atómicos y describir una única intención. Cada
cambio debe incluir una validación proporcional al riesgo y guardar evidencia
cuando forme parte de los criterios de aceptación. La documentación y la
implementación no deben atribuir a la PoC garantías de seguridad que realmente
no proporciona.

Para Layer 1, la spec vigente es
[`docs/specs/001-layer1.md`](docs/specs/001-layer1.md). Sus decisiones
pendientes bloquean la implementación del pipeline hasta ser resueltas.
