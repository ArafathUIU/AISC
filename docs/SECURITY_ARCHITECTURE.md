# AISC — Security Architecture

**Author**: Lead Systems Architect
**Date**: 2026-06-18
**Version**: 1.0

---

## 1. Security Overview

AISC implements defense-in-depth across its entire architecture. Security is non-negotiable: the Security Quality Gate has the highest threshold (98) and critical findings halt the deployment pipeline immediately.

---

## 2. Authentication

### 2.1 OAuth2 / JWT Flow

```
┌────────┐     ┌─────────────┐     ┌──────────┐
│ Client │     │ Auth Service │     │   Redis   │
└───┬────┘     └──────┬──────┘     └────┬─────┘
    │                 │                 │
    │ POST /login     │                 │
    │────────────────►│                 │
    │                 │ Verify bcrypt   │
    │                 │ hash            │
    │                 │                 │
    │                 │ Store refresh   │
    │                 │ token family    │
    │                 │────────────────►│
    │                 │                 │
    │ 200 {access,    │                 │
    │      refresh}   │                 │
    │◄────────────────│                 │
    │                 │                 │
    │ API call with   │                 │
    │ Bearer <access> │                 │
    │────────────────►│                 │
    │                 │ Verify JWT      │
    │                 │ Check blacklist │
    │                 │◄────────────────│
    │                 │                 │
    │ 200 OK / 401    │                 │
    │◄────────────────│                 │
```

### 2.2 Token Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Access Token TTL | 15 minutes | Limit blast radius of stolen token |
| Refresh Token TTL | 7 days | Reasonable session length |
| Algorithm | RS256 (asymmetric) | Services can verify without calling auth service |
| Key Rotation | Every 30 days | Limit key exposure |
| Token Blacklist | Redis set with TTL matching token expiry | Fast invalidation |
| Refresh Token Rotation | New refresh token on each use | Detect token theft (reuse = theft) |

### 2.3 Multi-Factor Authentication (Optional)

| Method | Implementation |
|--------|---------------|
| TOTP | pyotp, QR code enrollment |
| WebAuthn | For admin/high-privilege accounts |
| Backup Codes | 10 single-use recovery codes |

---

## 3. Authorization

### 3.1 RBAC (Role-Based Access Control)

| Role | Permissions |
|------|-------------|
| `admin` | Full system access. User management. System configuration. |
| `developer` | Create/edit projects. View all artifacts. Trigger deployments. |
| `viewer` | Read-only access to assigned projects. |

### 3.2 ABAC (Attribute-Based Access Control)

```yaml
# Example policy: User can only access projects they are a member of
policy:
  resource: "project"
  action: "read"
  condition:
    user_id: "{{request.user.id}}"
    project_members: "contains(project.members, user_id)"

# Example policy: Only project owner can delete
policy:
  resource: "project"
  action: "delete"
  condition:
    user_id: "{{request.user.id}}"
    project_owner_id: "equals(project.owner_id, user_id)"
```

### 3.3 Permission Hierarchy

```
projects:admin
  ├── projects:create
  ├── projects:read
  ├── projects:update
  ├── projects:delete
  └── projects:manage_members

artifacts:admin
  ├── artifacts:create
  ├── artifacts:read
  ├── artifacts:update
  └── artifacts:approve

deployments:admin
  ├── deployments:execute
  ├── deployments:rollback
  └── deployments:approve

system:admin
  ├── agents:manage
  ├── config:manage
  └── audit:read
```

---

## 4. Encryption

### 4.1 Data in Transit

| Layer | Protocol | Notes |
|-------|----------|-------|
| External API | TLS 1.3 | Minimum: TLS 1.2, HSTS enabled |
| Internal Services | mTLS via Istio | All service-to-service encrypted |
| Kafka | TLS + SASL_SSL | Broker-client encryption |
| Database Connections | TLS 1.3 | All DB connections encrypted |

### 4.2 Data at Rest

| Data Type | Encryption | Key Management |
|-----------|------------|----------------|
| PostgreSQL | AES-256 (storage-level) | Cloud KMS or Vault Transit |
| Redis | Not encrypted by default | Sensitive values encrypted at application layer |
| Qdrant | AES-256 (storage-level) | Cloud KMS |
| Neo4j | AES-256 (storage-level) | Cloud KMS |
| File Storage (S3/GCS) | SSE-KMS | Cloud KMS with automatic rotation |
| Backups | AES-256 | Separate backup encryption key |

### 4.3 Application-Level Encryption

