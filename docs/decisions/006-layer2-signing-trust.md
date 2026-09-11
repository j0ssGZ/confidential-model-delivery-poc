# Decisión 006: firma y confianza de la clave pública

Estado: D1–D4 aprobadas por Jose el 11-09-2026. Diseño, aún no implementado.
Contrato: [spec Layer 2](../specs/002-layer2.md).

## ConfigMap explicado para la defensa

Un ConfigMap guarda configuración no secreta como pares nombre/valor y puede
montarla como archivos en un Pod. No cifra su contenido. Referencia:
[ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/).

Nuestro diseño: el operador toma `keys/signing-public.pem`, crea el objeto
`model-signing-public-key` con entrada `public.pem`, y el Job la monta en
`/etc/model-signing/public.pem`. Consumer recibe esa ruta y verifica la firma.
Es un recorrido previsto, no un despliegue ya realizado.

Tres piezas diferentes: privada Ed25519 en el equipo que firma; pública
Ed25519 en ConfigMap para comprobar firmas; clave AES en Secret para descifrar.
La pública no permite ni firmar ni descifrar el modelo.

## Por qué la pública necesita protección

La analogía útil es una muestra de sello auténtico: cualquiera puede verla,
pero no debe poder reemplazar la muestra por la suya. Si un atacante sustituye
la pública confiada, puede hacer pasar sus propias firmas por válidas.
Montar el archivo de solo lectura impide escribir por ese montaje; no impide
que una identidad autorizada cambie el objeto mediante la API.

La integridad depende de controlar quién puede modificar ConfigMap, Job,
imagen y permisos. RBAC permite limitar acciones sobre recursos; los permisos
efectivos deben comprobarse en el despliegue, no inferirse por el nombre del
objeto. [RBAC oficial](https://kubernetes.io/docs/reference/access-authn-authz/rbac/).
El proceso consume un archivo y no necesita consultar la API de Kubernetes.
No se atribuye al laboratorio una auditoría RBAC que todavía no se ha realizado.

## Alternativas defendibles

- **ConfigMap — elegida:** separa la confianza configurada por el operador
  de la imagen. Encaja con nuestra frontera de confianza y facilita cambiar
  la pública sin reconstruir el programa. Exige cuidar permisos y rotación.
- **Pública dentro de la imagen:** buena opción para una entrega autocontenida
  donde el evaluador fije el digest de imagen. Cambiar la pública requiere
  otra imagen; la confianza se traslada al proceso de construcción y entrega.
- **Secret con la pública:** funciona y sería razonable si una organización
  ya administra todo material de claves mediante ese flujo. La pública no
  requiere confidencialidad; el objeto Secret no demuestra quién la aprobó.
  Los Secrets están orientados a datos sensibles y el cifrado de etcd requiere
  configuración: [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/).
- **Pública descargada con el bundle:** solo defendible con una raíz de
  confianza independiente, por ejemplo una huella esperada fijada por el
  operador. Sin ella, el atacante puede sustituir clave, firma y bundle.
- **ConfigMap inmutable/versionado:** alternativa útil para evitar cambios
  accidentales. Kubernetes permite `immutable: true`, pero se puede eliminar
  y recrear con permisos suficientes. Rotar mediante otro nombre y un Job
  nuevo hace explícita la transición. No se promete esa modalidad como
  implementada; la decisión actual es ConfigMap dedicado.

Estas valoraciones son razonamiento de diseño para esta PoC, no una
clasificación universal de seguridad.

## Las otras decisiones y sus alternativas

Ed25519 reutiliza la dependencia criptográfica existente. RSA-PSS sería
defendible por interoperabilidad con sistemas que ya lo emplean; para este
challenge no tenemos ese requisito. HMAC no resuelve la separación buscada:
los verificadores con el secreto también podrían crear autenticadores.

PEM identifica el formato y tipo de clave; raw es más compacto, pero facilita
confundir archivos de 32 bytes con AES. La privada sin contraseña simplifica
la ejecución local automatizada; una PEM cifrada añade gestión de contraseña
y un KMS/HSM añadiría infraestructura. Es un compromiso explícito de PoC.

La CLI firmada dedicada hace obligatoria su política; un selector en la CLI
única también es defendible si sus combinaciones y fallos se validan. Conservar
ambas CLI permite repetir Layer 1, pero no impide que un administrador cambie
el comando del Job: seguimos confiando en quien despliega.

## Respuesta oral

«Uso ConfigMap porque la clave pública se puede conocer, pero su origen debe
ser fiable. La aprovisiona el operador; no acepto una clave sustituible junto
al bundle. La AES permanece en Secret y la privada de firma en el Producer.
La alternativa de incluir la pública en la imagen también es válida; elegí
configuración separada para facilitar la rotación sin reconstruir.»
