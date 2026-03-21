# FAQ

## Can I use this without Azure?

Partially. The agent **tools** (KB search, SQL queries, etc.) work locally with mock/synthetic data — you can develop and test tools without Azure. However, the **agent orchestration** (triage routing, HandoffBuilder, tool calling by the model) requires Azure AI Foundry because the models run there.

For local-only development, you can:
- Write and unit test tools without Azure
- Run `uv run python -m agent_core.validate` to check your agent config
- Use the scaffold CLI to generate agent packages

## Can I use models other than GPT-4.1?

Yes. Any model deployed in your Azure AI Foundry project works. Set the `model` field in your agent config:

```python
config = AgentConfig(
    model="gpt-4.1-mini",   # Cheaper, good for routing
    # model="gpt-4.1",      # More capable, for complex tasks
    # model="gpt-4.1-nano", # Very cheap, for simple extraction
)
```

The triage/router agent should use `gpt-4.1-mini` — it only routes, it doesn't reason.

## How do I add my own data?

Two ways:

1. **RAG (document search)**: Drop files in `agents/my-agent/knowledge/`, upload with `uv run python -m agent_core.knowledge upload`, and set `file_search_enabled=True`. Supports PDF, Markdown, DOCX, HTML, CSV, JSON.

2. **Custom tools**: Write a tool function that queries your data source (database, API, etc.). See [Adding Agents](adding-agents.md).

## Is this production-ready?

This is a **solution accelerator** — a starting point for building production systems. The architecture is production-quality (middleware, auth, observability, Terraform IaC), but you should:

- Add your own tests and evaluation criteria
- Review security for your specific use case
- Set up monitoring and alerting
- Consider rate limiting and cost controls

## What is A2A and do I need it?

A2A (Agent-to-Agent) is an open protocol for agents to communicate across different frameworks and services. You need it when:

- Different teams build agents with different frameworks
- You want to connect agents running in different services
- You need cross-organization agent collaboration

If all your agents run on this single platform, you don't need A2A — the router handles everything internally. A2A is for connecting to **external** agents.

## What is MCP and do I need it?

MCP (Model Context Protocol) connects agents to external tools and data without writing integration code. You need it when:

- You want to connect to Confluence, Jira, SharePoint, databases, etc.
- There's an MCP server available for your data source
- You want to avoid writing custom tool wrapper code

If your tools are simple Python functions, you don't need MCP.

## How much does it cost?

See [Cost Optimization](cost-optimization.md). Rough estimates:

- **Development**: ~$5-10/month (GPT-4.1-mini for routing + occasional GPT-4.1 calls)
- **POC deployment**: ~$10/month (Basic ACR, public endpoints)
- **Enterprise**: ~$92/month (Premium ACR, private networking)

Clean up: `azd down` or `terraform destroy` to avoid ongoing costs.

## How does auto-discovery work?

The router scans the `agents/` directory at startup:

1. Finds all subdirectories (except `router`)
2. Converts kebab-case to snake_case (e.g., `my-agent` → `my_agent`)
3. Imports the Python module
4. Extracts `config` and `tools` exports
5. Registers with the AgentRegistry

No manifest, no config file, no registration code. Just follow the [plugin contract](adding-agents.md#the-plugin-contract).

## Can I contribute a new agent?

Yes! See [CONTRIBUTING.md](../CONTRIBUTING.md). A good example agent:

- Teaches a specific concept (RAG, HITL, MCP, A2A, etc.)
- Uses mock/synthetic data (no external API keys required)
- Has unit tests for its tools
- Has a clear, specific description in its config
