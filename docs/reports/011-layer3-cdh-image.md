# Checkpoint 011: proveedor CDH real e imagen Layer 3

Fecha: 13-09-2026. Rama `layer3`; código del Consumer/imagen en `0581d0c`.
**L3-06 y L3-08 verificadas. Layer 3 no está cerrada:** AES real no aprovisionada,
Consumer del modelo E2E y negativos integrados pendientes. El operador anunció
que reiniciaría Ubuntu; se conserva este checkpoint para revalidarlo después.

## Resultado real

Job `attested-synthetic-4fmlj`, Pod `attested-synthetic-4fmlj-546qf`, IP
`10.244.0.34`, runtime `kata-qemu-coco-dev`. A las 13:18:26 UTC:

```text
cdh_python_synthetic_ok=true
GET /kbs/v0/resource/default/test/wrong-aes HTTP/1.1 -> 200
exit_code=0
```

El mismo módulo `cdh.retrieve_key()` de la imagen recuperó exactamente 32 bytes
desde `127.0.0.1:8006/cdh/resource/default/test/wrong-aes` y los comparó con la
fixture pública de 32 ceros. No se usó una respuesta simulada ni un cliente del
host. CDH/AA/KBC dentro de Kata pidieron el recurso a Trustee real.
Ver [resultado](evidence/011/attested-synthetic-4fmlj-result.json),
[log Consumer](evidence/011/attested-synthetic-4fmlj-consumer.log) y
[acceso KBS](evidence/011/attested-synthetic-4fmlj-kbs-access.log).

El verificador comprobó RuntimeClass, imagen por digest, raíz de solo lectura,
ausencia de volúmenes Secret/projected/hostPath y token Kubernetes deshabilitado.
Los manifiestos aplican UID/GID 10001, capabilities drop ALL y sin escalada.
La pública Ed25519 existente llegó mediante ConfigMap; otro ConfigMap contiene
únicamente repositorio y revisión HF. `/work` es un temporal Memory explícito.

Esto prueba recuperación sintética y empaquetado, **no** carga MiniLM, AES real
ni los negativos del Consumer final. La política continúa acotada a Sample y
rutas explícitas; no autentica exclusivamente la identidad de este workload.

## Incidencia de arranque diagnosticada y resuelta

1. `attested-synthetic-69ddx`: salida 128/StartError. Kata canceló
   `CreateContainer` exactamente a 60 s, antes de ejecutar Python.
2. `attested-synthetic-dwwz5`: con anotación Kata de 300 s, kubelet canceló a
   120 s. Salida 128, ninguna etapa Consumer ni petición de recurso.
3. `attested-synthetic-4fmlj`: tras ampliar el timeout de kubelet, la creación
   guest tardó aproximadamente 191 s y Python/CDH terminó correctamente.

Los fallos no cuentan como negativos de seguridad. Se conservaron sus Jobs y
los [resultados](evidence/011/attested-synthetic-dwwz5-result.json). Los registros
completos de Pods y logs se copiaron al Mac antes del reinicio anunciado, en
`/private/tmp/cmdp-l3-evidence-pre-reboot` y `/private/tmp/cmdp-l3-first-timeout`.
Son copias temporales adicionales; el resumen público de aceptación sí está en Git.

La anotación `io.katacontainers.config.runtime.create_container_timeout=300`
está soportada por el código oficial etiquetado Kata 4.0.0. El script
`layer3_kubelet_timeout.py` guardó la configuración original en
`/var/lib/kubelet/cmdp-kubelet-backup-7k0zyfo3/config.yaml`, cambió
`runtimeRequestTimeout: 0s` a `10m0s` y reinició únicamente kubelet. Nodo Ready;
KBS, AS y RVPS conservaron sus Pods y cero reinicios en esa comprobación.
No se cambió memoria, snapshotter, runtime ni versiones. No se habilitaron logs
debug ni consola guest. Fuente y justificación en [ADR 007](../decisions/007-layer3-attestation.md).

