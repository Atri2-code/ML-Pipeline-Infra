# ML-Pipeline-Infra

![CI](https://github.com/Atri2-code/ml-pipeline-infra/actions/workflows/ci.yml/badge.svg)
![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC)
![Kubernetes](https://img.shields.io/badge/orchestration-Kubernetes-326CE5)
![Python](https://img.shields.io/badge/language-Python_3.11-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)

Production-grade infrastructure repository for deploying, scaling, and monitoring a machine learning inference pipeline on AWS. Provisions cloud resources with Terraform, orchestrates containerised ML services with Kubernetes, automates build and release with GitHub Actions, and exposes system health through a Grafana observability dashboard.

Built to mirror real Software Infrastructure team responsibilities: CI platform management, build engineering, component integration, and packaging and release systems for ML software components.

---

## Architecture overview

```
┌─────────────────────────────────────────────────────────┐
│                     GitHub Actions CI                    │
│   lint → test → build → push image → deploy to k8s     │
└───────────────────────┬─────────────────────────────────┘
                        │
         ┌──────────────▼──────────────┐
         │        AWS (Terraform)       │
         │   EC2 · S3 · IAM · VPC      │
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │      Kubernetes Cluster      │
         │  ┌──────────┐ ┌──────────┐  │
         │  │ inference│ │  model   │  │
         │  │  service │ │  store   │  │
         │  └──────────┘ └──────────┘  │
         │  ┌──────────────────────┐   │
         │  │   Grafana Dashboard  │   │
         │  └──────────────────────┘   │
         └─────────────────────────────┘
```

---

## Repository structure

```
ml-pipeline-infra/
├── .github/
│   └── workflows/
│       ├── ci.yml              # lint, test, build, push on PR
│       └── release.yml         # tag-triggered deploy to k8s
├── terraform/
│   ├── main.tf                 # root module — AWS provider + state backend
│   ├── variables.tf            # input variable declarations
│   ├── outputs.tf              # exported resource identifiers
│   └── modules/
│       ├── ec2/                # compute module (instance, SG, IAM role)
│       └── s3/                 # model artefact store module
├── kubernetes/
│   ├── deployments/
│   │   ├── inference-deployment.yaml
│   │   └── grafana-deployment.yaml
│   ├── services/
│   │   ├── inference-service.yaml
│   │   └── grafana-service.yaml
│   └── configmaps/
│       └── inference-config.yaml
├── grafana/
│   └── dashboards/
│       └── ml-pipeline-dashboard.json
├── scripts/
│   ├── build.sh                # docker build + tag + push
│   ├── deploy.sh               # kubectl apply wrapper
│   └── healthcheck.sh          # post-deploy liveness probe loop
├── src/
│   ├── inference_service.py    # FastAPI ML inference endpoint
│   └── model_loader.py         # S3 model artefact fetch + cache
├── tests/
│   ├── test_inference.py
│   └── test_model_loader.py
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Docker | 24+ |
| kubectl | 1.28+ |
| Terraform | 1.7+ |
| AWS CLI | 2.x (configured with credentials) |

---

## Quick start

### 1. Provision cloud infrastructure

```bash
cd terraform
terraform init
terraform plan -var="environment=staging"
terraform apply -var="environment=staging"
```

This provisions an EC2 instance for the k8s node, an S3 bucket for model artefacts, and the required IAM roles and VPC security groups.

### 2. Deploy to Kubernetes

```bash
# Apply all manifests
chmod +x scripts/deploy.sh
./scripts/deploy.sh staging

# Verify rollout
kubectl rollout status deployment/inference-service -n ml-pipeline
```

### 3. Run the test suite

```bash
pip install -r requirements.txt
pytest tests/ -v --tb=short
```

### 4. Build and push the Docker image

```bash
chmod +x scripts/build.sh
./scripts/build.sh 1.0.0
```

---

## CI/CD pipeline

Two GitHub Actions workflows automate the full build and release lifecycle:

**`ci.yml`** — triggered on every pull request:
1. Lint Python with `ruff`
2. Run `pytest` unit test suite
3. Build Docker image (no push on PR)
4. Validate Terraform plan (`terraform validate`)

**`release.yml`** — triggered on version tags (`v*.*.*`):
1. Run full test suite
2. Build and push Docker image to ECR
3. Update Kubernetes deployment image tag
4. Run post-deploy healthcheck (`scripts/healthcheck.sh`)
5. Notify on failure

---

## Kubernetes manifests

The inference service runs as a `Deployment` with 3 replicas behind a `ClusterIP` service. Resource requests and limits are set to prevent noisy-neighbour issues on shared HPC nodes.

```bash
kubectl get pods -n ml-pipeline
kubectl logs -f deployment/inference-service -n ml-pipeline
kubectl get svc -n ml-pipeline
```

---

## Terraform modules

### `modules/ec2`
Provisions a compute instance with an instance profile granting S3 read access for model artefact fetching. Security group restricts inbound to ports 22 (SSH, CIDR-scoped) and 8080 (inference API).

### `modules/s3`
Provisions a versioned S3 bucket for model artefact storage with server-side encryption (AES-256) and a lifecycle rule archiving objects older than 90 days to Glacier.

---

## Grafana observability

Import `grafana/dashboards/ml-pipeline-dashboard.json` into your Grafana instance. The dashboard tracks:

- Inference request rate (req/s)
- P50 / P95 / P99 response latency
- Pod CPU and memory utilisation
- Model load time from S3
- Error rate by HTTP status code

---

## Running tests

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=term-missing
```

Tests cover inference endpoint response schema, model loader S3 fetch logic (mocked with `moto`), and error handling on malformed inputs.

---

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `MODEL_BUCKET` | S3 bucket name for model artefacts | — |
| `MODEL_KEY` | S3 object key for the model file | — |
| `LOG_LEVEL` | Python logging level | `INFO` |
| `PORT` | Port the inference service listens on | `8080` |

---

## License

MIT
