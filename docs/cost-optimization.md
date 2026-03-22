# Cost Optimization

## Model selection

The biggest cost driver is model usage. Choose the right model for each agent:

| Model | Best for | Relative cost |
|-------|----------|--------------|
| `gpt-4.1` | Complex reasoning, multi-step tasks | High |
| `gpt-4.1-mini` | Simple Q&A, classification, routing | Low |
| `gpt-4.1-nano` | Very simple tasks, extraction | Very low |

```python
config = AgentConfig(
    model="gpt-4.1-mini",       # Use mini for simple agents
    max_output_tokens=1024,     # Limit response length
)
```

The triage agent should use `gpt-4.1-mini` — it only routes, it doesn't reason.

## Token limits

Set `max_output_tokens` to the minimum your agent needs:

- Routing/classification: `512`
- Simple Q&A: `1024`
- Detailed explanations: `2048`

## Infrastructure

### Foundry hosted (default, recommended)

With `deployment_mode = "foundry"` (default), Foundry manages the agent runtime. You pay only for model tokens — no Container Apps hosting cost.

Backing resources (Cosmos DB, AI Search, Storage Account) are provisioned by the AVM module and have minimal cost at low usage. This is the most cost-effective option for most workloads.

### Container Apps (self-hosted)

With `deployment_mode = "container_apps"`:
- **POC**: Public endpoints, Basic ACR (~$10/month)
- **Enterprise**: Private endpoints, Premium ACR, VNet (~$92/month)

## Monitoring

Enable instrumentation to track token usage:

```
ENABLE_INSTRUMENTATION=true
ENABLE_CONSOLE_EXPORTERS=true
```

DevUI shows token usage per request. Use this to identify expensive agents.
