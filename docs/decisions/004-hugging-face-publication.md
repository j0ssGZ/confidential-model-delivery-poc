# Decisión 004: publicación del bundle en Hugging Face

- **Estado:** cerrada.
- **Ámbito:** Layer 1.
- **Decisión:** publicar únicamente el bundle cifrado y sus metadatos no
  sensibles en el repositorio público dedicado
  `j0ssGZ/confidential-model-delivery-artifacts`.

## Publicación y consumo

El producer publicará `minilm-l6-v2.bundle.enc` y los metadatos no sensibles
acordados. Nunca publicará claves, tokens, archivos de modelo en claro ni
directorios descifrados.

La publicación requerirá un token de Hugging Face local con el privilegio
mínimo de escritura para este repositorio. El token se mantendrá fuera de Git,
de las imágenes y de los manifiestos versionados.

Después de publicar, se registrará el commit exacto que contiene el bundle.
El consumer descargará por esa revisión inmutable, en lugar de usar `main`,
`latest` u otra referencia mutable.

## Motivo

Un repositorio público simplifica la demostración de descarga reproducible y
no debilita el objetivo de confidencialidad de Layer 1: el contenido publicado
permanece cifrado y la clave se distribuye por Kubernetes. Separarlo en un
repositorio dedicado evita mezclar artefactos descargables con código y
documentación.

## Alternativas descartadas

- **Repositorio privado:** podría aportar control de acceso adicional, pero
  añade autenticación al consumer y no sustituye el cifrado exigido por el
  challenge.
- **Usar `main` o `latest`:** impediría reproducir exactamente el artefacto
  validado por Kubernetes.
- **Publicar el modelo en claro:** incumple el objetivo de distribución
  cifrada de Layer 1.

## Límite de seguridad

La visibilidad pública no proporciona ni elimina garantías criptográficas. La
protección depende de que la clave AES-GCM permanezca fuera del repositorio y
del acceso no autorizado al Secret. Un repositorio público también expone los
metadatos publicados, por lo que estos no deben contener información sensible.

## Consecuencias

El destino, visibilidad y autenticación de Hugging Face dejan de bloquear
Layer 1. Sigue abierta la decisión de ejecución del consumer en Kubernetes;
la implementación continúa bloqueada hasta cerrarla.
