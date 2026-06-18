# AISC — Deployment Architecture

**Author**: Lead Systems Architect
**Date**: 2026-06-18
**Version**: 1.0

---

## 1. Overview

AISC deploys as a Kubernetes-native platform with 12 microservices, 4 databases, and supporting infrastructure. All infrastructure is defined as code (Terraform + Helm) and deployed via automated CI/CD pipelines.

---

## 2. Container Strategy

### 2.1 Multi-Stage Dockerfile Template

```
Stage 1 (builder):
  - python:3.12-slim
  - Install build dependencies
  - pip install --no-cache-dir

Stage 2 (runtime):
  - python:3.12-slim (distroless-like)
  - Copy venv from builder
  - Copy application code
  - Non-root user (uid 1000)
  - HEALTHCHECK configured
```

### 2.2 Image Specifications

| Parameter | Target |
|-----------|--------|
| Base image | `python:3.12-slim` |
| Image size | < 300MB per service |
| Layer caching | requirements.txt copied first, then app code |
| Security | Non-root user, no shell, minimal packages |
| Labels | `org.opencontainers.image.*` standard labels |
| Signing | Cosign keyless signing |

---

## 3. Kubernetes Architecture

### 3.1 Cluster Topology

```
┌──────────────────────────────────────────────────┐
│              Production Cluster                   │
│  (3+ nodes per AZ, multi-AZ)                      │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │           System Namespace                   │ │
│  │  Kong Ingress, cert-manager, Istio, Vault    │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │           AISC Namespace                     │ │
│  │  12 microservice Deployments                 │ │
│  │  Horizontal Pod Autoscalers (HPA)            │ │
│  │  Pod Disruption Budgets (PDB)                │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │           Data Namespace                     │ │
│  │  PostgreSQL StatefulSet, Redis StatefulSet   │ │
│  │  Qdrant StatefulSet, Neo4j StatefulSet       │ │
│  │  Kafka StatefulSet                           │ │
│  └─────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### 3.2 Service Deployment Specification

```yaml
# Template for each microservice
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator-service
  namespace: aisc
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      serviceAccountName: aisc-orchestrator
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: orchestrator
        image: registry.aisc.dev/orchestrator-service:{{VERSION}}
        ports:
        - containerPort: 8002
        resources:
          requests: { cpu: "250m", memory: "256Mi" }
          limits:   { cpu: "1000m", memory: "512Mi" }
        livenessProbe:
          httpGet: { path: /health, port: 8002 }
          initialDelaySeconds: 30, periodSeconds: 10
        readinessProbe:
          httpGet: { path: /health, port: 8002 }
          initialDelaySeconds: 5, periodSeconds: 5
        envFrom:
        - configMapRef: { name: aisc-config }
        - secretRef: { name: aisc-secrets }
        volumeMounts:
        - name: vault-secrets
          mountPath: /vault/secrets
      volumes:
      - name: vault-secrets
        csi:
          driver: secrets-store.csi.k8s.io
---
apiVersion: v1
kind: Service
metadata:
  name: orchestrator-service
spec:
  selector: { app: orchestrator-service }
  ports: [{ port: 8002, targetPort: 8002 }]
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orchestrator-service-hpa
spec:
  minReplicas: 3, maxReplicas: 10
  metrics:
  - type: Resource
    resource: { name: cpu, target: { type: Utilization, averageUtilization: 70 } }
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: orchestrator-service-pdb
spec:
  minAvailable: 2
