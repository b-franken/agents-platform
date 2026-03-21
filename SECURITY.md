# Security

## Reporting vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Use GitHub's [private vulnerability reporting](https://github.com/b-franken/agent-platform/security/advisories/new) to submit the report
3. Include steps to reproduce the issue

We will respond within 48 hours and work with you to address the issue.

## Security practices

This project follows these security practices:

- **No secrets in code** — all credentials via environment variables
- **Dependency scanning** — automated via Dependabot
- **Input validation** — InputGuard middleware limits input size and conversation turns
- **Sensitive data masking** — logging middleware masks PII patterns
- **Explicit authentication** — no credential fallback chains (see `factory.py`)
- **Least privilege** — agents only have access to their configured tools

## Dependencies

This project depends on:

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) (RC)
- [Azure Identity](https://github.com/Azure/azure-sdk-for-python) for authentication
- [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/) for model inference

Keep dependencies up to date. Review the `uv.lock` file for the full dependency tree.
