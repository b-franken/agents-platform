from agent_core import AgentConfig

config = AgentConfig(
    name="code-reviewer-agent",
    description=(
        "Code review demo — regex-based quality and security pattern scanning"
    ),
    instructions="""\
You are a code review agent.

When a user submits code for review:
1. Run analyze_code_quality to find common issues.
2. Run check_security_patterns to detect security anti-patterns.
3. Run suggest_improvements to offer refactoring ideas.

Present findings grouped by severity. Be constructive and specific.""",
    tools=[
        "analyze_code_quality",
        "check_security_patterns",
        "suggest_improvements",
    ],
)
