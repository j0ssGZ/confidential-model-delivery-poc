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

## Requisito permanente de cierre y sincronización

Se aplica a todas las tareas del proyecto, en todas las sesiones. Antes de
declarar una tarea terminada, revisar y actualizar los documentos afectados:

- Spec y decisiones: requisitos, alcance, comportamiento y límites reales.
- Plan y tareas: estados y checks respaldados por evidencia concreta.
- README: comandos reproducibles, entradas, resultados esperados y errores.
- Informes: fecha, commit, pruebas ejecutadas y resultados, sin secretos.
- Notion principal: https://app.notion.com/p/3d778dc87e9281f7b4dbfc7275d6a141
- Notion defensa/flujo: https://app.notion.com/p/3d878dc87e9281f295faee6ae00005e3

La spec gobierna el alcance; el código y las pruebas prueban el comportamiento.
Si difieren, registrar la discrepancia y resolverla, nunca copiar garantías sin
comprobarlas. Actualizar primero el contrato cuando cambie el comportamiento.
No confundir implementado, probado localmente, integrado y reproducido desde
cero. Mantener como históricos los resultados que no se hayan repetido.
No marcar ensayos personales, auditorías completas o capas opcionales sin
evidencia. No añadir frases humorísticas del chat a los entregables.

Leer Notion antes de editar y volver a leer después de cambios estructurales;
comprobar enlaces, subpáginas, checks y bloques Mermaid. Si Notion no está
accesible, registrar el pendiente exacto y comunicarlo: la sincronización sigue
abierta, no se omite silenciosamente ni impide avanzar con trabajo independiente.

Cada cierre debe indicar qué se validó, qué documentos se sincronizaron y qué
queda pendiente. Para documentos no afectados, basta justificar que no cambian;
no crear cambios cosméticos ni repetir pruebas caras sin motivo. Hacer commits
pequeños y publicarlos según la autorización vigente del usuario. Esta norma
no autoriza cambios de alcance ni divulgación de secretos.

## Ciclo SDD

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

Las specs vigentes son [`docs/specs/001-layer1.md`](docs/specs/001-layer1.md),
[`docs/specs/002-layer2.md`](docs/specs/002-layer2.md) y, en la rama `layer3`,
[`docs/specs/003-layer3.md`](docs/specs/003-layer3.md). Las decisiones pendientes
de la capa activa bloquean su implementación hasta ser resueltas.
