# Troubleshooting

Common issues and how to fix them.

## "ModuleNotFoundError: No module named '...'"

You need to install dependencies:

```bash
uv sync
```

If you just added a new agent, `uv sync` registers it as a workspace package.

## "Azure CLI auth failed" or "DefaultCredential failed"

Log in to Azure:

```bash
az login
```

Or set an API key in your `.env`:

```
AZURE_OPENAI_API_KEY=your-key-here
```

The platform uses explicit credential selection (no fallback chains):
1. `AZURE_OPENAI_API_KEY` set → API key auth
2. `AZURE_CLIENT_ID` set → Managed Identity (production)
3. Neither → Azure CLI credential (local development)

## "Model deployment not found" or "Resource not found"

Check your `.env` file:

```
AZURE_AI_PROJECT_ENDPOINT=https://<your-project>.services.ai.azure.com/api/projects/<project-id>
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=gpt-4.1
```

- The endpoint must include the full path with `/api/projects/<id>`
- The deployment name must match exactly what's in your Azure AI Foundry

## "Agent not discovered by the router"

The router auto-discovers agents by scanning `agents/`. Check:

1. **Package exports**: `agents/my-agent/src/my_agent/__init__.py` must export `config` and `tools`:
   ```python
   from . import tools
   from .config import config
   __all__ = ["config", "tools"]
   ```

2. **Package installed**: Run `uv sync` after creating a new agent

3. **Validation**: Run `uv run python -m agent_core.validate` — it checks all agents

4. **Naming**: Directory name must be in kebab-case (e.g., `my-agent`), which becomes snake_case for the Python package (`my_agent`)

## "Vector store not found" (RAG)

Upload your documents first:

```bash
cd agents/my-agent
uv run python -m agent_core.knowledge upload
```

Then copy the `VECTOR_STORE_ID` to your `.env` file.

## Tool not being called by the agent

- Check the **docstring**: The AI model reads the docstring to decide when to call a tool. Make it specific.
- Check `config.tools`: The function name must be listed in the config's `tools` array.
- Check the **description** in your config: The triage agent reads this to decide routing. If it's vague, questions may route to the wrong agent.

## Slow responses

- Use `gpt-4.1-mini` for simple agents (routing, classification, Q&A)
- Set `max_output_tokens` to the minimum your agent needs
- See [Cost Optimization](cost-optimization.md) for model selection tips

## Docker issues

```bash
docker compose up --build   # Rebuild after code changes
```

The Aspire Dashboard (observability) is available at `http://localhost:18888`.

## Still stuck?

- Run the pre-flight check: `uv run python scripts/preflight.py`
- Check the [FAQ](faq.md)
- [Open an issue](https://github.com/b-franken/agent-platform/issues/new/choose)
