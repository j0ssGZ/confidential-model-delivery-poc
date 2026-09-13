# Evidencia 012: Consumer Layer 3 end-to-end

Fecha: 13-09-2026. Rama `layer3`. Este informe cierra L3-07 y L3-09, pero no
L3-10 ni el tag final. El entorno es `secure-ai-node` tras reboot: Kubernetes,
`kata-qemu-coco-dev` y Trustee volvieron a `Ready`. El LocalFs de KBS, soportado
por `emptyDir`, perdió sus recursos; se restauró primero la fixture sintética.
Esto confirma la limitación de persistencia prevista en D4.

## Recurso y frontera de secretos

El operador comprobó localmente cuál de sus archivos privados de 32 bytes
corresponde al bundle firmado de la revisión Hub inmutable y registró ese mismo
material, sin imprimirlo, bajo `default/key/minilm-l6-v2` con el cliente KBS
oficial fijado. No se generó una AES, no se recifró/republicó el bundle, y no se
modificó la clave positiva histórica. El Job no monta Secret AES: usa ConfigMaps
públicos, una pública Ed25519 independiente, `/work` Memory y CDH local.

Una primera carga administrativa usó por error una AES válida asociada a otro
bundle local. La firma pasó y GCM la rechazó; se detuvo, se identificó el
emparejamiento correcto localmente y se sustituyó el recurso sin exponer valores.
No se cuenta ese diagnóstico como caso de aceptación. Demuestra que la firma
autentica el bundle, mientras que GCM también exige la AES exacta de ese bundle.

## Resultados reales

Todos los Jobs usan `kata-qemu-coco-dev` y la imagen inmutable
`docker.io/jfanjul/confidential-model-delivery-consumer-attested@sha256:5ec1d732edfb5cb7a2efcbcdfadbba4f310759f1cd1d0ca309d64f36ce2238b6`.

| Caso | Job / Pod | Resultado y frontera comprobada |
| --- | --- | --- |
| Firma manipulada | `attested-tampered-signature-v64dh` / `…-kz4ct` | Falló, salida 2: `bundle signature verification failed`; no emitió etapas CDH. Pod `10.244.0.45` no tiene petición KBS correlacionada. |
| Positivo restaurado | `attested-positive-mzk8j` / `…-cfrq9` | Salida 0; firma, petición/recuperación de clave y GCM pasaron; MiniLM devolvió `(1, 384)`. KBS: `10.244.0.46` → recurso clave HTTP 200. |
| Política/recurso denegado | `attested-denied-27nq9` / `…-zfndb` | Falló, salida 2 tras `signature_verified` y `key_requested`; error CDH, sin `key_retrieved` ni GCM. KBS: `10.244.0.47` → `default/test/denied` HTTP 401. |
| Positivo restaurado | `attested-positive-klmht` / `…-zgb4p` | Salida 0 con las cuatro etapas y embedding `(1, 384)`. |
| AES de prueba errónea | `attested-wrong-aes-4v9r2` / `…-mzxtt` | Falló, salida 2 tras `signature_verified`, `key_requested`, `key_retrieved`; `bundle authentication failed`, sin GCM completado/extracción/carga. KBS: `10.244.0.49` → `default/test/wrong-aes` HTTP 200. |
| Positivo final | `attested-positive-5xx5n` / `…-dtvmb` | Salida 0 con `signature_verified=true key_retrieved=true model_loaded=true embedding_shape=(1, 384)`. KBS: `10.244.0.50` → recurso clave HTTP 200. |

El positivo tras cada negativo evita confundir una denegación o fixture de prueba
con infraestructura rota. Los logs no contienen AES, tokens ni privada Ed25519.
El warning de descarga anónima de Hugging Face es una limitación de disponibilidad
por rate limit; no se usó ni expuso token HF.

## Interpretación defendible

La evidencia demuestra el orden exacto: firma válida → CDH/KBS → longitud de
clave → AES-GCM → extracción → carga. En particular, no es posible inferir una
petición de clave desde el negativo de firma, ni inferir descifrado desde el
negativo KBS. La política allowlist limita rutas y exige evidencia `Sample`, pero
Sample no identifica exclusivamente este código. `kata-qemu-coco-dev` demuestra
arquitectura, protocolo y liberación controlada por política; no una TEE real ni
confidencialidad frente a un host malicioso.

La auditoría de repositorio/historial/imagen, la repetición final de la suite y
la sincronización completa de documentación/Notion pertenecen aún a L3-10.
