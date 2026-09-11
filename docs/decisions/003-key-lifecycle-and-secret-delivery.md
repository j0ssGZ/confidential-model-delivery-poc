# Decisión 003: ciclo de vida y entrega de la clave

- **Estado:** cerrada.
- **Ámbito:** Layer 1.
- **Decisión:** usar una clave cruda aleatoria de 32 bytes generada por el
  producer, conservada localmente fuera de Git y entregada al consumer mediante
  un Kubernetes Secret montado como archivo de solo lectura.

## Flujo acordado

1. El producer genera criptográficamente una clave de 32 bytes y la guarda en
   `secrets/model-key.bin` con permisos `0600`.
2. El producer recibe esa ruta como parámetro. No accede a la API de
   Kubernetes y no escribe la clave en la imagen, el bundle, manifiestos
   versionados, variables de entorno ni logs.
3. Una operación local de despliegue crea o actualiza el Secret
   `model-decryption-key` en el namespace `secure-ai-poc`, con la entrada
   `key`.
4. El consumer monta la entrada como archivo de solo lectura en
   `/var/run/secrets/model-delivery/key` y lee de ahí exactamente los 32 bytes.

## Rotación

La clave está ligada al bundle que cifra. Para rotarla se genera una clave
nueva, se vuelve a cifrar y publicar el bundle y se actualiza el Secret. La
clave nueva no puede descifrar el bundle anterior.

## Motivo

El Secret montado como archivo satisface el requisito explícito de Layer 1 y
reduce exposiciones accidentales habituales de las variables de entorno. La
separación entre producer y la operación de despliegue evita conceder al
producer permisos innecesarios contra Kubernetes.

## Alternativas descartadas

- **Variable de entorno:** es válida técnicamente, pero puede aparecer con más
  facilidad en diagnósticos, volcados o configuraciones derivadas.
- **Clave dentro de la imagen o un manifiesto versionado:** expone el secreto
  a registros de imágenes o al historial de Git; queda prohibida.
- **Acceso del producer a la API de Kubernetes:** amplía privilegios sin ser
  necesario para cifrar y publicar el artefacto.
- **Gestor externo de claves o attestation:** queda fuera de Layer 1; es parte
  del alcance opcional de Layer 3.

## Límite de seguridad

Kubernetes y el host forman parte de la frontera de confianza de Layer 1. Un
administrador suficientemente privilegiado puede acceder al Secret o al
workload; esta decisión no afirma confidential computing ni protege frente a
ese actor.

## Consecuencias

La gestión de la clave deja de bloquear Layer 1. Siguen abiertas el destino y
la autenticación de Hugging Face, además de la ejecución del consumer en
Kubernetes; por ello la implementación continúa bloqueada.
