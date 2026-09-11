# Layer 2: firma del bundle cifrado

Estado: borrador para aclaración. No implementado. Las decisiones D1–D4
requieren confirmación de Jose antes de implementar.

## Alcance y base aprobada

Añadir firma asimétrica y verificación previa al descifrado de Layer 1.
Mismo repositorio, rama `layer2`; etiqueta `layer1-complete` sobre
`103b29c4cd7fddb8cbb364797d2921a554a9897a`, ambas publicadas.
La spec de Layer 1 y sus evidencias se conservan. Layer 3 queda fuera.

## Amenaza y confianza

Un atacante puede sustituir bundle y firma en el transporte o almacenamiento.
Puede incluso conocer la clave AES compartida, pero no la privada de firma.
El Consumer confía en la clave pública aprovisionada por el operador y debe
rechazar lo que no corresponda a ella. Host, imagen, código y operador siguen
dentro de la frontera de confianza. Si el atacante sustituye también esa clave
pública o el programa verificador, esta capa no ofrece la garantía prevista.

## Decisiones propuestas, pendientes de confirmación

- **D1 — Algoritmo y bytes:** Ed25519 mediante `cryptography`; firmar todos los
  bytes exactos del bundle v1, incluida cabecera, metadata y ciphertext/tag.
  Firma separada binaria de 64 bytes: `minilm-l6-v2.bundle.enc.sig`.
  No modificar el formato AES ni firmar solo el hash textual de metadata.
- **D2 — Claves:** privada PEM PKCS8 en `secrets/signing-private.pem`, creada
  exclusivamente con permisos 0600; pública PEM SubjectPublicKeyInfo en
  `keys/signing-public.pem`. Privada sin contraseña para esta PoC automatizada,
  protegida por permisos y custodia local; no equivale a un KMS. El operador
  genera las claves; el Producer las lee. Nunca sobrescribir claves existentes.
- **D3 — Confianza pública:** ConfigMap dedicado creado por el operador desde
  su archivo público de confianza y montado de solo lectura. La clave pública
  no se obtiene del mismo origen sustituible que el bundle. No necesita secreto;
  necesita integridad. Permite cambiarla sin reconstruir la imagen. El nombre
  propuesto del ConfigMap es `model-signing-public-key`.
- **D4 — Interfaz:** nuevo entrypoint `cmdp-consumer-signed` que exige clave
  pública y firma; conservar `cmdp-consumer` para Layer 1. Producer incorpora
  opción explícita de firma. No permitir fallback sin firma en el entrypoint
  firmado. Manifiestos Layer 2 separados bajo `k8s/layer2/`, con nombres de
  Jobs e imagen distintos para no reemplazar la demo anterior.

Alternativas: clave pública dentro de la imagen (requiere reconstrucción para
rotar), selector de modo en una única CLI (más fácil omitir el modo firmado),
claves binarias raw (más fácil confundirlas con AES). Se propone PEM para
identificar el tipo de clave y una CLI dedicada para hacer explícita la política.

## Contrato propuesto

El Producer firma el mismo bundle que entrega; un fallo de firma no debe
presentarse como una entrega firmada completa. El operador publica bundle y
firma en un mismo commit nuevo de Hugging Face y fija su revisión completa.
La referencia histórica de Layer 1 permanece intacta. Antes de publicar una
firma del bundle existente se comprueba su correspondencia con la fuente local
confiada; no se firma ciegamente una descarga no validada.

Consumer firmado: descargar ambos archivos de la misma revisión o recibir
ambos localmente → leer bytes → verificar con clave pública aprovisionada →
descifrar esos mismos bytes ya verificados → validar identidad → extraer →
cargar → comprobar embedding → limpiar el temporal propio. No releer el bundle
desde disco entre verificación y descifrado: evitar sustitución entre fases.
Errores controlados, salida no cero, sin claves ni contenido del modelo en logs.

## Criterios de aceptación

1. Firma y claves correctas: embedding finito `(1, 384)`.
2. Bundle o firma manipulados, firma ausente/truncada o clave pública incorrecta:
   rechazo antes de invocar descifrado, extracción o carga. Comprobar ese orden
   con instrumentación en tests; un mensaje de error no basta.
3. Firma válida y clave AES incorrecta: verificación correcta y rechazo GCM.
4. El Consumer descifra exactamente los bytes verificados, aunque cambie el
   archivo original entre fases.
5. CLI firmada rechaza entradas incompletas y no ofrece fallback a Layer 1.
6. Las 36 pruebas actuales de Layer 1 continúan pasando, junto a regresiones
   nuevas de firma, claves, publicación local y limpieza.
7. Demo Kubernetes positiva y negativos de firma alterada, bundle alterado y
   clave pública incorrecta, sin modificar los recursos positivos de Layer 1.
8. Privada ausente de Git, imagen, Hub y logs; revisión con alcance explícito.
9. README, spec, plan, tareas, Notion y evidencias sincronizados antes del cierre.

## Límites y referencias

Firma no significa calidad del modelo, protección del host ni confidencialidad.
Una firma válida antigua no demuestra actualidad: no hay política general de
antirrollback ni revocación automática. La clave AES sigue separada y en Secret.
Se mantiene el procesamiento completo del bundle en RAM de esta PoC.

- [API oficial Ed25519](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/).
  Verificar compatibilidad con la versión fijada en `uv.lock` al implementar;
  la documentación latest puede describir una versión posterior.
- [Layer 1](001-layer1.md).
- [Notion Layer 2](https://app.notion.com/p/3d878dc87e92819aaedbe32909c3885a).
- [Plan propuesto](../plans/002-layer2-plan.md).
- [Tareas propuestas](../tasks/002-layer2-tasks.md).
