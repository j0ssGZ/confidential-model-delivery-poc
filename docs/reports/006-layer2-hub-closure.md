# Evidencia L2-06/L2-07: cierre desde Hugging Face Hub

Fecha: 12-09-2026. Rama `layer2`, base de código `5fb10ca`.

## Publicación y correspondencia

El operador publicó únicamente `minilm-l6-v2.bundle.enc` y
`minilm-l6-v2.bundle.enc.sig` en el repositorio público de artefactos. Revisión
inmutable:
[11eefa27b9f320b95263e1b00c09f2d2cbe36181](https://huggingface.co/J0ssGZ/confidential-model-delivery-artifacts/tree/11eefa27b9f320b95263e1b00c09f2d2cbe36181),
hija del commit histórico Layer 1
`c6d037b94a2f9e1072198a9c8de94540ada55edc`.

- Bundle local y descargado: SHA-256
  `eccee00558491a77db4857144d06714396c137850054399bf1b9fb664a068013`.
- Firma local y descargada: SHA-256
  `4bbb8932bd6beba7326edc2f6340d987600d2b3af59a4da4dcc045cbef405953`.
- `cmp` confirmó igualdad byte a byte de ambos archivos.
- La página del commit muestra dos cambios: bundle cifrado y firma binaria de
  64 bytes. No se publicaron claves ni modelo en claro.

Una carga local descargada desde esa revisión produjo:

```text
signature_verified=true model_loaded=true embedding_shape=(1, 384)
```

## Kubernetes desde Hub

Clúster `kind-secure-ai-repro`, namespace `secure-ai-layer2`, imagen local
`cmdp-consumer:layer2`. Los Pods descargaron bundle y firma desde la misma
revisión completa, sin `hostPath`.

- `signed-hub-positive-jqxtq`: Succeeded, salida 0; firma verificada y
  embedding finito `(1, 384)`.
- `signed-hub-tampered-bundle-268sn`: Failed, salida 2; firma inválida.
- `signed-hub-tampered-signature-hkznm`: Failed, salida 2; firma inválida.
- `signed-hub-wrong-public-l28j6`: Failed, salida 2; firma inválida.
- `signed-hub-wrong-aes-vwh42`: Failed, salida 2; autenticación GCM fallida.

Los tres rechazos de firma registraron `bundle signature verification failed`;
la AES incorrecta registró `bundle authentication failed`. Los tests
instrumentados son la evidencia del orden interno y confirman que una firma
inválida impide invocar el descifrado.

## Verificación y límites

La suite vigente pasó: 84 tests en 3,10 s, incluidos los 36 de Layer 1. El
escáner recorrió 170 blobs con las dos AES conocidas y produjo un hallazgo:
`6fee8c7acc15ceb01978deb968f3b9719aedca2b`, el archivo `signing.py` por su
cadena literal de cabecera PEM. La inspección confirmó que es el falso positivo
ya documentado. Una comprobación específica de la privada Ed25519 conocida
recorrió los mismos 170 blobs y obtuvo cero coincidencias con PEM, raw,
hexadecimal o Base64. Esta revisión es acotada: no demuestra ausencia de
secretos desconocidos, ni audita reflogs, permisos completos del Hub o
infraestructura de producción.

Los Pods hicieron descargas públicas sin token; la advertencia de rate limit no
afectó el resultado. La clave pública continúa en ConfigMap, la AES en Secret y
la privada Ed25519 solo en el entorno Producer. El host, la imagen y el operador
siguen dentro de la frontera de confianza. No hay TEE, política antirrollback
general ni revocación automática.

La publicación no modifica el commit Layer 1: crea una revisión nueva. Los Jobs,
Pods, ConfigMap, Secret, claves y temporales no se eliminan automáticamente.
