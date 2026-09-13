# Evidencia L3-05: Trustee sintético allow/deny

Fecha: 13-09-2026. Base del repositorio: `38d40d3`. Entorno descrito en los
informes [007](007-layer3-bootstrap.md) y [008](008-layer3-runtime-smoke.md).

## Resultado

Trustee v0.21.0 quedó desplegado junto a CoCo chart 0.22.0. La release de
Trustee declara esa pareja compatible. El checkout y KBS client usan el commit
exacto `258ea4acb7b9bd865fce5c63a539f2120dba8298`; no quedan imágenes core
`latest`. Helm terminó en revisión 2, estado `deployed`, y KBS/AS/RVPS quedaron
Available con estos image IDs observados:

```text
kbs-grpc-as@sha256:4379293c1c83bbf03f0436da9154da7f8f265e2c32d7019ed75e43bcd5cde3d0
coco-as-grpc@sha256:e73b7c1249ec3b5e0d676d6e984cab498fd1d24030df22c2df232b68ffca0b91
rvps@sha256:3c478488eaf1b8a7b6580128ccf960ad4a5e4f000af5c3089c863275a1fea84a
```

El chart incluido conserva metadatos `trustee-0.18.0`/app 0.18.0. Esto no se
trató como otra release: se comprobó el checkout v0.21.0 y se fijaron las tres
imágenes al commit anterior. El cliente `sample_only` se obtuvo del artefacto
OCI de ese mismo commit, cuyo manifiesto resolvió a
`sha256:429be62c527e766a9854f9dac37f878010069c4aa6745d3d555d2bf393b9e82e`.
ORAS 1.3.0 se descargó con su fichero de checksums; `sha256sum -c` devolvió OK.

Se registró únicamente el texto público `cmdp-l3-synthetic-ok-v1` como
`default/test/l3-synthetic`. Ninguna AES ni clave de firma de Layer 1/2 fue
leída, copiada o enviada a Trustee.

## Prueba positiva

Tras aplicar `allow_all.rego`, un Pod `kata-qemu-coco-dev` con BusyBox fijado
por digest solicitó el recurso al CDH local. Resultado final, repetido después
de restaurar la política:

```text
pod=trustee-synthetic-allow-restored phase=Succeeded exit=0 ip=10.244.0.23
trustee_allow_ok=true
GET /kbs/v0/resource/default/test/l3-synthetic HTTP/1.1 200
```

KBS registró antes `POST /auth` 200 y `POST /attest` 200. AS registró
`Verifier/endorsement check passed` con `tee=Sample`, `tee_class="cpu"`, y
`AttestationEvaluate succeeded`.

## Prueba denegatoria

Con el mismo runtime, imagen y recurso, se aplicó `deny_all.rego`. El Pod trató
el fallo de recuperación como resultado esperado y terminó en salida 0:

```text
pod=trustee-synthetic-deny-pinned phase=Succeeded exit=0 ip=10.244.0.22
wget: server returned error: HTTP/1.1 500 Internal Server Error
trustee_deny_ok=true
GET /kbs/v0/resource/default/test/l3-synthetic HTTP/1.1 401
```

El 500 es la traducción que CDH entrega al cliente; el 401 de KBS demuestra que
la petición autenticada/atestada llegó al policy engine y fue rechazada. La
política `allow_all.rego` se restauró después y el positivo final obtuvo 200.

## Fallos de diagnóstico descartados

- La primera instalación usó los `latest` predeterminados del chart y tardó más
  que el timeout mientras descargaba imágenes. Los servicios llegaron a estar
  sanos, pero esa revisión no se aceptó como evidencia reproducible; Helm
  revisión 2 fijó las tres imágenes al commit de la release.
- El tag OCI corto `v0.21.0` no existe para kbs-client. Se enumeró el registro y
  se eligió el tag `sample_only-<commit>-x86_64` verificando su manifiesto.
- Un primer Pod allow recibió un comando alterado por expansión accidental del
  shell del host. Fue sustituido por un heredoc literal.
- Un primer negativo escribió su redirección en `/tmp` con raíz de solo lectura
  y produjo un falso positivo antes de llamar a CDH. Se descartó. El caso final
  captura stderr en memoria y se acepta solo junto al 401 correlacionado de KBS.
- Un manifiesto intermedio seleccionó un hostname incorrecto y otro digest de
  BusyBox inexistente. `kubectl describe` mostró FailedScheduling/ErrImagePull;
  ambos errores se corrigieron usando la etiqueta del RuntimeClass y el digest
  ya comprobado en L3-04. Ninguno cuenta como resultado de aceptación.

## Reproducción y verificación

- `k8s/layer3/trustee-values.yaml` fija las imágenes y documenta las identidades
  demo efímeras.
- Los manifiestos allow/deny fijan BusyBox por digest, no montan token de
  ServiceAccount, ejecutan UID/GID 10001 y usan raíz de solo lectura.
- `scripts/layer3_trustee_smoke.sh` valida el commit de Trustee, guarda el token
  administrativo solo en un `mktemp` 0700/archivos 0600, no imprime payload ni
  token, exige marcadores del Pod y decisiones KBS 200/401 y restaura allow en
  salida normal o mediante trap.
- El script completo se transfirió sin credenciales a un directorio temporal del
  servidor y terminó con los seis marcadores documentados en el runbook; su trap
  retiró el token temporal y cerró el port-forward. El directorio y el archivo
  de transferencia también se eliminaron al finalizar.
- `sh -n scripts/layer3_trustee_smoke.sh`: salida 0.
- `UV_CACHE_DIR=/private/tmp/cmdp-uv-cache uv run pytest -q`: 84 tests pasan;
  son regresión de Layer 1/2 y todavía no hay código Python de Layer 3.
- `git diff --check`: salida 0.

Los tokens administrativos temporales y port-forwards usados durante el ensayo
se retiraron. El recurso y las identidades del chart viven en almacenamiento
efímero del laboratorio; los Pods finales se conservan como evidencia.

## Límites y bloqueo siguiente

Este resultado demuestra conectividad CDH → Attestation Agent → KBS/AS y
enforcement allow/deny con evidencia `Sample`. **No demuestra una TEE real ni
protección frente a un host o control plane malicioso.** Trustee comparte el
clúster, usa HTTP interno, LocalFs/`emptyDir`, claves demo generadas por el chart
y una política deliberadamente amplia. AS avisa además de que `audience` no está
configurado en trusted issuers.

Por tanto L3-05 queda cerrada, pero está prohibido registrar la AES real todavía.
D3 debe fijar el contrato del Consumer y D4 debe resolver persistencia, TLS,
identidad/token administrativo, política mínima ligada al workload y el warning
de audience. No se modificaron bundle publicado, claves existentes, tags,
Dockerfiles, código Python ni recursos de Layer 1/2.

Referencias: [release Trustee v0.21.0](https://github.com/confidential-containers/trustee/releases/tag/v0.21.0),
[instalación Helm](https://confidentialcontainers.org/docs/attestation/installation/helm/),
[configuración CoCo](https://confidentialcontainers.org/docs/attestation/coco-setup/)
y [get-resource CDH](https://confidentialcontainers.org/docs/features/get-resource/).
