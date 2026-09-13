# Checkpoint D3/D4 y Consumer Layer 3

13-09-2026; parte de `a554e568bca6239b0d82863b601a23209de6d4bb`.

Se revalidó el servidor existente sin reinstalar: nodo Ready, DaemonSet 1/1,
KBS/AS/RVPS sanos y mismo arranque 12-09-2026 23:39:15. Nuevo smoke
`kata-runtime-smoke-b4dfq` pasó exit 0, kernel 6.18.35 y `kata_smoke_ok=true`.
El script L3-05 se repitió con 200/401 y restauración válida.

La causa de audience está en KBS admin, no AS: el chart omite audience en el
verificador. Se añadió `audience="KBS"` manteniendo las identidades. Antes de
reiniciar únicamente KBS se conservaron configuración, logs y repositorio en
`/tmp/cmdp-l3-private-backups/kbs-audience-09zy3gx8` del operador. Se restauraron
los datos; admin válido devolvió 200 y token con la misma firma confiada pero
audience distinta devolvió 401. El warning ausente dejó de aparecer.

`sample-resource-policy.rego` deniega por defecto y limita plugin, query,
evidencia Sample y tres rutas explícitas. El smoke real pasó con la política
acotada, deny_all y restauración acotada. Se registró solo la fixture pública
de 32 ceros `default/test/wrong-aes`; la AES real todavía no se usó.

Proveedor CDH y Consumer separado implementados. `uv run pytest -q`: 123 tests
pasaron, incluyendo límites HTTP, ausencia de proxy/redirecciones, firma antes
del proveedor, rechazo de clave denegada/longitud inválida antes de GCM, GCM
incorrecto antes de extracción, snapshot de bytes y limpieza ante fallo.
No se modificaron funciones, manifiestos ni entrypoints existentes de L1/L2.

La ejecución del proveedor Python en Kata, builds y E2E con modelo siguen
pendientes en este checkpoint; la regresión unitaria no los sustituye.
