# Decisión 001: selección del modelo

- **Estado:** cerrada.
- **Ámbito:** Layer 1.
- **Decisión:** usar `sentence-transformers/all-MiniLM-L6-v2` en la revisión
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.

## Contexto

Layer 1 debe demostrar el flujo seguro de distribución: descargar un modelo,
cifrarlo, publicarlo, recuperarlo en Kubernetes, descifrarlo y cargarlo solo
desde los archivos recuperados. El challenge propone explícitamente un BERT
pequeño y no requiere generación de texto.

El modelo elegido tiene licencia Apache-2.0, arquitectura BERT encoder y
aproximadamente 22,7 millones de parámetros. Se usará `sentence-transformers`
como librería de carga y se preferirá `model.safetensors` como formato de
pesos.

## Justificación

MiniLM mantiene la PoC pequeña, rápida y reproducible en CPU/ARM64. Proporciona
una carga funcional representativa sin añadir el coste de un modelo generativo,
que no mejora el objetivo evaluado por el challenge.

La revisión queda fijada a
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41` para que producer y consumer
trabajen sobre una entrada identificable y reproducible.

## Verificación funcional y restricciones de carga

El consumer generará un embedding para un texto fijo y comprobará que el
resultado tiene shape `(1, 384)` y que todos sus valores son finitos. Esta
comprobación aporta evidencia de carga y ejecución, no solo de descarga o
descifrado.

La carga deberá usar únicamente el directorio descifrado, sin red, sin caché
previa y sin `trust_remote_code`. Si falta cualquier archivo, el consumer debe
fallar en vez de obtenerlo desde Hugging Face u otra ubicación.

## Alternativas descartadas

- **`HuggingFaceTB/SmolLM2-135M`:** es generativo, pero añade peso y consumo
  sin mejorar el objetivo del flujo seguro de distribución.
- **`prajjwal1/bert-tiny`:** es más ligero, pero menos representativo y tiene
  una distribución de pesos menos conveniente para esta PoC.
- **`intfloat/e5-small-v2`:** es válido, pero introduce convenciones de
  `query`/`passage` que no aportan al challenge.

## Consecuencias

La selección del modelo deja de bloquear la implementación. Las demás
decisiones abiertas en la spec de Layer 1 continúan pendientes y mantienen
bloqueada la fase de implementación.
