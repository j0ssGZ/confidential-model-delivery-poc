# Evidencia L2-05: Kubernetes con fixtures locales

Fecha de cierre: 12-09-2026. Base de código firmada `dce5e4d`, manifiestos y
scripts incorporados con este informe. Layer 2 sigue pendiente de cierre Hub.

## Pruebas

84 tests correctos en 3,22 s, incluidos 36 de Layer 1. Nuevas comprobaciones
del renderizador: namespace/imagen separados, firma obligatoria, cuenta sin
token, controles de contenedor y ausencia de hostPath en modo Hub.

Imagen construida con `uv sync --locked --no-dev`, contexto 27,75 kB:
`sha256:3562253389f22d03cfcaa829253b66ae13c090d57986ffc3c37e8147eeb40331`.
Imagen importada en los cinco Pods:
`sha256:6a7bd1279175893f1b58d177bdf693e14013058ad0b6ca4be3100367e456d21e`.
Son identificadores de objetos distintos (índice Docker e importación kind).

Clúster `kind-secure-ai-repro`, namespace `secure-ai-layer2`:

- `signed-fixture-positive-w5ksb`: salida 0, Complete en 15 s,
  `signature_verified=true model_loaded=true embedding_shape=(1, 384)`.
- `signed-fixture-tampered-bundle-ltmff`: salida 2, firma inválida.
- `signed-fixture-tampered-signature-lcgb5`: salida 2, firma inválida.
- `signed-fixture-wrong-public-rwnlg`: salida 2, firma inválida.
- `signed-fixture-wrong-aes-4rvm6`: salida 2, autenticación GCM fallida.

Firma inválida: `bundle signature verification failed`.
AES incorrecta: `bundle authentication failed`.
El orden se demuestra con tests instrumentados; los logs de Kubernetes por
sí solos no prueban que no hubo llamadas internas al descifrador.

## Material de prueba y confianza

Bundle SHA-256:
`eccee00558491a77db4857144d06714396c137850054399bf1b9fb664a068013`.
Firma SHA-256:
`4bbb8932bd6beba7326edc2f6340d987600d2b3af59a4da4dcc045cbef405953`.
Hashes locales y del nodo iguales. AES correspondiente:
`secrets/reproduction-20260911.bin`. Firma creada con la pareja operativa
local de Layer 2; la privada no se copió al nodo ni al namespace.

ConfigMap pública y Secret AES aprovisionados; ServiceAccount dedicada sin
token ni RoleBindings nuevos. `kubectl auth can-i update configmaps --as
system:serviceaccount:secure-ai-layer2:signed-consumer -n secure-ai-layer2`
devolvió `no`. Comprobación acotada, no auditoría completa de RBAC.

Inspección del contenedor con `--network none`: `image_payload_check=passed`;
sin `/app/{secrets,keys,models,artifacts,.git}` ni safetensors bajo `/app`.
No equivale a auditoría completa de capas de imagen.

Historial al commit `dce5e4d`: 133 blobs, dos AES conocidas. El escáner genérico
marcó un blob: `6fee8c7acc15ceb01978deb968f3b9719aedca2b`, correspondiente a
`signing.py` y a la cadena literal de cabecera PEM que valida el formato.
Se comprobó que el hash corresponde al archivo fuente: falso positivo,
no una clave publicada. Escaneo adicional de la privada Ed25519 conocida
(PEM completo, raw, hexadecimal y Base64) sobre esos 133 blobs: 0 hallazgos.
El alcance excluye secretos desconocidos, reflogs y referencias no descargadas.

## Pendiente real

No se publicó aún la pareja firmada en Hugging Face. No hay token disponible
en la biblioteca; el control del navegador quedó pendiente de permisos de
Accesibilidad/Grabación de pantalla. El ensayo local no sustituye ese requisito.
Falta publicar ambos archivos, fijar el commit, ejecutar los cinco Jobs Hub
y cerrar evidencias/documentación. No se crearon credenciales alternativas.

Se conservaron ambas capas, Jobs/logs, archivos de claves y fixtures. Comandos
reproducibles en [runbook Layer 2](../../k8s/layer2/README.md).
