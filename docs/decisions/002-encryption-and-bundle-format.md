# Decisión 002: cifrado y formato del bundle

- **Estado:** cerrada.
- **Ámbito:** Layer 1.
- **Decisión:** usar AES-256-GCM sobre un TAR determinista sin compresión, en
  el formato binario v1 descrito en este documento.

## Cifrado

El producer generará una clave aleatoria de 32 bytes y un nonce aleatorio de
12 bytes para cada cifrado. Cifrará el TAR completo con AES-256-GCM mediante la
librería `cryptography`. El tag de autenticación tendrá 16 bytes y será el que
produzca AES-GCM.

Está prohibido reutilizar una combinación de clave y nonce. La implementación
deberá tratar esa combinación como única incluso si se vuelve a cifrar el mismo
payload.

## Empaquetado determinista

El plaintext será un TAR sin compresión. Para que su representación sea
determinista, sus archivos se ordenarán y tendrán timestamps, UID y GID
normalizados. Todas las rutas serán relativas.

Antes de escribir cualquier archivo durante la extracción, el consumer validará
el conjunto completo de entradas. Rechazará rutas absolutas, rutas con path
traversal, dispositivos y enlaces. No se aceptarán entradas que puedan escapar
del directorio de extracción ni representar tipos de archivo no regulares.

## Bundle autocontenido v1

El nombre previsto del artefacto es `minilm-l6-v2.bundle.enc`.

El formato binario v1 es, en este orden:

1. Magic ASCII de 8 bytes: `CMDP1ENC`.
2. Longitud de la metadata: `uint32` big-endian.
3. Metadata JSON canónica codificada en UTF-8.
4. Ciphertext seguido por el tag de autenticación producido por AES-GCM.

La metadata contiene exactamente los campos de esta versión:

- `schema_version`
- `algorithm`
- `source_model`
- `source_revision`
- `payload_format`
- `plaintext_sha256`
- `nonce_b64`

Se serializa con claves ordenadas, separadores compactos y sin timestamp ni
otros campos variables innecesarios. Esto proporciona una representación
reproducible de la metadata sin incorporar información de ejecución al bundle.

## Autenticidad e integridad

El AAD de AES-GCM es la concatenación de magic, longitud codificada y los bytes
exactos de la metadata. Por tanto, el tag autentica la cabecera y metadata además
del ciphertext. El `plaintext_sha256` se comprobará después del descifrado antes
de aceptar el payload.

Modificar la cabecera, metadata, nonce, modelo, revisión, hash, ciphertext o
tag debe hacer que el consumer rechace el bundle y no extraiga ni cargue el
modelo. Los errores de parseo de cabecera o metadata también se consideran
rechazos antes de cualquier escritura.

## Limitación aceptada

La API `AESGCM` procesará el TAR completo en memoria. Es aceptable para MiniLM
y para esta PoC. Para modelos grandes se usaría cifrado autenticado por bloques
o streaming, con nonces derivados de forma segura y autenticación por bloque.

## Alternativas descartadas

- **AES-CBC + HMAC:** añade piezas y aumenta el riesgo de composición
  incorrecta.
- **Fernet:** es válido, pero oculta decisiones relevantes y añade su propio
  formato.
- **ChaCha20-Poly1305:** es una alternativa AEAD válida, pero AES-GCM es más
  común en infraestructura empresarial y servicios de gestión de claves.
- **tar.gz:** aporta poca ganancia sobre `safetensors` y añade tiempo y
  variabilidad.

## Consecuencias

La decisión de cifrado, formato del artefacto y empaquetado deja de bloquear la
implementación. Siguen abiertas la gestión de la clave, el destino y la
autenticación de Hugging Face, y la ejecución en Kubernetes; por ello la
implementación de Layer 1 continúa bloqueada.