```

### 3.3 Resource Allocations per Service

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit | Min Replicas | Max Replicas |
|---------|:----------:|:---------:|:-------------:|:------------:|:------------:|:------------:|
| auth-service | 250m | 500m | 256Mi | 512Mi | 2 | 5 |
| orchestrator-service | 250m | 1000m | 256Mi | 512Mi | 3 | 10 |
| agent-runtime | 500m | 2000m | 512Mi | 4096Mi | 3 | 10 |
| quality-gate-service | 250m | 500m | 256Mi | 512Mi | 2 | 5 |
| scoring-engine | 250m | 1000m | 256Mi | 1024Mi | 2 | 8 |
| rag-service | 250m | 1000m | 256Mi | 2048Mi | 2 | 5 |
| memory-service | 500m | 1000m | 512Mi | 1024Mi | 3 | 8 |
| self-learning-service | 250m | 500m | 256Mi | 512Mi | 2 | 5 |
| self-healing-service | 250m | 500m | 256Mi | 512Mi | 2 | 5 |
| debate-service | 250m | 500m | 256Mi | 512Mi | 2 | 5 |
| observability-service | 250m | 500m | 256Mi | 512Mi | 2 | 5 |
| ws-gateway | 250m | 500m | 256Mi | 512Mi | 2 | 10 |

---

## 4. Terraform Infrastructure

### 4.1 Cloud Resources

```hcl
# Managed Resources (per environment)
resource "aws_eks_cluster" "aisc" { ... }           # or GKE, AKS
resource "aws_db_instance" "postgresql" { ... }      # RDS PostgreSQL 15
resource "aws_elasticache_cluster" "redis" { ... }   # ElastiCache Redis 7
resource "aws_msk_cluster" "kafka" { ... }           # MSK (Managed Kafka)
resource "aws_ecr_repository" "services" { ... }     # ECR for 12 services
resource "aws_secretsmanager_secret" { ... }         # or Vault
resource "aws_acm_certificate" "aisc" { ... }        # TLS certificates
resource "aws_route53_zone" "aisc" { ... }           # DNS
```

### 4.2 Environment Matrix

| Environment | Purpose | DB Tier | Node Count | Auto-Scaling |
|-------------|---------|---------|:----------:|:------------:|
| **dev** | Local development | docker-compose | 1 (local) | No |
| **staging** | Pre-production testing | db.t3.medium | 3 | Yes (2-10) |
| **production** | Live system | db.r5.xlarge (Multi-AZ) | 6+ (multi-AZ) | Yes (3-20) |

---

## 5. CI/CD Pipeline

### 5.1 Pipeline Stages

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Lint   │───►│  Test   │───►│  Build  │───►│  Scan   │
│  Type   │    │         │    │  Image  │    │  Image  │
└─────────┘    └─────────┘    └─────────┘    └────┬────┘
                                                   │
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌────▼────┐
│Monitor  │◄───│ Deploy  │◄───│ Quality │◄───│ Deploy  │
│(5 min)  │    │ Prod    │    │ Gate    │    │ Staging │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### 5.2 GitHub Actions Workflow

```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    services:
      postgres: { image: postgres:15 }
      redis: { image: redis:7 }
      kafka: { image: confluentinc/cp-kafka }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: mypy --strict .
      - run: pytest --cov --cov-report=xml

  build-and-push:
    needs: lint-and-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [auth, orchestrator, agent-runtime, quality-gate, scoring, rag, memory, self-learning, self-healing, debate, observability, ws-gateway]
    steps:
      - run: docker build -t $REGISTRY/${{matrix.service}}-service:$SHA services/${{matrix.service}}-service
      - run: docker push $REGISTRY/${{matrix.service}}-service:$SHA
      - run: trivy image --severity CRITICAL,HIGH $REGISTRY/${{matrix.service}}-service:$SHA

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - run: helm upgrade aisc-staging ./infra/helm/aisc-platform -f values-staging.yaml --set imageTag=$SHA

  integration-tests:
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/integration/ --env staging

  quality-gate:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - run: python -m aisc.tools.quality_gate_check --env staging --threshold 95

  deploy-production:
    needs: quality-gate
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: helm upgrade aisc-prod ./infra/helm/aisc-platform -f values-production.yaml --set imageTag=$SHA --wait --timeout 10m

  smoke-tests:
    needs: deploy-production
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/smoke/ --env production
      - if: failure()
        run: helm rollback aisc-prod
```

---

## 6. Deployment Strategies

### 6.1 Canary Deployment

```
1. Deploy canary (10% traffic)
2. Observe for 5 minutes
3. Check: error rate, latency, health
4. IF stable: promote to 100% (in 25% increments every 2 min)
5. IF degraded: auto-rollback to previous version
```

### 6.2 Rollback Strategy

```
Auto-rollback triggers:
  - Error rate > 10% for > 1 minute
  - P95 latency > 3x baseline for > 2 minutes
  - Health check failure rate > 5%
  - Any OOM kill or crash loop

Rollback process:
  1. kubectl rollout undo deployment/{service} -n aisc
  2. Verify previous version is healthy
  3. Create incident record
  4. Notify on-call
```

---

## 7. Monitoring & Observability Stack

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│Prometheus│    │ Grafana  │    │ AlertMgr │
│(Metrics) │    │(Dashboards)   │(Alerts)  │
└────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │
     └───────────────┼───────────────┘
                     │
┌──────────┐    ┌────▼─────┐    ┌──────────┐
│   ELK    │    │OpenTele- │    │  Jaeger  │
│(Logging) │    │ metry    │    │(Tracing) │
└──────────┘    │(Collector)│    └──────────┘
                └──────────┘
```

---

## 8. Disaster Recovery

| Component | RPO | RTO | Strategy |
|-----------|:---:|:---:|----------|
| PostgreSQL | < 1 hour | < 4 hours | Continuous WAL archiving, cross-region replica |
| Redis | < 5 min | < 30 min | AOF persistence + snapshot |
| Kafka | 0 (replication) | < 30 min | Multi-broker, cross-AZ, MirrorMaker to DR |
| Qdrant | < 1 hour | < 2 hours | Snapshots to S3 |
| Neo4j | < 1 hour | < 2 hours | Enterprise backups to S3 |
| Event state | Reconstructable | < 4 hours | Replay from Kafka log |

---

## 9. Cost Estimation

| Resource | Monthly Cost (Est.) |
|----------|:-------------------:|
| EKS Cluster (3 nodes x t3.xlarge) | $500 |
| RDS PostgreSQL (db.r5.xlarge, Multi-AZ) | $600 |
| ElastiCache Redis (cache.r5.large) | $200 |
| MSK Kafka (3 x kafka.t3.small) | $400 |
| Qdrant (self-hosted, 3 nodes) | $400 |
| Neo4j (self-hosted, 3 nodes) | $400 |
| Vault (self-hosted) | $0 (infra cost) |
| Load Balancer + NAT Gateway | $100 |
| S3 / Backup Storage | $50 |
| LLM API Costs (per project) | Variable ($100-1000) |
| **Total Infrastructure** | **~$2,650/month** |

---

*End of Deployment Architecture*
