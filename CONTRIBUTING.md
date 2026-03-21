# Contributing

Thank you for your interest in contributing to Agent Platform! Whether it's a new agent, a bug fix, or a documentation improvement — we welcome it.

## Your first contribution

1. **Fork and clone** the repository
2. **Install**: `pip install uv && uv sync`
3. **Create a branch**: `git checkout -b my-feature`
4. **Make your changes**
5. **Check your work**:
   ```bash
   make lint       # Code style
   make test       # Run tests
   make validate   # Validate agents
   ```
6. **Submit a pull request** using the PR template

## Adding a new agent

The fastest way to contribute is adding a new agent. A good example agent:

- **Teaches a concept** — RAG, human-in-the-loop, MCP tools, A2A, etc.
- **Uses mock data** — no external API keys required
- **Has unit tests** — in `agents/<name>/tests/test_tools.py`
- **Has a clear description** — the triage agent reads this for routing

### Quick start

```bash
uv run python -m agent_core.scaffold my-agent --description "What it does"
# Edit agents/my-agent/src/my_agent/tools.py
# Edit agents/my-agent/src/my_agent/config.py
uv sync
uv run python -m agent_core.validate
```

See [docs/tutorial.md](docs/tutorial.md) for a complete walkthrough.

### Agent checklist

- [ ] `config.name` is unique
- [ ] `config.description` clearly says what the agent handles
- [ ] All tools have docstrings and type annotations
- [ ] Tools return strings
- [ ] Destructive tools use `@tool(approval_mode="always_require")`
- [ ] Unit tests exist for all tools
- [ ] `uv run python -m agent_core.validate` passes
- [ ] `uv run ruff check .` passes

## Other contributions

### Bug fixes
- Open an issue first to discuss the bug
- Include steps to reproduce
- Reference the issue in your PR

### Documentation
- Fix typos, improve explanations, add examples
- Documentation is in `docs/` (Markdown)
- Check that all links work

### Infrastructure
- Terraform changes in `infra/`
- CI/CD changes in `.github/workflows/`
- Test changes locally before submitting

## Development workflow

```bash
# Setup
git clone https://github.com/b-franken/agent-platform.git
cd agent-platform
pip install uv && uv sync

# Development loop
make lint        # Check code style
make format      # Auto-format
make test        # Run all tests
make validate    # Check all agents

# Run the platform
make run
```

## Code style

- **Python 3.13+** with type annotations
- **Ruff** for linting and formatting (`make lint`, `make format`)
- **Docstrings** on public functions (tools especially — the model reads these)
- Keep tools focused — one tool, one job

## Pull request process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure all checks pass: `make lint && make test && make validate`
4. Submit a PR using the [PR template](.github/PULL_REQUEST_TEMPLATE.md)
5. A maintainer will review your PR

## Reporting issues

Use the [issue templates](https://github.com/b-franken/agent-platform/issues/new/choose) for:
- **Bug reports** — something isn't working
- **Feature requests** — an idea for improvement
- **New agent proposals** — a new example agent you'd like to see
