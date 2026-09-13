# Contributing

Contributions are welcome. Keep adapters focused on translating one source into the provider-neutral `Notification` model and keep provider behavior out of them.

1. Use Python 3.12 and install `requirements-dev.txt`.
2. Add tests for every behavior change.
3. Run `pytest` and `python -m compileall -q gateway`.
4. Never include real device keys, tokens, secrets, domains, or personal payloads.

New sources should include authentication, malformed-payload handling, unknown-event fallback, documentation, and sanitized representative tests.

