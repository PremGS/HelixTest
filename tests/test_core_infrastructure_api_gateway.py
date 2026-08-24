# TS-002: Core Infrastructure & API Gateway
# Framework: pytest + httpx.AsyncClient
# Stories: STORY-1, STORY-3, STORY-4, STORY-5, STORY-6

import os
import json
import subprocess
import asyncio
import pytest
import httpx
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration & Fixtures
# ---------------------------------------------------------------------------

API_GATEWAY_BASE_URL = os.environ.get("API_GATEWAY_BASE_URL", "http://localhost:8000")
COSMOS_DB_ACCOUNT_NAME = os.environ.get("COSMOS_DB_ACCOUNT_NAME", "sllip-cosmos-dev")
COSMOS_DB_RESOURCE_GROUP = os.environ.get("COSMOS_DB_RESOURCE_GROUP", "sllip-rg-dev")
STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT_NAME", "sllipstoragedev")
STORAGE_RESOURCE_GROUP = os.environ.get("STORAGE_RESOURCE_GROUP", "sllip-rg-dev")
OTEL_COLLECTOR_ENDPOINT = os.environ.get("OTEL_COLLECTOR_ENDPOINT", "http://localhost:4317")
BICEP_TEMPLATE_PATH = os.environ.get("BICEP_TEMPLATE_PATH", "infra/main.bicep")
AZURE_SUBSCRIPTION_ID = os.environ.get("AZURE_SUBSCRIPTION_ID", "")
CI_SKIP_AZURE_DEPLOY = os.environ.get("CI_SKIP_AZURE_DEPLOY", "true").lower() == "true"

EXPECTED_COSMOS_CONTAINERS = [
    "claims",
    "documents",
    "audit-trails",
    "vector-metadata",
    "knowledge-base"
]

EXPECTED_BLOB_CONTAINERS = [
    "pharmaceutical-docs",
    "processed-output",
    "knowledge-base-docs"
]

EXPECTED_API_VERSIONS = ["v1", "v2"]

EXPECTED_LOG_FIELDS = ["trace_id", "span_id", "service_name", "timestamp", "level", "message"]


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def async_client():
    """Shared httpx.AsyncClient for all API tests in this module."""
    async with httpx.AsyncClient(base_url=API_GATEWAY_BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="module")
def az_cli_available():
    """Check whether Azure CLI is available in the CI runner."""
    result = subprocess.run(["az", "--version"], capture_output=True, text=True)
    return result.returncode == 0