```
Sensitive fields encrypted before storage:

- User PII (email, name): AES-256-GCM with per-user key
- API keys (stored in Vault): Vault-managed
- JWT signing keys: Vault-managed, auto-rotated
- Database credentials: Vault dynamic secrets
```

---

## 5. Secret Management

### 5.1 Vault Architecture

```
┌──────────────────────────────────────────────┐
│              HashiCorp Vault                  │
│                                               │
│  ┌─────────────┐  ┌─────────────┐            │
│  │ Static      │  │ Dynamic     │            │
│  │ Secrets     │  │ Secrets     │            │
│  │ (KV v2)     │  │ (DB, Cloud) │            │
│  └──────┬──────┘  └──────┬──────┘            │
│         │                │                    │
│  ┌──────▼────────────────▼──────┐            │
│  │      Kubernetes CSI Driver    │            │
│  │   (mounts secrets as files)   │            │
│  └──────────────┬───────────────┘            │
└─────────────────┼────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌─────▼────┐  ┌────▼─────┐
│ Auth  │   │ Agent    │  │ DevOps   │
│ Svc   │   │ Runtime  │  │ Svc      │
└───────┘   └──────────┘  └──────────┘
```

### 5.2 Secret Types Managed

| Secret | Rotation | Access Pattern |
|--------|----------|----------------|
| PostgreSQL credentials | Vault dynamic (1hr TTL) | Per-service DB role |
| Redis password | 90-day rotation | Shared |
| JWT signing keys | 30-day rotation | Auth service only |
| LLM API keys | 90-day rotation | Agent runtime only |
| Cloud provider credentials | Vault dynamic (1hr TTL) | DevOps service |
| TLS certificates | 90-day rotation (auto via cert-manager) | Ingress |

---

## 6. Network Security

### 6.1 Network Segmentation

```
┌──────────────────────────────────────────────────┐
│                  External Network                 │
│  (Internet -> Cloud Load Balancer -> WAF)         │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│                  DMZ Subnet                       │
│  Kong API Gateway, WebSocket Gateway              │
│  (only services exposed to internet)              │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│              Application Subnet                   │
│  12 microservices (internal communication only)   │
│  Istio mTLS, network policies                     │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│                Data Subnet                        │
│  PostgreSQL, Redis, Qdrant, Neo4j, Kafka, Vault   │
│  (no internet access, app subnet ingress only)    │
└──────────────────────────────────────────────────┘
```

### 6.2 Kubernetes Network Policies

```yaml
# Default: deny all ingress
# Allow: app subnet -> data subnet (specific ports)
# Allow: DMZ -> app subnet (API gateway ports)
# Deny:  data subnet -> internet (egress blocked)
# Deny:  pod-to-pod in different namespaces (unless explicitly allowed)
```

---

## 7. Agent Security

### 7.1 Agent Execution Sandbox

| Constraint | Implementation |
|------------|---------------|
| Code execution | Isolated Docker container, no network access |
| File system | Read-only except designated output directory |
| Network | Only allowed to call internal services (HTTP) and LLM APIs |
| Environment | No secrets in env vars (Vault CSI driver mounts) |
| Resource limits | CPU: 2 cores, Memory: 4GB, Timeout: 10min per task |
| Disk | Ephemeral, wiped after task completion |

### 7.2 Agent Permissions (Principle of Least Privilege)

| Agent | Can Read | Can Write | Can Execute |
|-------|----------|-----------|-------------|
| Developer | Architecture, API specs | Source code | Code generation, static analysis |
| QA | Source code, API specs | Test files | Test runner |
| Security | All code | Security reports | SAST scanners |
| DevOps | Code, tests | Deploy configs | Docker, K8s, Terraform |
| Self-Healing | Logs, metrics, code | Patches, incidents | RCA, patch generation |

---

## 8. Vulnerability Management

### 8.1 Automated Scanning

| Scan Type | Tool | Frequency | Gate Impact |
|-----------|------|-----------|-------------|
| SAST | bandit | Every code generation | Blocks if HIGH+ found |
| Dependency CVE | safety | Every generation + daily | Blocks if CRITICAL CVE |
| Secret Detection | detect-secrets | Every commit + pre-commit hook | Blocks on any finding |
| Container Scan | Trivy | Every image build | Blocks if CRITICAL CVE |
| DAST | OWASP ZAP | Every staging deploy | Blocks if HIGH+ found |
| IaC Scan | tfsec / checkov | Every Terraform change | Blocks on CRITICAL |

### 8.2 Vulnerability Response SLA

