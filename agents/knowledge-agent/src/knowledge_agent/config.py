from agent_core import AgentConfig

config = AgentConfig(
    name="knowledge-agent",
    description=("Searches company documentation: handbook, policies, procedures, FAQ"),
    instructions="""\
You are a company knowledge assistant.

Answer questions using your tools and document search.
Always cite which document or section your answer comes from.
If you cannot find the answer, say so clearly.""",
    tools=["search_documents", "list_available_documents"],
    file_search_enabled=True,
)
