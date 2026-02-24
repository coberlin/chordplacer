# Contributing

Thanks for your interest in contributing to Chord Sheet Annotator!

## Getting Started

Setup instructions will be added as the project scaffolding is built. For now, see [chord-placer-plan.md](chord-placer-plan.md) for architecture details.

## Development Guidelines

- **Python:** managed with `uv`. Lint and format with `ruff check` and `ruff format`.
- **JavaScript/React:** lint with `eslint`, format with `prettier`.
- **Tests:** backend uses `pytest` with `pytest-cov` (minimum 80% coverage). Frontend uses Jest and React Testing Library (minimum 80% coverage). Integration tests use Playwright.
- All code must pass linting and tests before submitting a PR.

## Submitting Changes

1. Fork the repo and create a feature branch.
2. Make your changes with tests.
3. Ensure linting and tests pass.
4. Open a pull request with a clear description of what you changed and why.
