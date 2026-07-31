# Release Process

The SDK follows Semantic Versioning independently from the `/api/v1` API version.

1. Update `CHANGELOG.md`.
2. Run `ruff check .`, `mypy --no-site-packages pharos_sdk`, and `pytest`.
3. Create an immutable signed tag such as `v0.1.0`.
4. Push the tag. GitHub Actions publishes to PyPI through Trusted Publishing.
