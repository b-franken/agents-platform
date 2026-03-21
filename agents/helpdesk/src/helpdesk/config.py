from agent_core import AgentConfig

config = AgentConfig(
    name="helpdesk-agent",
    description=(
        "IT helpdesk: troubleshoots problems using a knowledge base "
        "and manages support tickets"
    ),
    instructions="""\
You are an IT helpdesk agent.

When a user reports a problem:
1. Search the knowledge base for a matching solution.
2. If no solution is found, offer to create a support ticket.
3. When asked about tickets, use list_tickets to show them.

Always try to solve the problem before creating a ticket.""",
    tools=[
        "search_knowledge_base",
        "create_ticket",
        "list_tickets",
    ],
)
