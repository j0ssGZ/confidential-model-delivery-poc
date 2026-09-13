# Evidencia L3-03/L3-04: bootstrap del laboratorio

Fecha: 13-09-2026. Host `secure-ai-node`, acceso SSH desde la red local.
Esta evidencia no contiene contraseñas, kubeconfigs, claves privadas, tokens de
unión ni material AES.

## Host comprobado

- Ubuntu 22.04.5 LTS, kernel 5.15.0-191, x86_64.
- Intel Core i5-4670K, 4 CPU, VT-x y flags VMX/EPT.
- `/dev/kvm` presente; módulos `kvm_intel` y `kvm` cargados.
- 7,7 GiB de RAM, sin swap y 86 GiB libres en `/`.
- Usuario operador con sudo; añadido a `kvm`, efectivo en el siguiente login.

## Componentes fijados

- containerd 2.2.1, activo/habilitado; configuración v3 con
  `SystemdCgroup = true`.
- Kubernetes 1.36.4: kubeadm, kubelet y kubectl instalados desde el repositorio
  oficial `pkgs.k8s.io` después de reparar su keyring. Paquetes en hold.
- Helm 3.18.6 descargado desde `get.helm.sh`; checksum publicado correcto.
- Flannel 0.28.8 desde URL de release fijada.
- CoCo Helm chart 0.22.0, digest observado
  `sha256:de6297ee48652e7c339553ce7ffd562b0e0ea7b8cc7a63362c59745156bfd3c5`.

## Resultado Kubernetes

`kubeadm init` usó la IP 192.168.2.26, el socket de containerd y CIDR de Pods
`10.244.0.0/16`. Kubeconfig de usuario quedó con modo 0600. El nodo de control
se desmarcó de `NoSchedule` por ser laboratorio de un solo nodo.

El token bootstrap mostrado una vez por kubeadm se revocó inmediatamente;
`kubeadm token list` quedó vacío. No se registra su valor en este informe.

Estado observado antes de salir:

- `secure-ai-node`: `Ready`, Kubernetes v1.36.4.
- API server, etcd, scheduler, controller-manager, kube-proxy y dos CoreDNS:
  `Running`.
- `kube-flannel-ds`: `Running`.
- release Helm `coco`: `deployed`, revisión 1.
- RuntimeClass `kata-qemu-coco-dev`: creada.
- `kata-as-coco-runtime`: `ContainerCreating`, descargando la imagen fijada
  `quay.io/kata-containers/kata-deploy:4.0.0`.

## Pendiente al cerrar este bootstrap (histórico)

No se afirma que CoCo esté operativo. Hay que comprobar persistencia del nodo,
esperar el DaemonSet, inspeccionar errores y ejecutar un Pod mínimo con
`kata-qemu-coco-dev`. Solo entonces se completa L3-04 y se comienza Trustee.
No se desplegó Trustee, no se registró la AES y no se modificó ni republicó el
bundle de Hugging Face.

Seguimiento posterior: el instalador terminó y el smoke pasó el 13-09-2026;
ver [informe 008](008-layer3-runtime-smoke.md). El host aún mantenía su arranque
anterior, por lo que sigue pendiente comprobar un reinicio real.
