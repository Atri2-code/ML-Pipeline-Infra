#!/usr/bin/env bash
# deploy.sh — apply all Kubernetes manifests for the given environment
# Usage: ./scripts/deploy.sh <environment>
# Example: ./scripts/deploy.sh staging

set -euo pipefail

ENVIRONMENT="${1:-staging}"
NAMESPACE="ml-pipeline"
MANIFEST_DIR="kubernetes"

echo "==> Deploying to environment: ${ENVIRONMENT}"
echo "==> Namespace: ${NAMESPACE}"

echo "==> Ensuring namespace exists"
kubectl get namespace "${NAMESPACE}" > /dev/null 2>&1 \
  || kubectl create namespace "${NAMESPACE}"

echo "==> Applying ConfigMaps"
kubectl apply -f "${MANIFEST_DIR}/configmaps/" -n "${NAMESPACE}"

echo "==> Applying Deployments"
kubectl apply -f "${MANIFEST_DIR}/deployments/" -n "${NAMESPACE}"

echo "==> Applying Services"
kubectl apply -f "${MANIFEST_DIR}/services/" -n "${NAMESPACE}"

echo "==> Waiting for inference-service rollout"
kubectl rollout status deployment/inference-service \
  -n "${NAMESPACE}" \
  --timeout=300s

echo "==> Waiting for grafana rollout"
kubectl rollout status deployment/grafana \
  -n "${NAMESPACE}" \
  --timeout=120s

echo "==> Deployment complete"
kubectl get pods -n "${NAMESPACE}"
