#!/usr/bin/env sh
set -eu

key_file=${1:?usage: create_model_secret.sh /path/to/model-key.bin [context]}
cluster_context=${2:-kind-secure-ai}

if [ "$(wc -c < "$key_file" | tr -d ' ')" != "32" ]; then
  echo "key file must contain exactly 32 bytes" >&2
  exit 2
fi

kubectl --context "$cluster_context" -n secure-ai-poc create secret generic \
  model-decryption-key --from-file=key="$key_file" --dry-run=client -o yaml | \
  kubectl --context "$cluster_context" apply -f -