## Imagen, pruebas y auditoría del checkpoint

Imagen pública del operador, AMD64:
`docker.io/jfanjul/confidential-model-delivery-consumer-attested@sha256:5ec1d732edfb5cb7a2efcbcdfadbba4f310759f1cd1d0ca309d64f36ce2238b6`.
Publicada con tag `0581d0c`; el digest es la referencia de ejecución. ORAS en el
servidor verificó el índice anónimamente. El manifiesto AMD64 es
`sha256:83b3c5d191f9d936cdace7b26774c0d3883f4e92adcea7e1a03eefab9a02f609`.
358.245.992 bytes comprimidos según containerd; no modelo ni claves dentro.

Comandos ejecutados:

```sh
.venv/bin/pytest
git diff --check
docker build --platform linux/amd64 -f Dockerfile.consumer-attested -t cmdp-consumer-attested:0581d0c .
docker run --rm --platform linux/amd64 --network none --read-only \
  --tmpfs /work:rw,nosuid,nodev,size=256m,mode=1777 cmdp-consumer-attested:0581d0c --help
docker save -o /private/tmp/cmdp-consumer-attested-0581d0c.tar cmdp-consumer-attested:0581d0c
.venv/bin/python scripts/audit_layer3_image.py /private/tmp/cmdp-consumer-attested-0581d0c.tar \
  --known-secret secrets/model-key.bin --known-secret secrets/signing-private.pem
docker history --no-trunc cmdp-consumer-attested:0581d0c
docker tag cmdp-consumer-attested:0581d0c jfanjul/confidential-model-delivery-consumer-attested:0581d0c
docker push jfanjul/confidential-model-delivery-consumer-attested:0581d0c
```

Resultados: **138 tests pasan**, build y ayuda con `/work` escribible pasan,
`git diff --check` sin errores. Una primera ayuda sin temporal escribible falló
al importar librerías ML; no se ocultó el requisito de `/work`.

Auditoría de las 27.621 entradas regulares de todas las capas: cero coincidencias
con las claves conocidas (archivo, hex, Base64), cero rutas de secretos/modelos/
artefactos/cachés. El `.venv` de la imagen es el construido desde el lock, no
una copia de la máquina. COPY está limitado a archivos de proyecto y `src`.
Cinco archivos tuvieron marcadores genéricos: delimitadores PEM en `signing.py`
y `cryptography/serialization/ssh.py`, símbolos compilados en `hf_xet` y SciPy,
y una fixture pública de CI sandbox incluida por upstream en
`transformers/testing_utils.py`. Se revisó el contexto ocultando coincidencias;
no son claves/tokens del operador. No se afirma ausencia universal de secretos
desconocidos ni una auditoría de dependencias de producción.

## Custodia y siguiente paso

AES positiva y privada Ed25519 originales permanecen intactas en el Mac.
No se copiaron a Ubuntu, imágenes, YAML, Git ni Notion; no se regeneraron claves
ni se republicó Hugging Face. Trustee solo recibió las fixtures sintéticas
descritas en los checkpoints 009/010. No hay port-forward de esta prueba.
No se modificaron tags históricos ni se creó `layer3-complete`.

Kubelet y containerd están habilitados en systemd. **Reboot no verificado**:
eso no prueba persistencia del KBS efímero. Tras el reinicio anunciado,
revalidar nodo/CoCo/Trustee, audience, política y fixture; después aprovisionar
la AES original y ejecutar positivo → firma inválida → positivo → recurso
denegado → positivo → AES incorrecta → positivo, antes de auditoría/cierre final.

`kata-qemu-coco-dev` usa evidencia **Sample**, no una TEE real. Se demuestra
integración/protocolo y liberación controlada por política; no confidencialidad
frente a un host malicioso. HTTP interno, identidades demo y almacenamiento
efímero permanecen dentro del threat model de laboratorio documentado.
