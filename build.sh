#!/usr/bin/env bash
# build.sh — build, tag, and push the inference service Docker image to ECR
# Usage: ./scripts/build.sh <version>
# Example: ./scripts/build.sh 1.2.0

set -euo pipefail

VERSION="${1:-latest}"
AWS_REGION="${AWS_REGION:-eu-west-2}"
IMAGE_NAME="ml-inference-service"

if [[ -z "${AWS_ACCOUNT_ID:-}" ]]; then
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
fi

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}"

echo "==> Logging into ECR"
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "==> Building image: ${IMAGE_NAME}:${VERSION}"
docker build \
  --tag "${IMAGE_NAME}:${VERSION}" \
  --tag "${IMAGE_NAME}:latest" \
  --file Dockerfile \
  .

echo "==> Tagging for ECR"
docker tag "${IMAGE_NAME}:${VERSION}" "${ECR_URI}:${VERSION}"
docker tag "${IMAGE_NAME}:latest"     "${ECR_URI}:latest"

echo "==> Pushing to ECR"
docker push "${ECR_URI}:${VERSION}"
docker push "${ECR_URI}:latest"

echo "==> Done — pushed ${ECR_URI}:${VERSION}"
