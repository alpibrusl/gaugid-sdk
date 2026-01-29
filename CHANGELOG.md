# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for the Python and TypeScript packages.

## [Unreleased]

### Added

- Open-source release: root README, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG
- GitHub issue and pull request templates
- Root CI workflow for Python SDK

### Changed

- Python SDK uses `a2p-sdk` from PyPI (>=0.1.1)
- Default namespace for GaugidClient is `"gaugid"` when not provided

## [0.1.0] - 2024

### Added

- **Python SDK** (`gaugid-sdk-python`)
  - GaugidClient and GaugidStorage
  - OAuth flow and connection tokens
  - A2P-Signature support
  - DID resolution and agent registration
  - Optional integrations: ADK, LangGraph, Anthropic, OpenAI, LlamaIndex, Agno, CrewAI
- **TypeScript SDK** (`gaugid-sdk-typescript`)
  - GaugidClient and GaugidStorage
  - OAuth and connection token support
  - A2P-Signature and DID resolution
  - Framework integration stubs
- **Documentation** (MkDocs)
- **Examples** (frameworks, notebooks, use-cases)

[Unreleased]: https://github.com/alpibrusl/gaugid-sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/alpibrusl/gaugid-sdk/releases/tag/v0.1.0
