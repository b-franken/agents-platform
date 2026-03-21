# Agent Platform: Responsible AI FAQ

## What is the Agent Platform?

The Agent Platform is an open-source, plug-and-play multi-agent system built on [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) and [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/). It provides a reference architecture for building, connecting, and deploying AI agents that work together using open standards like the [A2A protocol](https://a2a-protocol.org/) and [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

The platform includes example agents (helpdesk, knowledge search, data analysis, expense approval) that demonstrate common enterprise patterns such as RAG, human-in-the-loop approval, and multi-agent orchestration.

## What can the Agent Platform do?

- Route user questions to specialist AI agents based on the question's intent
- Search knowledge bases and return grounded answers with citations
- Execute read-only SQL queries against databases using natural language
- Create support tickets and submit expenses with human approval before execution
- Connect agents across services and frameworks via the A2A protocol
- Integrate with external tools (Confluence, Jira, SharePoint) via MCP

## What are the intended uses?

This solution accelerator is provided as an open-source reference implementation under the [MIT license](LICENSE). It is intended to:

- Help developers learn multi-agent patterns on Azure AI Foundry
- Serve as a starting point for building custom agent systems
- Demonstrate enterprise patterns (authentication, observability, human-in-the-loop)

All AI-generated output is for informational purposes only and should be reviewed by a human before acting on it. This platform is not a managed service and does not come with support guarantees.

## How was the Agent Platform evaluated?

The platform includes an evaluation suite (`evals/`) that tests:

- **Routing accuracy** — Does the triage agent hand off to the correct specialist?
- **Tool selection** — Does each specialist call the right tool for a given question?
- **Response quality** — Do responses contain relevant, factual information?

These evaluations require Azure credentials and make real API calls. They are designed to be extended as new agents are added. See [Microsoft Responsible AI principles](https://www.microsoft.com/ai/responsible-ai) for the broader framework guiding this work.

## What are the limitations and how can users minimize them?

**AI model limitations:**
- Agents rely on Azure OpenAI models which may produce inaccurate, incomplete, or biased responses
- Routing decisions depend on the triage agent's interpretation — misrouting can occur for ambiguous questions
- SQL generation by the data analyst agent may produce incorrect queries for complex questions

**Platform limitations:**
- Built on Microsoft Agent Framework RC5 and A2A beta — APIs may change before GA
- Requires an Azure subscription with Azure AI Foundry access
- Example agents use mock/sample data — they are not connected to real enterprise systems
- No built-in rate limiting or token budget enforcement

**How to minimize risks:**
- Use `@tool(approval_mode="always_require")` on any tool that creates, modifies, or deletes data
- Review the InputGuard middleware configuration for input length and conversation turn limits
- Enable sensitive data masking in production (`ENABLE_SENSITIVE_DATA=false`)
- Run the evaluation suite when adding or modifying agents
- Monitor agent behavior through the OpenTelemetry integration
- Always review AI-generated SQL queries before executing them against production databases