def run_az_command(args: list) -> dict:
    """Helper: run an az CLI command and return parsed JSON output."""
    result = subprocess.run(
        ["az"] + args + ["--output", "json"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        pytest.fail(f"az CLI command failed: {result.stderr}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


# ---------------------------------------------------------------------------
# TC-002-001: Cosmos DB Provisioning via Bicep
# STORY-1, STORY-6
# ---------------------------------------------------------------------------

class TestCosmosDBProvisioning:
    """TC-002-001 — Cosmos DB Account and Containers Provisioned via Bicep."""

    @pytest.mark.skipif(CI_SKIP_AZURE_DEPLOY, reason="Skipping live Azure deployment in unit CI; enable with CI_SKIP_AZURE_DEPLOY=false")
    def test_bicep_template_validates_without_errors(self):
        """
        TC-002-001 / STORY-1 / STORY-6
        Validates that the root Bicep main template passes 'az bicep build'
        without compilation or validation errors.
        """
        # TC-002-001 Step 1: validate Bicep template syntax
        assert os.path.exists(BICEP_TEMPLATE_PATH), (
            f"Bicep template not found at {BICEP_TEMPLATE_PATH}"
        )
        result = subprocess.run(
            ["az", "bicep", "build", "--file", BICEP_TEMPLATE_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Bicep template validation failed.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    @pytest.mark.skipif(CI_SKIP_AZURE_DEPLOY, reason="Skipping live Azure provisioning check in unit CI")
    def test_cosmos_db_account_exists_and_running(self, az_cli_available):
        """
        TC-002-001 / STORY-1
        Step 2: Confirms the Cosmos DB account is provisioned and in a
        'Succeeded' provisioning state after 'azd up'.
        """
        assert az_cli_available, "Azure CLI not available in this runner"
        cosmos_account = run_az_command([
            "cosmosdb", "show",
            "--name", COSMOS_DB_ACCOUNT_NAME,
            "--resource-group", COSMOS_DB_RESOURCE_GROUP
        ])
        assert cosmos_account.get("provisioningState") == "Succeeded", (
            f"Cosmos DB account provisioning state is not Succeeded: "
            f"{cosmos_account.get('provisioningState')}"
        )
        assert cosmos_account.get("name") == COSMOS_DB_ACCOUNT_NAME

    @pytest.mark.skipif(CI_SKIP_AZURE_DEPLOY, reason="Skipping live Azure container listing in unit CI")
    def test_cosmos_db_required_containers_exist(self, az_cli_available):
        """
        TC-002-001 / STORY-1 / STORY-6
        Step 3: Lists all containers in the Cosmos DB account and asserts
        that all expected containers are present with correct IDs.
        """
        assert az_cli_available, "Azure CLI not available in this runner"
        # Assumption: database name is 'sllip-db'; adjust via env var if needed
        db_name = os.environ.get("COSMOS_DB_DATABASE_NAME", "sllip-db")
        containers_response = run_az_command([
            "cosmosdb", "sql", "container", "list",
            "--account-name", COSMOS_DB_ACCOUNT_NAME,
            "--resource-group", COSMOS_DB_RESOURCE_GROUP,
            "--database-name", db_name
        ])
        existing_ids = [
            c["name"] for c in containers_response
            if isinstance(containers_response, list)
        ]
        for expected in EXPECTED_COSMOS_CONTAINERS:
            assert expected in existing_ids, (
                f"Expected Cosmos DB container '{expected}' not found. "
                f"Existing containers: {existing_ids}"
            )

    def test_bicep_template_file_exists_in_repo(self):
        """
        TC-002-001 / STORY-1
        Lightweight CI check: asserts the Bicep template file is committed
        to the repository at the expected path (runs without Azure credentials).
        """
        assert os.path.isfile(BICEP_TEMPLATE_PATH), (
            f"Bicep template missing from repository at: {BICEP_TEMPLATE_PATH}"
        )

    def test_bicep_template_contains_cosmos_resource(self):
        """
        TC-002-001 / STORY-1
        Parses the Bicep template text and asserts it references
        'Microsoft.DocumentDB/databaseAccounts' (Cosmos DB resource type),
        confirming Cosmos DB is declared in IaC.
        """
        if not os.path.isfile(BICEP_TEMPLATE_PATH):
            pytest.skip("Bicep template not found; skipping content check")
        with open(BICEP_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Microsoft.DocumentDB/databaseAccounts" in content, (
            "Bicep template does not declare a Cosmos DB resource "
            "(Microsoft.DocumentDB/databaseAccounts)"
        )


# ---------------------------------------------------------------------------
# TC-002-002: Blob Storage Provisioning
# STORY-1, STORY-3
# ---------------------------------------------------------------------------

class TestBlobStorageProvisioning:
    """TC-002-002 — Azure Blob Storage Account and Containers Provisioned."""

    def test_bicep_template_contains_storage_resource(self):
        """
        TC-002-002 / STORY-1 / STORY-3
        Asserts the Bicep template declares a Storage Account resource
        (Microsoft.Storage/storageAccounts).
        """
        if not os.path.isfile(BICEP_TEMPLATE_PATH):
            pytest.skip("Bicep template not found; skipping content check")
        with open(BICEP_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Microsoft.Storage/storageAccounts" in content, (
            "Bicep template does not declare a Storage Account resource"
        )

    @pytest.mark.skipif(CI_SKIP_AZURE_DEPLOY, reason="Skipping live Azure storage check in unit CI")
    def test_storage_account_exists_and_available(self, az_cli_available):
        """
        TC-002-002 / STORY-1
        Confirms Azure Blob Storage account is provisioned and in
        'Succeeded' state.
        """
        assert az_cli_available, "Azure CLI not available"
        storage = run_az_command([
            "storage", "account", "show",
            "--name", STORAGE_ACCOUNT_NAME,
            "--resource-group", STORAGE_RESOURCE_GROUP
        ])
        assert storage.get("provisioningState") == "Succeeded", (
            f"Storage account provisioning state: {storage.get('provisioningState')}"
        )

    @pytest.mark.skipif(CI_SKIP_AZURE_DEPLOY, reason="Skipping live blob container listing in unit CI")
    def test_required_blob_containers_exist(self, az_cli_available):
        """
        TC-002-002 / STORY-3
        Lists blob containers and asserts all expected containers are present.
        """
        assert az_cli_available, "Azure CLI not available"
        connection_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
        if not connection_str:
            pytest.skip("AZURE_STORAGE_CONNECTION_STRING not set")
        containers_output = run_az_command([
            "storage", "container", "list",
            "--connection-string", connection_str
        ])
        existing_names = [
            c["name"] for c in containers_output
            if isinstance(containers_output, list)
        ]
        for expected in EXPECTED_BLOB_CONTAINERS:
            assert expected in existing_names, (
                f"Expected blob container '{expected}' not found. "
                f"Existing: {existing_names}"
            )


# ---------------------------------------------------------------------------
# TC-002-003: API Gateway Versioned Routing
# STORY-3, STORY-4, STORY-5
# ---------------------------------------------------------------------------

class TestAPIGatewayVersionedRouting:
    """TC-002-003 — API Gateway responds correctly on versioned route prefixes."""

    @pytest.mark.asyncio
    async def test_api_v1_health_endpoint_returns_200(self, async_client):
        """
        TC-002-003 / STORY-3 / STORY-4
        Sends GET /v1/health to the API Gateway and asserts HTTP 200,
        confirming v1 routing is active.
        """
        response = await async_client.get("/v1/health")
        assert response.status_code == 200, (
            f"Expected 200 from /v1/health, got {response.status_code}: {response.text}"
        )

    @pytest.mark.asyncio
    async def test_api_v2_health_endpoint_returns_200(self, async_client):
        """
        TC-002-003 / STORY-3 / STORY-5
        Sends GET /v2/health and asserts HTTP 200, confirming v2
        versioned routing is active in the gateway.
        """
        response = await async_client.get("/v2/health")
        assert response.status_code == 200, (
            f"Expected 200 from /v2/health, got {response.status_code}: {response.text}"
        )

    @pytest.mark.asyncio
    async def test_unversioned_root_returns_redirect_or_200(self, async_client):
        """
        TC-002-003 / STORY-3
        Sends GET / to the API Gateway root and asserts the gateway
        does not return 5xx (gateway is reachable and routing is configured).
        """
        response = await async_client.get("/", follow_redirects=True)
        assert response.status_code < 500, (
            f"API Gateway root returned server error: {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_invalid_version_prefix_returns_404(self, async_client):
        """
        TC-002-003 / STORY-3
        Sends GET /v99/health to assert the gateway returns 404 for
        unsupported API version prefixes (no passthrough to undefined routes).
        """
        response = await async_client.get("/v99/health")
        assert response.status_code == 404, (
            f"Expected 404 for invalid version prefix /v99, got {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_api_gateway_response_includes_version_header(self, async_client):
        """
        TC-002-003 / STORY-4 / STORY-5
        Asserts that the API Gateway attaches an 'X-API-Version' or
        'api-version' response header indicating the active route version.
        """
        response = await async_client.get("/v1/health")
        version_header = (
            response.headers.get("X-API-Version")
            or response.headers.get("api-version")
            or response.headers.get("x-api-version")
        )
        assert version_header is not None, (
            "API Gateway response missing version header "
            "(expected X-API-Version or api-version)"
        )

    @pytest.mark.asyncio
    async def test_v1_claims_route_reachable(self, async_client):
        """
        TC-002-003 / STORY-4
        Sends GET /v1/claims to assert the versioned claims endpoint
        is routed correctly (200 or 401/403 for auth — not 404/502).
        """
        response = await async_client.get("/v1/claims")
        assert response.status_code not in [404, 502, 503], (
            f"Claims route unreachable via API Gateway v1: {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_v1_documents_route_reachable(self, async_client):
        """
        TC-002-003 / STORY-3 / STORY-5
        Sends GET /v1/documents to verify the documents endpoint is
        routed through the API Gateway (not returning gateway errors).
        """
        response = await async_client.get("/v1/documents")
        assert response.status_code not in [404, 502, 503], (
            f"Documents route unreachable via API Gateway v1: {response.status_code}"
        )


# ---------------------------------------------------------------------------
# TC-002-004: Cosmos DB Schema Integrity
# STORY-1, STORY-6
# ---------------------------------------------------------------------------

class TestCosmosDBSchemaIntegrity:
    """TC-002-004 — Cosmos DB containers enforce expected partition key schema."""

    @pytest.mark.skipif(CI_SKIP_AZURE_DEPLOY, reason="Requires live Cosmos DB access")
    @pytest.mark.parametrize("container_name,expected_partition_key", [
        ("claims", "/documentId"),
        ("documents", "/tenantId"),
        ("audit-trails", "/sessionId"),
        ("vector-metadata", "/claimId"),
        ("knowledge-base", "/therapeuticArea"),
    ])
    def test_cosmos_container_partition_key_schema(
        self, az_cli_available, container_name, expected_partition_key
    ):
        """
        TC-002-004 / STORY-1 / STORY-6
        For each required Cosmos DB container, asserts the partition key
        path matches the schema defined in the SRS/data model.
        """
        assert az_cli_available, "Azure CLI not available"
        db_name = os.environ.get("COSMOS_DB_DATABASE_NAME", "sllip-db")
        container_info = run_az_command([
            "cosmosdb", "sql", "container", "show",
            "--account-name", COSMOS_DB_ACCOUNT_NAME,
            "--resource-group", COSMOS_DB_RESOURCE_GROUP,
            "--database-name", db_name,
            "--name", container_name
        ])
        partition_key_paths = (
            container_info
            .get("resource", {})
            .get("partitionKey", {})
            .get("paths", [])
        )
        assert expected_partition_key in partition_key_paths, (
            f"Container '{container_name}': expected partition key "
            f"'{expected_partition_key}', found: {partition_key_paths}"
        )

    @pytest.mark.asyncio
    async def test_claims_api_returns_schema_conformant_response(self, async_client):
        """
        TC-002-004 / STORY-6
        Sends GET /v1/claims with a test document ID and asserts the
        response payload contains required top-level schema fields:
        'documentId', 'claims', 'status'.
        This validates the Cosmos DB read path produces schema-conformant output.
        """
        test_doc_id = os.environ.get("TEST_DOCUMENT_ID", "test-doc-001")
        response = await async_client.get(
            f"/v1/claims",
            params={"documentId": test_doc_id},
            headers={"Authorization": f"Bearer {os.environ.get('TEST_API_TOKEN', 'test-token')}"}
        )
        # Accept 200 (data found) or 404 (no test data in CI) — not a schema error
        if response.status_code == 200:
            payload = response.json()
            for field in ["documentId", "claims", "status"]:
                assert field in payload, (
                    f"Claims response missing required schema field '{field}'. "
                    f"Payload keys: {list(payload.keys())}"
                )
        elif response.status_code == 404:
            # 404 acceptable in CI where no seed data exists
            pass
        else:
            pytest.fail(
                f"Unexpected status {response.status_code} from /v1/claims: {response.text}"
            )


# ---------------------------------------------------------------------------
# TC-002-005: Centralized Logging with OpenTelemetry
# STORY-4, STORY-5
# ---------------------------------------------------------------------------

class TestCentralizedLoggingOpenTelemetry:
    """TC-002-005 — OpenTelemetry trace/span propagation across API requests."""

    @pytest.mark.asyncio
    async def test_api_response_contains_traceparent_header(self, async_client):
        """
        TC-002-005 / STORY-4 / STORY-5
        Sends a request to /v1/health and asserts the response includes
        a 'traceparent' header (W3C Trace Context), confirming OTel
        instrumentation is active on the API Gateway.
        """
        response = await async_client.get("/v1/health")
        assert response.status_code == 200
        traceparent = response.headers.get("traceparent")
        assert traceparent is not None, (
            "Response missing 'traceparent' header — OTel instrumentation "
            "may not be configured on the API Gateway"
        )

    @pytest.mark.asyncio
    async def test_traceparent_header_format_is_valid_w3c(self, async_client):
        """
        TC-002-005 / STORY-4
        Asserts the 'traceparent' header conforms to W3C format:
        '00-<traceId:32hex>-<parentId:16hex>-<flags:2hex>'.
        """
        import re
        response = await async_client.get("/v1/health")
        traceparent = response.headers.get("traceparent", "")
        if not traceparent:
            pytest.skip("traceparent header not present; skipping format validation")
        w3c_pattern = re.compile(
            r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$"
        )
        assert w3c_pattern.match(traceparent), (
            f"traceparent header does not conform to W3C format: '{traceparent}'"
        )

    @pytest.mark.asyncio
    async def test_structured_log_endpoint_emits_required_fields(self, async_client):
        """
        TC-002-005 / STORY-5
        Sends a request to /v1/logs/last (internal diagnostics endpoint)
        and verifies the log payload contains all required OTel fields:
        trace_id, span_id, service_name, timestamp, level, message.
        Skips gracefully if the diagnostics endpoint is not exposed in CI.
        """
        response = await async_client.get(
            "/v1/logs/last",
            headers={"Authorization": f"Bearer {os.environ.get('TEST_API_TOKEN', 'test-token')}"}
        )
        if response.status_code in [404, 403]:
            pytest.skip("/v1/logs/last not exposed in this environment; skipping")
        assert response.status_code == 200, (
            f"Log diagnostics endpoint returned {response.status_code}: {response.text}"
        )
        log_entry = response.json()
        for field in EXPECTED_LOG_FIELDS:
            assert field in log_entry, (
                f"Log entry missing required OTel field '{field}'. "
                f"Available fields: {list(log_entry.keys())}"
            )

    @pytest.mark.asyncio
    async def test_trace_id_propagated_across_downstream_service(self, async_client):
        """
        TC-002-005 / STORY-4 / STORY-5
        Sends a request with a custom 'traceparent' header and asserts
        the API Gateway echoes the same trace ID in the response,
        confirming distributed trace context propagation.
        """
        custom_traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        response = await async_client.get(
            "/v1/health",
            headers={"traceparent": custom_traceparent}
        )
        assert response.status_code == 200
        response_traceparent = response.headers.get("traceparent", "")
        if response_traceparent:
            injected_trace_id = custom_traceparent.split("-")[1]
            response_trace_id = response_traceparent.split("-")[1] if response_traceparent else ""
            assert response_trace_id == injected_trace_id, (
                f"Trace ID not propagated. Sent: {injected_trace_id}, "
                f"Received: {response_trace_id}"
            )


# ---------------------------------------------------------------------------
# TC-002-006: Bicep IaC Template Validation (Static Analysis)
# STORY-1
# ---------------------------------------------------------------------------

class TestBicepIaCTemplateValidation:
    """TC-002-006 — Static validation and structure checks for Bicep IaC templates."""

    INFRA_DIR = os.environ.get("INFRA_DIR", "infra")

    def test_infra_directory_exists(self):
        """
        TC-002-006 / STORY-1
        Asserts the infra/ directory exists at the expected repository path.
        """
        assert os.path.isdir(self.INFRA_DIR), (
            f"infra/ directory not found at '{self.INFRA_DIR}'"
        )

    def test_main_bicep_file_exists(self):
        """
        TC-002-006 / STORY-1
        Asserts infra/main.bicep (root orchestration template) exists.
        """
        assert os.path.isfile(BICEP_TEMPLATE_PATH), (
            f"Root Bicep template not found: {BICEP_TEMPLATE_PATH}"
        )

    def test_bicep_template_declares_cosmos_db(self):
        """
        TC-002-006 / STORY-1
        Static check: Bicep template references Cosmos DB resource type.
        """
        if not os.path.isfile(BICEP_TEMPLATE_PATH):
            pytest.skip("Bicep template not found")
        with open(BICEP_TEMPLATE_PATH, "r") as f:
            content = f.read()
        assert "Microsoft.DocumentDB" in content, (
            "Bicep template missing Cosmos DB declaration"
        )

    def test_bicep_template_declares_container_apps(self):
        """
        TC-002-006 / STORY-1
        Static check: Bicep template references Azure Container Apps
        (Microsoft.App/containerApps) — primary compute layer per SRS.
        """
        if not os.path.isfile(BICEP_TEMPLATE_PATH):
            pytest.skip("Bicep template not found")
        with open(BICEP_TEMPLATE_PATH, "r") as f:
            content = f.read()
        assert "Microsoft.App/containerApps" in content, (
            "Bicep template missing Azure Container Apps declaration"
        )

    def test_bicep_template_declares_storage_account(self):
        """
        TC-002-006 / STORY-1
        Static check: Bicep template includes Storage Account declaration.
        """
        if not os.path.isfile(BICEP_TEMPLATE_PATH):
            pytest.skip("Bicep template not found")
        with open(BICEP_TEMPLATE_PATH, "r") as f:
            content = f.read()
        assert "Microsoft.Storage/storageAccounts" in content, (
            "Bicep template missing Storage Account declaration"
        )

    def test_bicep_template_declares_ai_search(self):
        """
        TC-002-006 / STORY-1 / STORY-5
        Static check: Bicep template references Azure AI Search
        (Microsoft.Search/searchServices) per SRS vector storage requirement.
        """
        if not os.path.isfile(BICEP_TEMPLATE_PATH):
            pytest.skip("Bicep template not found")
        with open(BICEP_TEMPLATE_PATH, "r") as f:
            content = f.read()
        assert "Microsoft.Search/searchServices" in content, (
            "Bicep template missing Azure AI Search declaration (required for vector storage)"
        )

    def test_bicep_az_build_compiles_without_error(self):
        """
        TC-002-006 / STORY-1
        Runs 'az bicep build' to compile the template and asserts
        zero exit code (no syntax or structural errors).
        Skipped if Azure CLI / Bicep CLI is not installed in the runner.
        """
        check = subprocess.run(["az", "bicep", "--help"], capture_output=True)
        if check.returncode != 0:
            pytest.skip("az bicep CLI not available in this runner")
        if not os.path.isfile(BICEP_TEMPLATE_PATH):
            pytest.skip("Bicep template not found")
        result = subprocess.run(
            ["az", "bicep", "build", "--file", BICEP_TEMPLATE_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"az bicep build failed.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    @pytest.mark.skipif(
        not os.path.isfile("infra/main.bicep"),
        reason="Bicep template not present"
    )
    def test_bicep_parameter_file_exists_for_dev_environment(self):
        """
        TC-002-006 / STORY-1
        Asserts a dev-environment parameter file exists alongside main.bicep,
        e.g. infra/main.parameters.dev.json or azure.yaml.
        """
        param_candidates = [
            "infra/main.parameters.dev.json",
            "infra/parameters.dev.json",
            "azure.yaml",
            ".azure/config"
        ]
        found = any(os.path.isfile(p) or os.path.isdir(p) for p in param_candidates)
        assert found, (
            f"No dev environment parameter file found. Checked: {param_candidates}"
        )
