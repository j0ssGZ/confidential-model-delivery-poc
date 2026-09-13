#!/bin/sh
set -eu

TRUSTEE_NAMESPACE="coco-trustee"
WORKLOAD_NAMESPACE="secure-ai-layer3"
RESOURCE_PATH="default/test/l3-synthetic"
TRUSTEE_COMMIT="258ea4acb7b9bd865fce5c63a539f2120dba8298"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_DIR=$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)
ALLOW_POLICY="$REPO_DIR/k8s/layer3/sample-resource-policy.rego"
KBS_CLIENT=${KBS_CLIENT:-}
TRUSTEE_CHECKOUT=${TRUSTEE_CHECKOUT:-}

if [ -z "$KBS_CLIENT" ] || [ ! -x "$KBS_CLIENT" ]; then
  echo "error: set KBS_CLIENT to the executable v0.21.0 sample-only client" >&2
  exit 2
fi
if [ -z "$TRUSTEE_CHECKOUT" ] || [ ! -d "$TRUSTEE_CHECKOUT/kbs/sample_policies" ]; then
  echo "error: set TRUSTEE_CHECKOUT to the Trustee v0.21.0 checkout" >&2
  exit 2
fi
if [ "$(git -C "$TRUSTEE_CHECKOUT" rev-parse HEAD)" != "$TRUSTEE_COMMIT" ]; then
  echo "error: TRUSTEE_CHECKOUT is not the approved Trustee v0.21.0 commit" >&2
  exit 2
fi

work_dir=$(mktemp -d)
port_forward_pid=""
restore_allow="false"

cleanup() {
  result=$?
  trap - EXIT
  if [ "$restore_allow" = "true" ]; then
    if ! "$KBS_CLIENT" --url http://127.0.0.1:18080 config \
      --admin-token-file "$work_dir/admin-token" set-resource-policy \
      --policy-file "$ALLOW_POLICY" \
      >/dev/null 2>&1; then
      echo "error: policy restoration failed; restore sample-resource-policy.rego before continuing" >&2
      result=1
    fi
  fi
  if [ -n "$port_forward_pid" ]; then
    kill "$port_forward_pid" 2>/dev/null || true
    wait "$port_forward_pid" 2>/dev/null || true
  fi
  rm -rf "$work_dir"
  exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

wait_for_terminal_phase() {
  pod_name=$1
  attempts=0
  while [ "$attempts" -lt 100 ]; do
    phase=$(kubectl -n "$WORKLOAD_NAMESPACE" get "$pod_name" -o jsonpath='{.status.phase}')
    case "$phase" in
      Succeeded) return 0 ;;
      Failed) return 1 ;;
    esac
    attempts=$((attempts + 1))
    sleep 3
  done
  return 1
}

wait_for_kbs_decision() {
  pod_ip=$1
  expected_status=$2
  attempts=0
  while [ "$attempts" -lt 20 ]; do
    if kubectl -n "$TRUSTEE_NAMESPACE" logs deployment/trustee-kbs \
      --since=5m 2>/dev/null | grep -F "$pod_ip" | \
      grep -Fq "\"GET /kbs/v0/resource/$RESOURCE_PATH HTTP/1.1\" $expected_status "; then
      return 0
    fi
    attempts=$((attempts + 1))
    sleep 1
  done
  echo "error: KBS did not log HTTP $expected_status for Pod $pod_ip" >&2
  return 1
}

kubectl -n "$TRUSTEE_NAMESPACE" wait --for=condition=available \
  deployment/trustee-kbs deployment/trustee-as deployment/trustee-rvps \
  --timeout=180s

kubectl port-forward -n "$TRUSTEE_NAMESPACE" svc/trustee-kbs 18080:8080 \
  >"$work_dir/port-forward.log" 2>&1 &
port_forward_pid=$!
sleep 2
kill -0 "$port_forward_pid"

admin_secret=$(kubectl -n "$TRUSTEE_NAMESPACE" get secret -o name | \
  sed -n '/bootstrap-user-keys$/p' | head -n 1)
test -n "$admin_secret"
umask 077
kubectl -n "$TRUSTEE_NAMESPACE" get "$admin_secret" \
  -o jsonpath='{.data.KBS_ADMIN_TOKEN}' | base64 -d >"$work_dir/admin-token"
printf '%s' 'cmdp-l3-synthetic-ok-v1' >"$work_dir/resource"

"$KBS_CLIENT" --url http://127.0.0.1:18080 config \
  --admin-token-file "$work_dir/admin-token" set-resource-policy \
  --policy-file "$ALLOW_POLICY" >/dev/null
restore_allow="true"
"$KBS_CLIENT" --url http://127.0.0.1:18080 config \
  --admin-token-file "$work_dir/admin-token" set-resource \
  --path "$RESOURCE_PATH" --resource-file "$work_dir/resource" >/dev/null

kbs_ip=$(kubectl -n "$TRUSTEE_NAMESPACE" get svc trustee-kbs \
  -o jsonpath='{.spec.clusterIP}')
sed "s/__KBS_IP__/$kbs_ip/g" \
  "$REPO_DIR/k8s/layer3/trustee-synthetic-allow.yaml" >"$work_dir/allow.yaml"
allow_pod=$(kubectl create -f "$work_dir/allow.yaml" -o name)
wait_for_terminal_phase "$allow_pod"
kubectl -n "$WORKLOAD_NAMESPACE" logs "$allow_pod" | grep -Fx 'trustee_allow_ok=true'
allow_ip=$(kubectl -n "$WORKLOAD_NAMESPACE" get "$allow_pod" \
  -o jsonpath='{.status.podIP}')
wait_for_kbs_decision "$allow_ip" 200
echo "trustee_allow_kbs_http=200"

"$KBS_CLIENT" --url http://127.0.0.1:18080 config \
  --admin-token-file "$work_dir/admin-token" set-resource-policy \
  --policy-file "$TRUSTEE_CHECKOUT/kbs/sample_policies/deny_all.rego" >/dev/null
sed "s/__KBS_IP__/$kbs_ip/g" \
  "$REPO_DIR/k8s/layer3/trustee-synthetic-deny.yaml" >"$work_dir/deny.yaml"
deny_pod=$(kubectl create -f "$work_dir/deny.yaml" -o name)
wait_for_terminal_phase "$deny_pod"
kubectl -n "$WORKLOAD_NAMESPACE" logs "$deny_pod" | grep -Fx 'trustee_deny_ok=true'
deny_ip=$(kubectl -n "$WORKLOAD_NAMESPACE" get "$deny_pod" \
  -o jsonpath='{.status.podIP}')
wait_for_kbs_decision "$deny_ip" 401
echo "trustee_deny_kbs_http=401"

"$KBS_CLIENT" --url http://127.0.0.1:18080 config \
  --admin-token-file "$work_dir/admin-token" set-resource-policy \
  --policy-file "$ALLOW_POLICY" >/dev/null
restore_allow="false"
echo "trustee_policy_restored=sample_resource_allowlist"

echo "trustee_synthetic_allow_deny_ok=true"
