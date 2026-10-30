# WaveWeaver for Atlassian Forge — Rovo Agent, Teamwork Graph & MCP Server (`Codegeist 2026`)

This directory contains the native **Atlassian Forge** module for **WaveWeaver (织浪 AI)**, built for **Codegeist 2026 ($120,000+ Prize Pool)**.

## Targeted Codegeist 2026 Categories & Bonus Prizes

1. **Main Category**: *Apps for Software Teams* / *Apps for Business Teams*
2. **Bonus Prize 1 — Best Agents (Rovo/Assignable agents · $1,500 × 6)**:
   - Declares `rovo:agent` (`waveweaver-release-agent`) and 3 reusable `action` tools (`traverse-teamwork-graph`, `audit-anti-ai-slop`, `synthesize-sprint-media-kit`) in [`manifest.yml`](./manifest.yml).
3. **Bonus Prize 2 — Best app with Atlassian MCP ($1,500 × 6)**:
   - Exposes a JSON-RPC 2.0 Model Context Protocol (MCP) server via Forge WebTrigger (`waveweaver-atlassian-mcp-server`) in [`src/index.js`](./src/index.js).
4. **Bonus Prize 3 — Best apps with Teamwork Graph integration ($1,500 × 6)**:
   - Traverses linked Jira Epics, issues, and Confluence specifications while enforcing WaveWeaver's 3-tier `Organization ➔ Workspace ➔ ReleaseChannel` context isolation.

## Quick Start (`forge deploy`)

```bash
cd atlassian-forge-rovo-mcp
forge register
forge deploy
forge install
```

After deploying, open the [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/), enable **Distribution -> Share your app**, and paste the generated installation link into the Codegeist 2026 Devpost submission form.
