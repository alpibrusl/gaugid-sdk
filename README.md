# Gaugid SDK

[![CI](https://github.com/alpibrusl/gaugid-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/alpibrusl/gaugid-sdk/actions/workflows/ci.yml)
[![License: EUPL-1.2](https://img.shields.io/badge/License-EUPL--1.2-blue.svg)](https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Official SDK for [Gaugid](https://gaugid.com)—the consent-first profile layer for AI agents. Gaugid SDK lets you integrate with the Gaugid (a2p-cloud) service so your agents can access user profiles with proper consent and privacy controls. It implements the [a2p protocol](https://a2p-protocol.org) and adds OAuth flows, connection tokens, and framework integrations.

---

## About

Gaugid SDK is maintained as open source to support the a2p ecosystem and give developers a single, protocol-compliant way to build consent-aware AI applications. The SDK is used in production with the Gaugid service and is designed for reliability and long-term compatibility.

**Project status:** Alpha — API is stable for core use cases; optional integrations and docs are still evolving. We follow [semantic versioning](https://semver.org) and document breaking changes in the [changelog](CHANGELOG.md).

---

## Features

- **Protocol-compliant** — Full support for a2p v0.1.0 (DIDs, A2P-Signature, agent registration)
- **OAuth & connection tokens** — Built-in flows for user-facing apps
- **Multi-framework** — Optional integrations for Google ADK, LangGraph, Anthropic, OpenAI, LlamaIndex, Agno, CrewAI
- **Python & TypeScript** — Official SDKs for both ecosystems
- **Async-first** — Designed for modern async/await usage

---

## Repository structure

| Path | Description |
|------|-------------|
| [gaugid-sdk-python/](gaugid-sdk-python/) | Python SDK (PyPI: `gaugid`) |
| [gaugid-sdk-typescript/](gaugid-sdk-typescript/) | TypeScript SDK (npm: `@gaugid/sdk`) |
| [examples/](examples/) | Examples, notebooks, and use-case demos |
| [docs/](docs/) | Documentation (MkDocs) |

---

## Quick start (Python)

```bash
pip install gaugid
```

```python
import asyncio
from gaugid import GaugidClient

async def main():
    client = GaugidClient(connection_token="your_connection_token")
    profile = await client.get_profile(scopes=["a2p:preferences"])
    print(profile)
    await client.close()

asyncio.run(main())
```

## Quick start (TypeScript)

```bash
npm install @gaugid/sdk
# or: pnpm add @gaugid/sdk
```

```typescript
import { GaugidClient } from "@gaugid/sdk";

const client = new GaugidClient({
  connectionToken: "your_connection_token",
});
const profile = await client.getProfile({ scopes: ["a2p:preferences"] });
console.log(profile);
```

---

## Documentation

- **Documentation site:** [docs.gaugid.com](https://docs.gaugid.com)
- **Python SDK:** [gaugid-sdk-python/README.md](gaugid-sdk-python/README.md)
- **TypeScript SDK:** [gaugid-sdk-typescript/README.md](gaugid-sdk-typescript/README.md)
- **Examples:** [examples/README.md](examples/README.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)

---

## Support

- **Questions & ideas:** [GitHub Discussions](https://github.com/alpibrusl/gaugid-sdk/discussions)
- **Bugs & features:** [GitHub Issues](https://github.com/alpibrusl/gaugid-sdk/issues)
- **Security:** See [SECURITY.md](SECURITY.md)
- **Getting help:** See [SUPPORT.md](SUPPORT.md)

---

## Contributing

We welcome contributions from the community. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Code of conduct and how to report issues
- Development setup and pull request process
- [Open-source checklist](docs/OPEN_SOURCE_CHECKLIST.md)
- [Internal content policy](docs/INTERNAL_CONTENT_POLICY.md)
- [Versioning and release](docs/VERSIONING.md)

---

## Governance

This project is maintained by the Gaugid team. How we make decisions and who to contact is described in [GOVERNANCE.md](GOVERNANCE.md).

---

## License

This project is licensed under the **European Union Public Licence v. 1.2 (EUPL-1.2)**. See [LICENSE](LICENSE) for the full text.

---

## Links

| Resource | URL |
|----------|-----|
| Gaugid | [gaugid.com](https://gaugid.com) |
| a2p protocol | [a2p-protocol.org](https://a2p-protocol.org) |
| a2p SDK (Python) | [PyPI](https://pypi.org/project/a2p-sdk/) |
| Repository | [github.com/alpibrusl/gaugid-sdk](https://github.com/alpibrusl/gaugid-sdk) |

---

*Copyright © Gaugid SDK Contributors. Gaugid is a trademark of its respective owner. This SDK is not affiliated with or endorsed by the a2p protocol foundation; it is an independent implementation.*
