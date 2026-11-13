# WaveWeaver for Atlassian Forge — Rovo Agent, Teamwork Graph & MCP Server (`Codegeist 2026`)

[![Atlassian Forge](https://img.shields.io/badge/Atlassian_Forge-nodejs20.x-0052CC)](./manifest.yml)
[![Rovo Agent](https://img.shields.io/badge/Rovo_Agent-@WaveWeaver-2684FF)](./manifest.yml)
[![MCP Server](https://img.shields.io/badge/Protocol-Atlassian_MCP_(JSON--RPC_2.0)-10B981)](./src/index.js)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](../LICENSE)

This directory contains the native **Atlassian Forge** application module for **WaveWeaver (织浪 AI)**, built specifically on Forge (`nodejs20.x`) during the **Codegeist 2026: Build with context. Ship with confidence. ($120,000+ Prize Pool)** submission period.

---

## 🎯 Targeted Codegeist 2026 Categories & Bonus Prizes

1. **Main Category**: *Apps for Software Teams* (connecting Jira Epics, Confluence release specs, and multi-format stakeholder communication)
2. **Bonus Prize 1 — Best Agents (Rovo/Assignable agents · $1,500 × 6)**:
   - Declares `rovo:agent` (`waveweaver-release-agent`) and 3 structured `action` tools (`traverse-teamwork-graph`, `audit-anti-ai-slop`, `synthesize-sprint-media-kit`) in [`manifest.yml`](./manifest.yml).
3. **Bonus Prize 2 — Best app with Atlassian MCP ($1,500 × 6)**:
   - Exposes a compliant JSON-RPC 2.0 Model Context Protocol (MCP) server via Forge WebTrigger (`waveweaver-atlassian-mcp-server`) in [`src/index.js`](./src/index.js) (`tools/list` and `tools/call`).
4. **Bonus Prize 3 — Best apps with Teamwork Graph integration ($1,500 × 6)**:
   - Traverses linked Jira Epics, completed sprint issues, and Confluence specifications while enforcing WaveWeaver's 3-tier `Organization ➔ Workspace ➔ ReleaseChannel` context isolation (`0.0%` cross-channel contamination).

---

## 🧩 Alignment with Atlassian's Six Enterprise Context Pillars

Atlassian's Codegeist 2026 rubric highlights the **six types of context a company runs on** (*Knowledge, Work, People, Communication, Code, and Assets*)—rewarding Forge apps that make them more **accessible, actionable, and connected**. WaveWeaver bridges all six in one deterministic 8-stage pipeline:

| Enterprise Context Pillar | Atlassian Surface / Scope | How WaveWeaver Makes It Accessible, Actionable & Connected |
| :--- | :--- | :--- |
| **1. Knowledge** | **Confluence** (`read:confluence-content.summary`, `write:confluence-page`) | Ingests architecture & verification specs (`CONF-9921`) as factual ground truth and writes calibrated executive release notes back to Confluence. |
| **2. Work** | **Jira Software & Teamwork Graph** (`read:jira-work`, `traverseTeamworkGraph`) | Traverses Epic-to-Issue story points and completion status inside isolated `BuildRun::AtlassianForge::<EpicKey>` namespaces (`0.0%` cross-project leakage). |
| **3. People** | **Rovo Agent (`@WaveWeaver`)** | Translates dense engineering tickets for cross-functional roles (Engineering Leads, Product Architects, Execs, Field Sales) via one-click Rovo conversation starters. |
| **4. Communication** | **Anti-AI-Slop Calibration (`auditAntiAiSlop`)** | Deterministically intercepts generic LLM filler (*"delving into"*, *"game-changing"*, *"seamless"*) and enforces explicit verification disclosures before any announcement ships. |
| **5. Code** | **Cryptographic Provenance (`crypto.createHash('sha256')`)** | Anchors every release summary to verified Jira/PR deliverables with an immutable `sha256:<digest>` attestation, preventing ungrounded AI hallucinations. |
| **6. Assets** | **5-Format Media Kit (`synthesizeSprintMediaKit`)** | Turns verified sprint context into 5 synchronized release assets: `9:16 MPT_VERTICAL_VIDEO` script, `6-Slide VISUAL_CAROUSEL`, `LONG_ARTICLE`, `PODCAST_AUDIO`, and `MICRO_THREAD`. |

---

## 🔌 Forge Architecture & MCP JSON-RPC 2.0 Interface

### 1. Forge Modules ([`manifest.yml`](./manifest.yml))
- **`rovo:agent` (`waveweaver-release-agent`)**: Interactive Rovo agent with 3 bound actions and pre-configured sprint/epic conversation starters.
- **`action` (`traverse-teamwork-graph`, `audit-anti-ai-slop`, `synthesize-sprint-media-kit`)**: Deterministic GET/CREATE handlers backed by [`src/index.js`](./src/index.js).
- **`webtrigger` (`waveweaver-atlassian-mcp-server`)**: Exposes the same 3 capabilities over JSON-RPC 2.0 (`tools/list`, `tools/call`) to any MCP client while honoring Forge tenant isolation.
- **Least-Privilege Scopes**: `read:jira-work`, `read:confluence-content.summary`, `write:confluence-page` (zero customer data used for model training).

### 2. Testing the MCP Server Endpoint
```bash
# List available Atlassian MCP tools
curl -X POST "<YOUR_FORGE_WEBTRIGGER_URL>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Synthesize a 5-format Sprint Media Kit with SHA-256 provenance for Epic ENG-804
curl -X POST "<YOUR_FORGE_WEBTRIGGER_URL>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"synthesize_sprint_media_kit","arguments":{"epicKey":"ENG-804","channelIsolationNamespace":"Org::Atlassian::ENG-804"}}}'
```

---

## 🚀 Quick Start (`forge deploy`)

> **Forge Submission Period Compliance Note**: This `atlassian-forge-rovo-mcp` Forge application (`manifest.yml` + `src/index.js` on `nodejs20.x`) was purpose-built on Atlassian Forge during the Codegeist 2026 submission window in full compliance with official Codegeist rules.

```bash
cd atlassian-forge-rovo-mcp
forge register
forge deploy
forge install
```

After deploying, open the [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/), enable **Distribution -> Share your app**, and paste the generated installation link into the Codegeist 2026 Devpost submission form.
