# From Demo to Production

The included agents use local demo data (YAML files, SQLite databases, regex patterns) so the platform works out of the box without external dependencies. This guide covers how to connect real data sources.

## Per-agent migration

### helpdesk

**Demo:** YAML knowledge base files in `agents/helpdesk/knowledge/`, SQLite ticket database.

**Production:**
- Replace `_load_kb_articles()` with a Confluence or ServiceNow KB API client
- Replace SQLite with your ticketing system API (Jira, ServiceNow, Zendesk)
- Add the external API as an MCP tool: `tools: ["mcp:jira:https://your-jira.atlassian.net/mcp"]`

### data-analyst

**Demo:** SQLite database with sample employees/projects/tickets data.

**Production:**
- Replace `_connect()` in `tools.py` with a connection to your actual database
- Use environment variables for the connection string
- Add row-level security and query timeout limits

### expense-approver

**Demo:** SQLite database with sample budgets and expenses.

**Production:**
- Connect to your ERP or finance system API (SAP, NetSuite, Dynamics)
- The `@tool(approval_mode="always_require")` pattern carries over directly

### incident-triage

**Demo:** Keyword-based severity classification with in-memory incident history.

**Production:**
- Replace keyword matching with PagerDuty or Opsgenie API for real incident data
- Use Azure Cosmos DB or Redis for incident history (see `BaseContextProvider`)
- The `IncidentClassification` Pydantic model works directly as `response_format`

### code-reviewer

**Demo:** Regex-based pattern matching for code quality and security checks.

**Production:**
- Wrap real linters as subprocess tools: `ruff check --output-format json`, `bandit -f json`, `semgrep`
- Use the hosted Code Interpreter tool for running analysis in a sandbox:
  ```python
  tools=[get_code_interpreter_tool(), analyze_code_quality]
  ```

### infra-analyzer

**Demo:** Regex-based Terraform pattern matching with simulated fix application.

**Production:**
- Wrap `tfsec` or `checkov` as subprocess tools for real IaC scanning
- Replace `apply_fix` stub with actual file I/O + `git diff` for reviewable changes
- The `@tool(approval_mode="always_require")` pattern ensures human review before any change

## Monitoring

OpenTelemetry instrumentation is built in. Enable it:

```bash
ENABLE_INSTRUMENTATION=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

The middleware stack (InputGuard, LoggingAgentMiddleware, LoggingFunctionMiddleware) automatically traces all agent runs and tool calls.

## Security

- **Authentication:** Managed Identity in production (set `AZURE_CLIENT_ID`), Azure CLI for development
- **Secrets:** Store API keys in Azure Key Vault, reference via environment variables
- **Network:** Enable `enable_private_networking = true` in Terraform for VNet isolation
- **RBAC:** Terraform assigns `Cognitive Services OpenAI User` to the Container App managed identity

## Cost management

See [cost-optimization.md](cost-optimization.md) for model selection and deployment tier guidance.
