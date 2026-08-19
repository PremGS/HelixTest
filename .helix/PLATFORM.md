# CATS Deployment Platform Reference

<!-- @helix curated — updated on CATS major releases -->

This file contains exact templates and key facts for deploying to Lilly's
CATS (Cloud Applications and Technology as a Service) Kubernetes platform.

---

## Key Facts

| Item | Value |
|------|-------|
| ECR Account (Prod) | `283234040926` |
| ECR Account (QA) | `474366589702` |
| ECR Account (Dev) | `408787358807` |
| ECR Region | `us-east-2` |
| Infra Apps Repo | `EliLillyCo/LRL_light_k8s_infra_apps` |
| `provenance` in build-push | **MUST be `false`** (prevents broken image index artifacts) |
| Flux annotation prefix | `app.lilly.com/flux.simple.<policy>` |
| Tag pattern (Flux V2) | `glob:sha-.*` (actually regex despite `glob:` prefix) |
| `$imagepolicy` comment | Required on `image:` line for Flux automation |
| Namespace folder | Must match namespace name exactly |
| Namespace changes | Require approval from `lrl_light_infra_approvers` |

---

## GitHub Actions — Load Credentials

```yaml
name: Load Credentials

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Select environment'
        required: true
        default: 'prd'
  pull_request:
    branches: [main]
  push:
    branches: [main]
    tags: ['v*']

jobs:
  Load-Credentials:
    uses: EliLillyCo/hangar/.github/workflows/load-credentials.yaml@main
    with:
      environment: ${{ github.event.inputs.environment || 'prd' }}
```

Creates secrets: `LIGHT_DOCKER_REPOSITORY_URL`, `LIGHT_DOCKER_TOKEN`, `LIGHT_DOCKER_USER`

---

## GitHub Actions — Build and Push Image

```yaml
name: Build and Push Docker Image

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    env:
      ENVIRONMENT: ""
      LOWERCASE_REPO: ""
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Get ECR repo name
        run: echo "LOWERCASE_REPO=$(echo ${{ github.event.repository.name }} | tr [A-Z] [a-z])" >> $GITHUB_ENV

      - name: Set dev variables
        if: github.event_name == 'pull_request'
        run: echo "ENVIRONMENT=dev" >> $GITHUB_ENV

      - name: Set qa variables
        if: github.event_name == 'push' && github.ref_type != 'tag'
        run: echo "ENVIRONMENT=qa" >> $GITHUB_ENV

      - name: Set prod variables
        if: github.ref_type == 'tag'
        run: echo "ENVIRONMENT=prod" >> $GITHUB_ENV

      - name: Generate Docker Metadata
        id: meta
        uses: docker/metadata-action@v5
        env:
          DOCKER_METADATA_PR_HEAD_SHA: true
        with:
          images: |
            ${{ secrets.LIGHT_DOCKER_REPOSITORY_URL }}/${{ env.LOWERCASE_REPO }}
          tags: |
            type=sha,prefix=sha-
            type=sha,prefix=sha-,format=short
            type=sha,prefix=${{ env.ENVIRONMENT }}-sha-,format=short
            type=ref,event=pr
            type=ref,event=branch
            type=ref,event=tag

      - name: Login to ECR
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.LIGHT_DOCKER_USER }}
          password: ${{ secrets.LIGHT_DOCKER_TOKEN }}
          registry: ${{ secrets.LIGHT_DOCKER_REPOSITORY_URL }}
          ecr: false

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          tags: ${{ steps.meta.outputs.tags }}
          push: true
          provenance: false
```

**Environment mapping:** PR → dev, push to main → qa, tag → prod

---

## Kubernetes Deployment Template

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <app-name>
  namespace: <namespace>
  annotations:
    app.lilly.com/flux.automated: "true"
    app.lilly.com/flux.simple.<policy-name>: "283234040926;<ecr-repo>;glob:sha-.*"
    wave.pusher.com/update-on-config-change: "true"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: <app-name>
  template:
    metadata:
      labels:
        app: <app-name>
    spec:
      containers:
        - name: <app-name>
          image: 283234040926.dkr.ecr.us-east-2.amazonaws.com/<ecr-repo>:sha-abc1234 # {"$imagepolicy": "<namespace>:<policy-name>"}
          ports:
            - containerPort: 8000
```

**Critical:** The `# {"$imagepolicy": ...}` comment on the `image:` line is REQUIRED for Flux V2 automation.

---

## Service Template

```yaml
apiVersion: v1
kind: Service
metadata:
  name: <app-name>
  namespace: <namespace>
spec:
  selector:
    app: <app-name>
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
```

---

## Ingress Route Types

| Type | Domain Pattern | Auth | Network |
|------|---------------|------|---------|
| Authenticated (browser) | `*.apps.lrl.lilly.com` | Microsoft SSO | Any |
| Unauthenticated (browser) | `*.apps-internal.lrl.lilly.com` | None | Lilly only |
| API/Script | `*.apps-api.lrl.lilly.com` | AWS STS / Azure App Reg | Lilly only |

**Environment suffixes:** dev = `-d`, qa = `-q`, prod = none

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: <app-name>-ingress
  namespace: <namespace>
spec:
  rules:
    - host: <app-name>.apps.lrl.lilly.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: <app-name>
                port:
                  number: 80
```

---

## Infra Apps Repo Structure

```
LRL_light_k8s_infra_apps/
└── projects/
    ├── dev/<namespace-dev>/
    │   ├── namespace.yaml      ← requires lrl_light_infra_approvers approval
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── ingress.yaml
    ├── qa/<namespace-qa>/
    └── prd/<namespace-prd>/
```

**Rules:**
- Folder name MUST match the namespace name inside `namespace.yaml`
- Only `namespace.yaml` changes require `lrl_light_infra_approvers` approval
- ArgoCD handles initial deploy; Flux V2 handles continuous image updates
- Merge Queue enabled — all PRs validated before merge

---

## Namespace Template

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: <namespace>
  labels:
    cost-center: "<cost-center-id>"
  annotations:
    app.lrl.lilly.com/compute: serverless
    app.lilly.com/argo.automated: "true"
    app.lilly.com/argo.config: |-
      {
        "roles": {
          "readADGroups": ["<read-ad-group>"],
          "adminADGroups": ["<admin-ad-group>"]
        }
      }
```
