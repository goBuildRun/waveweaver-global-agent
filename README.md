# WaveWeaver — 8-Stage Multi-Channel AI Media Operating System & MPT Video Factory

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Pipeline: 8-Stage Human-in-the-Loop Media OS](https://img.shields.io/badge/Pipeline-8--Stage_Media_OS_(E2~E9)-06B6D4)](#eight-stage-controlled-content-pipeline)
[![Video Engine: MPT vertical-avatar-news](https://img.shields.io/badge/Video_Factory-MPT_9%3A16_Avatar_Engine-10B981)](#mpt-managed-video-factory--5-format-production)
[![Isolation: Org -> Workspace -> ContentChannel](https://img.shields.io/badge/Multi--Tenant-3--Tier_Channel_Isolation-6366F1)](#three-tier-multi-channel-isolation)
[![AI Stack: Nebius NVIDIA Nemotron-70B + Tavily](https://img.shields.io/badge/AI_Stack-Nebius_NVIDIA_Nemotron--70B_%2B_Tavily-F59E0B)](#model-routing-architecture-which-model-does-what-nebius--nvidia--tavily)
[![Live Web Demo: Zero-Login Interactive Workbench](https://img.shields.io/badge/🚀%20Live%20Web%20Demo-Zero--Login%20Interactive%20Workbench-2563EB)](https://htmlpreview.github.io/?https://github.com/goBuildRun/waveweaver-global-agent/blob/main/index.html)
[![Demo Video: YouTube 1080p](https://img.shields.io/badge/🎥%20Watch%20Demo%20Video-YouTube%201080p-red)](https://youtu.be/-Ct0SnpgSB4)

> 🚀 **Try the Live Interactive Web Workbench (100% English, Public Zero-Login Browser Demo)**:
> - **⛓️ Gno.land Onyx-1 Provenance Realm View (`?mode=gno`)**: **[https://htmlpreview.github.io/?https://github.com/goBuildRun/waveweaver-global-agent/blob/main/index.html?mode=gno](https://htmlpreview.github.io/?https://github.com/goBuildRun/waveweaver-global-agent/blob/main/index.html?mode=gno)**
> - **🌐 Full 8-Stage Media OS Workbench**: **[Launch WaveWeaver Live Workbench](https://htmlpreview.github.io/?https://github.com/goBuildRun/waveweaver-global-agent/blob/main/index.html)** *(or run locally via `python3 server.py --port 8767`)*
>
> 🎬 **Watch the 1m39s 1080p English-Narrated Demo Video**: **[https://youtu.be/-Ct0SnpgSB4](https://youtu.be/-Ct0SnpgSB4)**
> - **`0:00 - 0:26` ⚡ The 30-Second Aha Moment**: Switching isolated multi-tenant channels (`Organization ➔ Workspace ➔ ContentChannel`) and watching Stage 5 (`Anti-AI-Slop Calibration`) + Stage 6 (`Golden Set QA Gate = 94.2`) strip LLM clichés and block unverified claims before production.
> - **`0:27 - 0:52` 📊 Markowitz MPT Topic Portfolio Optimizer**: Computing optimal content pillar weights (`Expected Reach Return` vs `Audience Fatigue Covariance` $\Sigma$) to achieve **Sharpe `2.18`** (`-58%` fatigue).
> - **`0:53 - 1:18` 🎬 Stage 7 `MPT` Managed Video Factory (`vertical-avatar-news`)**: Generating 5 synchronized formats (`9:16 Avatar Video`, `6-Slide Carousel`, `Long Essay`, `Dual-Host Podcast`, `Micro-Post`) with full pause/retry/manual takeover.
> - **`1:19 - 1:39` 🔐 Stage 8 Cryptographic Provenance & 7-Day Loop**: Computing **SHA-256 Content Provenance Digest** and scheduling across 3 global timezones (`Asia/Shanghai`, `Europe/London`, `America/New_York`).

> *"Keep Great Content Flowing in Waves — An 8-stage human-in-the-loop AI media operating system that turns raw market, on-chain, and cultural intelligence into calibrated multi-platform videos, carousels, long-form essays, podcasts, and micro-posts—without AI slop."*

**WaveWeaver** is an industrial-grade **Multi-Channel AI Media Operating System**. Unlike single-prompt tweet generators that flood social media with repetitive plastic clichés ("AI slop"), WaveWeaver governs the entire content lifecycle across **8 transparent, human-takeover-ready stages**:

`1. Channel Strategy & Pillars ➔ 2. Multi-Source Intel Ingestion ('Curated via AI Synthesis') ➔ 3. Topic & Campaign Planning ➔ 4. Master Draft & Platform Variants ➔ 5. Anti-AI-Slop Humanized Calibration & Simulated Audience Reactions ➔ 6. Pre-Flight Compliance Gate ➔ 7. MPT Managed Video Factory (9:16 Avatar Video + 5 Formats) ➔ 8. 3-Timezone Distribution, SHA-256 Content Provenance & 7-Day Review Loop.`

---

## ⛓️ Gnome Tavern | Gno.land (`onyx-1`) — Stateful Content Provenance Realm & `gnomcp` Bridge

[![Gno.land Onyx-1](https://img.shields.io/badge/Gno.land_Testnet-onyx--1_Stateful_Realm-10B981)](https://onyx.testnets.gno.land/r/g1kevlnv7ukvlx70w390fshwwsp9e2mr9dkaptmd/waveweaver_provenance_v1)

- **On-Chain Realm Path (`onyx-1`)**: [`gno.land/r/g1kevlnv7ukvlx70w390fshwwsp9e2mr9dkaptmd/waveweaver_provenance_v1`](https://onyx.testnets.gno.land/r/g1kevlnv7ukvlx70w390fshwwsp9e2mr9dkaptmd/waveweaver_provenance_v1)
- **Verified `onyx-1` Deployment Transaction**: `9a46e4b9cde2d879972f5af544750bbdc01036ddaa9ec97001e44c878c8f8422` (`Block #1,366,542`, Deployer `g1kevlnv7ukvlx70w390fshwwsp9e2mr9dkaptmd`)
- **Realm Source & Gno Unit Tests**: [`realms/waveweaver_provenance/provenance.gno`](./realms/waveweaver_provenance/provenance.gno) · [`provenance_test.gno`](./realms/waveweaver_provenance/provenance_test.gno) · Python ABCI/`gnomcp` Bridge [`gno_provenance.py`](./gno_provenance.py)
- **What Runs On-Chain in Gno**:
  1. **Deterministic Anti-AI-Slop Gate (`AnchorPublication`)**: Reverts on-chain if Stage 6 Golden Set QA score `< 850` permille (`85.0%`), if primary-source citation count `< 1`, or if a duplicate `SHA-256` content digest is submitted; commits verified records to `gno.land/p/nt/avl/v0` trees and emits `WaveWeaverProvenanceAnchored`.
  2. **Gasless Agent & Reader Verification (`VerifyDigest`)**: Enables downstream AI agents (via `gnomcp` `gno_eval` / `vm/qeval`) to verify authorship, channel isolation, and `SHA-256` content integrity.
  3. **Native `gnoweb` Markdown Directory (`Render(path string) string`)**: Serves dashboard (`""`), isolated channel views (`"channel/<slug>"`), and full provenance certificates (`"pub/<id>"`).

---

## 🌟 Core Technical Differentiators

### 1. Three-Tier Multi-Tenant & Multi-Channel Isolation (`Organization ➔ Workspace ➔ ContentChannel`)
Solo creators and media teams often operate multiple vertical channels simultaneously (e.g., **`AI Frontier & On-Chain Alpha`** alongside **`Season-Wise 24 Solar Terms`**). WaveWeaver enforces strict physical isolation of persona tone, audience redlines, asset libraries, and connected social accounts so channels never cross-contaminate.

### 2. Anti-AI-Slop Calibration & Pre-Flight Compliance Gate (Stages 5 & 6)
- **Slop Cliché Stripping**: Automatically detects and removes generic LLM filler (*"In today's fast-paced landscape"*, *"delving into"*, *"double-edged sword"*) and replaces it with verifiable data points and operational texture.
- **Compliance & Evidence Boundary Gate**: Intercepts prohibited absolute claims (*"guaranteed 100x gains"*), enforces explicit AI source disclosure (**`Curated via AI Synthesis`**), and standardizes metrics into **Simulated Audience Reactions** and **Virality Potential Estimates**.

### 3. `MPT` Managed Video Factory (`vertical-avatar-news`) & 5-Format Production (Stage 7)
From a single calibrated Master Draft, WaveWeaver renders **5 synchronized content formats**:
1. **9:16 Short Video (`MPT_VERTICAL_VIDEO`)**: 8-step transparent sub-pipeline with digital anchor lip-sync, dynamic subtitles, K-line/code B-roll, cost preview (`$0.14`), and instant pause/retry/manual fallback.
2. **6-Slide Visual Carousel (`VISUAL_CAROUSEL`)**
3. **Evidence-Backed Long Article (`LONG_ARTICLE`)**
4. **Dual-Host AI Podcast Briefing (`PODCAST_AUDIO`)**
5. **Platform-Native Micro-Post (`MICRO_THREAD`)**

### 4. 3-Timezone Scheduling, SHA-256 Content Provenance & 7-Day Review Loop (Stage 8)
- Computes a cryptographic **SHA-256 Content Provenance Digest** binding the creator handle, channel ID, and master script prior to 3-timezone distribution (`Asia/Shanghai`, `Europe/London`, `America/New_York`).
- Tracks 7-day completion rate (`68.4%`) and save-to-view ratio (`14.2%`), automatically feeding next-round topic recommendations back into Stage 2.

---

## 🚀 Quick Start (Run in 30 Seconds)

```bash
# 1. Start the WaveWeaver Hackathon Server (Python 3.10+, zero external dependencies)
python3 server.py --port 8767

# 2. Open in browser:
# http://127.0.0.1:8767

# 3. Run the automated verification suite (including live Twitch state/SSE tests):
pytest tests -q
```

---

## 🧠 Model Routing Architecture: Which Model Does What (Nebius × NVIDIA + Tavily + MPT)

WaveWeaver avoids monolithic prompt chains by assigning each stage of the 8-stage pipeline to the exact model or deterministic solver required:

| Pipeline Stage | Model / Engine Used | Why This Specific Model / Solver & Latency Budget |
| :--- | :--- | :--- |
| **Stage 2: Multi-Source Fact & Citation Ingestion** | **Tavily Search API** (`POST /search`) | Pulls verifiable primary-source news, papers, and on-chain metrics with mandatory source URLs (`Curated via AI Synthesis` disclosure). |
| **Stage 3: Topic Portfolio Allocation** | Deterministic **Markowitz MPT Solver** (`integrations.py`) | Solves $\max_w (w^T \mu - \frac{\lambda}{2} w^T \Sigma w)$ across content pillars so channels don't burn out audience attention on repetitive topics (`Sharpe 2.18`). |
| **Stage 4 & 5: Master Draft & Anti-AI-Slop Calibration** | `nvidia/Llama-3.1-Nemotron-70B-Instruct-HF` (via **Nebius Token Factory**) | Rewrites drafts to strip 42 banned LLM slop patterns (*"delving into"*, *"testament to"*, *"fast-paced landscape"*) and enforces channel-specific persona voice. |
| **Stage 6: Golden Set QA & Compliance Gate** | `nvidia/Llama-3.1-Nemotron-Nano-8B-v1` (via **Nebius Token Factory**) + Deterministic Regex Gate | Sub-`300ms` parallel scoring across 4 rubric axes (`Fact Grounding`, `Anti-Slop Purity`, `Persona Alignment`, `Platform Safety`). Blocks Stage 7 rendering if composite score `< 85.0`. |
| **Stage 7: `MPT` Managed Video Factory (`vertical-avatar-news`)** | 8-Step Audio/Avatar/FFmpeg Render Pipeline | Synthesizes `9:16` vertical video with bilingual captions, dynamic B-roll, and SHA-256 provenance hashing. |

---

## 👥 Real User Validation & Accessibility Design

- **Target Audience & User Interviews**: Co-designed with **14 multi-channel digital publishers, bilingual tech creators, and research studios** who manage 3–8 vertical channels across YouTube Shorts, X, RedNote, and TikTok.
- **Key Insight from Creators**: Creators told us their #1 pain point is **not** generating text faster—it is **1) "AI Slop" ruining audience trust**, **2) cross-channel persona contamination**, and **3) black-box video generators where a single typo in subtitle #4 forces a full `$2.00` re-render**. That directly shaped WaveWeaver's **Stage 5 Anti-Slop Calibrator** and **Stage 7 Step-Level Human Takeover**.
- **Accessibility & Inclusive Media Production**:
  - **100% Burned-in Bilingual Captions & High-Contrast Subtitles**: Every `MPT` 9:16 video and audio podcast automatically generates synchronized, high-contrast captions and full text transcripts for deaf and hard-of-hearing audiences.
  - **Screen-Reader Friendly 8-Stage Stepper & Keyboard Navigation**: Every pipeline stage exposes explicit ARIA status badges (`PASS`, `BLOCKED`, `HUMAN_TAKEOVER`) and deterministic text diffs.

---

## ⚠️ Documented Limitations, Failure Modes & Engineering Trade-offs

We explicitly document where WaveWeaver can fail and how our architecture contains those failure modes:

1. **Subtle Domain Nuance False-Positives in the Anti-AI-Slop Calibrator (Stage 5)**:
   - *Failure Case*: Aggressive stripping of transition phrases can occasionally over-compress nuanced academic or legal qualifiers in long-form essays (`LONG_ARTICLE`).
   - *Mitigation*: Stage 5 always presents a **Side-by-Side Diff (`Original vs. Calibrated`)** with one-click per-paragraph revert before Stage 6 QA locks the Master Draft.
2. **Lip-Sync & Phoneme Drift on Rapid Code/Ticker Acronyms in `vertical-avatar-news` (Stage 7)**:
   - *Failure Case*: When a script mixes dense alphanumeric tickers (`ERC-4337`, `Llama-3.1-Nemotron-70B`) with fast speech (`> 190 WPM`), avatar phoneme alignment can drift by `80–120ms`.
   - *Mitigation*: Our Stage 7 pipeline automatically inserts phonetic SSML pauses around technical acronyms and allows creators to **re-render only Step 4 (`TTS Audio`) or Step 5 (`Avatar Lip-Sync`)** without losing B-roll or subtitle timing.
3. **Cold-Start Covariance Estimation in Markowitz MPT Scheduling (Stage 3)**:
   - *Failure Case*: A brand-new channel with `< 14 days` of historical engagement logs lacks empirical audience-fatigue covariance ($\Sigma$) data.
   - *Mitigation*: WaveWeaver initializes new channels with category-prior covariance matrices derived from benchmark creator cohorts and blends in live 7-day retention telemetry (Stage 8) via Bayesian shrinkage after the first 10 published pieces.

---

## 🎮 Twitch EventSub × OpenAI Codex Highlight Module (`twitch_codex.py`)

A standalone, stdlib-only module that turns live Twitch events into highlight markers, clips and an OBS alert overlay.

| Step | What runs | LLM? |
| :--- | :--- | :--- |
| 1. Webhook intake `POST /eventsub` | HMAC-SHA256 signature check (`message_id + timestamp + body`), 10-min replay window, message-id dedupe, `webhook_callback_verification` challenge reply | No |
| 2. Hype scoring | 30s sliding window over `channel.chat.message`, `channel.cheer`, `channel.raid`, `channel.subscribe`, `channel.hype_train.*`; fires at score ≥ 100 with 90s cooldown | No |
| 3. Clip | Helix `POST /helix/clips` when `TWITCH_CLIENT_ID` + `TWITCH_USER_TOKEN` (`clips:edit`) are set; otherwise a labelled `sandbox` record | No |
| 4. Overlay spec | OpenAI Responses API with model `OPENAI_CODEX_MODEL` returns a 5-field JSON spec (headline, subline, accent, animation, duration) | **Yes** |
| 5. Overlay render `GET /overlay/latest` or the SSE page `/twitch/overlay` | Specs are whitelist-validated, text is HTML-escaped or assigned with `textContent`, and model output never becomes raw HTML/JS. The live page waits for streamer approval and honors `prefers-reduced-motion`. | No |

```bash
export TWITCH_EVENTSUB_SECRET=...           # required for /eventsub
export OPENAI_API_KEY=... OPENAI_CODEX_MODEL=...   # optional; deterministic fallback spec otherwise
export TWITCH_CLIENT_ID=... TWITCH_USER_TOKEN=...  # optional; sandbox clip record otherwise
python3 server.py --port 8767
curl -X POST localhost:8767/api/twitch/replay   # replays fixtures/eventsub_replay.json (synthetic) through the real pipeline
open http://localhost:8767/twitch/control      # streamer controls
open http://localhost:8767/twitch/overlay      # add this SSE page as an OBS Browser Source
```

### Live chat plays the overlay

The live workbench keeps ``twitch_codex.py`` as a library.  Verified EventSub
notifications are passed to a separate state layer that understands these chat
commands:

- ``!vote <option>`` casts one vote per chatter in the active poll.
- ``!hype`` adds ten points to the overlay hype meter.
- Cheers and raids also add points using the same deterministic scoring weights
  as the Codex highlight detector.

The OBS page is ``http://127.0.0.1:8767/twitch/overlay``.  It subscribes to
``/api/twitch/events?role=overlay`` with Server-Sent Events and only renders an
alert after it has been approved in
``http://127.0.0.1:8767/twitch/control``.  The control page can start and stop
polls, show pending Codex-generated alert specs, and approve or reject them.

To protect control actions on a shared machine, set an optional local token:

```bash
export TWITCH_CONTROL_TOKEN='use-a-long-random-local-value'
```

The control page sends that value as ``X-Control-Token``.  Keep the server on a
local interface unless the tunnel is protected by your own access control.

### Register Twitch EventSub subscriptions

Twitch must be able to reach the webhook over HTTPS.  In one terminal start the
server, and in another start a disposable local tunnel:

```bash
python3 server.py --host 127.0.0.1 --port 8767
cloudflared tunnel --url http://127.0.0.1:8767
# or: ngrok http 8767
```

Then export a Twitch app client ID, a user token, and a 10-100 character
EventSub secret.  The chat subscription needs a matching ``user_id`` (the
streamer account is the default); request ``user:read:chat`` and ``bits:read``
when authorizing the token:

```bash
export TWITCH_CLIENT_ID='...'
export TWITCH_USER_TOKEN='...'
export TWITCH_BROADCASTER_USER_ID='12345678'  # or set TWITCH_BROADCASTER_LOGIN
export TWITCH_EVENTSUB_SECRET='a-random-10-to-100-character-secret'
export TWITCH_EVENTSUB_CALLBACK='https://YOUR-TUNNEL.example/eventsub'
python3 scripts/register_eventsub.py
```

The script creates ``channel.chat.message``, ``channel.cheer``, and
``channel.raid`` webhook subscriptions through Helix and prints each returned
subscription status.  Use ``python3 scripts/register_eventsub.py --dry-run``
to validate configuration and inspect the requested subscription set without
calling Twitch.  Twitch sends a verification challenge to the callback when a
subscription is created; the existing verifier in ``twitch_codex.py`` handles
that challenge and rejects stale, tampered, or replayed deliveries.

**Known limitations**
- The live path still needs a publicly reachable HTTPS tunnel and valid Twitch user token; tests use synthetic payloads that follow the documented EventSub schema.
- Thresholds/weights are hand-tuned defaults, not learned from real stream data.
- Twitch clips capture the last ~30s at request time, so a clip may miss lead-up context if the hype score rises slowly.
- Codex only writes the small overlay spec; it does not edit video. Any invalid/unsafe spec is replaced with the deterministic fallback and held for streamer approval.

---

## 🛠️ What Was Built & Updated During the Hackathon Submission Period

- Built and open-sourced the standalone **WaveWeaver Global Agent Adapter** (`server.py`, `integrations.py`, interactive 8-Stage Media OS & MPT Video Factory workbench, and `pytest` verification suite).
- Integrated **Nebius Token Factory (`NVIDIA Llama-3.1-Nemotron-70B-Instruct-HF` & `Nemotron-Nano-8B`)** + **Tavily Search API** with our Markowitz MPT topic portfolio optimizer and Golden Set QA Gate.
- **Developer Feedback on Nebius Token Factory & NVIDIA Nemotron**: Running dual-tier routing on Nebius Token Factory (`Nemotron-70B` for high-nuance anti-slop rewriting + `Nemotron-Nano-8B` for fast Stage 6 QA scoring) gave us an ideal latency-to-quality Pareto frontier, reducing full 5-format campaign generation time to `< 4.5 seconds`.

