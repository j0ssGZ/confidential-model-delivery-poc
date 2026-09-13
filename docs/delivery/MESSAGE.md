# Mensaje propuesto de entrega

Enviar por el canal del contacto del challenge. Se ha omitido el ZIP por petición
del autor; el texto no presupone adjuntos. El hito técnico enlazado es inmutable;
la guía de entrega está en la rama `layer3`. Puede enlazarse también el commit
exacto del resumen de publicación. No se ha enviado ningún mensaje desde el agente.

**Asunto:** Entrega — Secure AI technical challenge — Jose Fanjul

Hola,

Os comparto mi solución al challenge Secure AI.

Código verificado:
https://github.com/j0ssGZ/confidential-model-delivery-poc/tree/layer3-complete

Guía del evaluador e instrucciones de reproducción:
https://github.com/j0ssGZ/confidential-model-delivery-poc/blob/layer3/docs/delivery/README.md

He implementado la Layer 1 obligatoria y las Layers 2 y 3 opcionales:
distribución AES-256-GCM, verificación Ed25519 y recuperación de la clave a través
de CDH/Trustee. El README y docs/delivery/README.md explican la arquitectura,
las decisiones y las instrucciones de reproducción.

El hito técnico está fijado en layer3-complete (b0fb7b6). La rama layer3
incorpora además la guía de entrega. La suite completa pasa 138 tests y
se documentan los positivos y negativos reales en Kubernetes/Kata.

Layer 3 usa kata-qemu-coco-dev y evidencia Sample: demuestra el protocolo y la
liberación de claves según política; no demuestra una TEE real ni protección
frente a un host malicioso.

Bundle cifrado y firma:
https://huggingface.co/J0ssGZ/confidential-model-delivery-artifacts/tree/11eefa27b9f320b95263e1b00c09f2d2cbe36181

El paquete no incluye claves ni credenciales. Podéis probar con una pareja
propia siguiendo la guía; para reproducir el artefacto publicado podemos
coordinar la AES y la pública de confianza por un canal independiente.

Quedo disponible para presentar el flujo, las decisiones y sus límites.

Un saludo,
Jose Fanjul