| Severity | Response Time | Fix Time | Process |
|----------|:------------:|:--------:|---------|
| Critical | 15 minutes | 4 hours | Halt pipeline, escalate, emergency patch |
| High | 2 hours | 24 hours | Block deployment, fix in next iteration |
| Medium | 8 hours | 7 days | Schedule fix |
| Low | — | 30 days | Backlog |

---

## 9. Audit Logging

### 9.1 Audited Events

| Category | Events Logged |
|----------|--------------|
| Authentication | Login, logout, failed login, password change, MFA enrollment |
| Authorization | Permission denied, role change, policy update |
| Agent Actions | Task creation, assignment, execution, escalation |
| Artifact Changes | Creation, update, approval, rejection, deletion |
| Deployment | Triggered, completed, rolled back, approved |
| Configuration | System config changes, agent config changes |
| Data Access | Sensitive data reads, exports |

### 9.2 Audit Log Format

```json
{
  "audit_id": "uuid",
  "timestamp": "ISO8601",
  "actor": {
    "type": "user|agent|system",
    "id": "uuid",
    "name": "john@example.com"
  },
  "action": "artifact.approve",
  "resource": {
    "type": "artifact",
    "id": "uuid",
    "project_id": "uuid"
  },
  "outcome": "success|failure",
  "details": {
    "previous_status": "in_review",
    "new_status": "approved",
    "gate_type": "code_gate",
    "score": 94
  },
  "ip_address": "203.0.113.1",
  "user_agent": "AISC-Admin-Dashboard/1.0",
  "correlation_id": "uuid"
}
```

### 9.3 Audit Log Storage

- Immutable append-only log (immudb or WORM storage)
- Retained for 3 years minimum
- Cannot be modified or deleted by any service account
- Queryable via admin API with RBAC check

---

## 10. Compliance Framework

### 10.1 OWASP Top 10 Coverage

| OWASP Risk | AISC Mitigation |
|------------|-----------------|
| A01 Broken Access Control | RBAC + ABAC on every endpoint |
| A02 Cryptographic Failures | TLS 1.3, AES-256, Vault-managed keys |
| A03 Injection | Parameterized queries, Pydantic validation, bandit scanning |
| A04 Insecure Design | Architecture security review gate, threat modeling |
| A05 Security Misconfiguration | IaC scanning, hardened container images, network policies |
| A06 Vulnerable Components | safety dependency scanning, Trivy container scanning |
| A07 Auth Failures | JWT with rotation, bcrypt, MFA, rate limiting on login |
| A08 Software/Data Integrity | Signed commits, image signing, artifact hashing |
| A09 Logging/Monitoring Failures | Structured audit logging, ELK, Prometheus alerting |
| A10 SSRF | Network policies, agent sandbox, egress filtering |

---

## 11. Incident Response

### 11.1 Incident Severity Classification

| Severity | Definition | Example |
|----------|------------|---------|
| SEV1 (Critical) | Production outage, data breach, auth bypass | All services down, secret exposed publicly |
| SEV2 (High) | Major feature down, security vulnerability found | Payment service broken, bandit CRITICAL finding |
| SEV3 (Medium) | Minor feature degraded, performance issue | Latency 2x baseline, flaky tests detected |
| SEV4 (Low) | Cosmetic issue, code quality warning | radon D-ranked function, minor lint warning |

### 11.2 Automated Response Matrix

| Trigger | Automated Action | Human Involvement |
|---------|-----------------|:-----------------:|
| SEV1 | Auto-rollback + halt pipeline + notify | Required immediately |
| SEV2 (known pattern, high confidence RCA) | Self-Healing generates + deploys patch | Notified, can override |
| SEV2 (unknown pattern) | Gather diagnostics, escalate | Required |
| SEV3 | Self-Healing generates patch, deploys to staging | Approve for production |
| SEV4 | Logged, added to improvement backlog | Optional |

---

## 12. Secure Development Lifecycle

```
Phase                Security Activity
─────                ─────────────────
Requirements  -->    Threat modeling, security requirements
Architecture  -->    Security architecture review gate
Code          -->    SAST (bandit), secret scanning, LLM security review
Testing       -->    Security-focused test cases, fuzzing
Pre-Deploy    -->    Dependency audit, container scan, IaC scan
Staging       -->    DAST (OWASP ZAP), penetration test
Production    -->    Runtime security monitoring, anomaly detection
Incident      -->    RCA, patch generation, knowledge extraction
```

---

*End of Security Architecture*
