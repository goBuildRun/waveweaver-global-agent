#!/usr/bin/env python3
"""
Automated 1080p Demo Video Recorder & English Voiceover Synthesizer for WaveWeaver (织浪 AI).
Produces:
1. `/Users/aronezhang-mini/buildrun-agent-engineering-platform/products/hackathon/submissions/waveweaver-demo-1080p.mp4`
2. 4 high-res 1080p gallery screenshots under `submissions/screenshots-waveweaver/`
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg"
FFPROBE_BIN = "/opt/homebrew/bin/ffprobe"
SAY_BIN = "/usr/bin/say"
PORT = 8767
BASE_URL = f"http://127.0.0.1:{PORT}"

ADAPTER_DIR = Path(__file__).resolve().parent
SUBMISSIONS_DIR = ADAPTER_DIR.parent.parent / "submissions"
SCREENSHOTS_DIR = SUBMISSIONS_DIR / "screenshots-waveweaver"
OUTPUT_MP4 = SUBMISSIONS_DIR / "waveweaver-demo-1080p.mp4"

SCENES = [
    {
        "id": "scene1_multichannel_and_intel",
        "caption": "Scene 1 · WaveWeaver (织浪 AI): 3-Tier Channel Isolation (Org ➔ Workspace ➔ Channel) & Live Intel Ingestion",
        "narration": (
            "Meet WaveWeaver, an eight-stage human-in-the-loop A.I. media operating system. "
            "Unlike single-prompt generators that produce repetitive A.I. slop, WaveWeaver enforces strict three-tier isolation "
            "across Organizations, Workspaces, and Content Channels—such as our A.I. Frontier Quant channel and our Twenty-Four Solar Terms culinary channel. "
            "Clicking Ingest Live Intelligence invokes Nebius NVIDIA Nemotron Seventy-B and Tavily Search to structure raw on-chain data into high-potential campaign cards."
        ),
    },
    {
        "id": "scene2_anti_ai_slop_calibration",
        "caption": "Scene 2 · Stage 5 & 6: Humanized Anti-AI-Slop Calibration, Simulated Audience Reaction & Compliance Gate",
        "narration": (
            "In the Anti-A.I.-Slop and Compliance tab, WaveWeaver strips plastic L.L.M. clichés like 'in today's fast-paced landscape' "
            "and intercepts prohibited financial guarantees, replacing them with verifiable five-hundred-seventy-six-token empirical metrics. "
            "Before production, it runs Simulated Audience Reactions across quant developer and retail personas, achieving ninety-three percent estimated retention."
        ),
    },
    {
        "id": "scene3_mpt_video_factory_5formats",
        "caption": "Scene 3 · Stage 7: MPT Managed Video Factory (vertical-avatar-news 9:16) & Simultaneous 5-Format Production",
        "narration": (
            "Switching to Stage Seven, our M.P.T. Managed Video Factory executes a transparent eight-step pipeline with pause, retry, and manual takeover controls. "
            "From one calibrated master draft, WaveWeaver simultaneously renders a sixty-two-second vertical avatar video, a six-slide visual carousel, "
            "a long-form research article, a dual-host podcast briefing, and platform-native micro-posts."
        ),
    },
    {
        "id": "scene4_provenance_and_7day_loop",
        "caption": "Scene 4 · Stage 8: 3-Timezone Distribution, SHA-256 Content Provenance & 7-Day Health Review Loop",
        "narration": (
            "Finally, in Stage Eight, WaveWeaver locks a three-timezone distribution schedule across Asia, Europe, and North America, "
            "mints a cryptographic SHA-two-fifty-six content provenance attestation on-chain, and closes the loop with a seven-day analytics engine "
            "that feeds next-round topic recommendations back into Stage Two. Thank you for watching WaveWeaver."
        ),
    },
]


def get_audio_duration(path: Path) -> float:
    cmd = [
        FFPROBE_BIN,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    return float(subprocess.check_output(cmd, text=True).strip())


def build_voiceover_tracks(work_dir: Path) -> tuple[Path, list[float]]:
    wav_files = []
    durations = []
    for idx, scene in enumerate(SCENES):
        aiff_path = work_dir / f"{idx:02d}_{scene['id']}.aiff"
        wav_path = work_dir / f"{idx:02d}_{scene['id']}.wav"
        subprocess.run(
            [SAY_BIN, "-v", "Samantha", "-r", "182", "-o", str(aiff_path), scene["narration"]],
            check=True,
        )
        subprocess.run(
            [
                FFMPEG_BIN,
                "-y",
                "-i",
                str(aiff_path),
                "-af",
                "apad=pad_dur=0.6",
                "-ar",
                "44100",
                "-ac",
                "2",
                str(wav_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        dur = get_audio_duration(wav_path)
        wav_files.append(wav_path)
        durations.append(dur)
        print(f"  [TTS] {scene['id']}: {dur:.2f}s")

    concat_list = work_dir / "concat_audio.txt"
    concat_list.write_text("\n".join(f"file '{w.as_posix()}'" for w in wav_files), encoding="utf-8")
    full_audio = work_dir / "full_voiceover.wav"
    subprocess.run(
        [
            FFMPEG_BIN,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(full_audio),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return full_audio, durations


def set_caption(page, text: str) -> None:
    page.evaluate(
        """(captionText) => {
            let banner = document.getElementById('judge-caption-banner');
            if (!banner) {
                banner = document.createElement('div');
                banner.id = 'judge-caption-banner';
                banner.style.cssText = [
                    'position: fixed',
                    'bottom: 16px',
                    'left: 50%',
                    'transform: translateX(-50%)',
                    'z-index: 9999',
                    'background: rgba(10, 14, 23, 0.95)',
                    'border: 1.5px solid #06B6D4',
                    'box-shadow: 0 8px 30px rgba(0,0,0,0.75)',
                    'color: #F4F7FB',
                    'padding: 10px 22px',
                    'border-radius: 999px',
                    'font-size: 14.5px',
                    'font-weight: 700',
                    'letter-spacing: 0.2px',
                    'white-space: nowrap'
                ].join(';');
                document.body.appendChild(banner);
            }
            banner.textContent = captionText;
        }""",
        text,
    )


def highlight_and_click(page, selector: str, wait_after: float = 1.2) -> None:
    loc = page.locator(selector).first
    loc.scroll_into_view_if_needed()
    loc.evaluate(
        """(el) => {
            const prevOutline = el.style.outline;
            const prevShadow = el.style.boxShadow;
            el.style.outline = '2.5px solid #06B6D4';
            el.style.boxShadow = '0 0 24px rgba(6, 182, 212, 0.85)';
            setTimeout(() => {
                el.style.outline = prevOutline;
                el.style.boxShadow = prevShadow;
            }, 1400);
        }"""
    )
    time.sleep(0.45)
    loc.click()
    time.sleep(wait_after)


def ensure_server_running() -> subprocess.Popen | None:
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/state", timeout=1.5) as resp:
            if resp.status == 200:
                return None
    except Exception:
        pass

    proc = subprocess.Popen(
        [sys.executable, str(ADAPTER_DIR / "server.py"), "--port", str(PORT)],
        cwd=str(ADAPTER_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/state", timeout=1.0) as resp:
                if resp.status == 200:
                    return proc
        except Exception:
            time.sleep(0.25)
    return proc


def record_browser_walkthrough(work_dir: Path, durations: list[float]) -> Path:
    video_dir = work_dir / "pw_video"
    video_dir.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            record_video_dir=str(video_dir),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        time.sleep(0.6)

        # --- SCENE 1: 3-Tier Channel Isolation & Live Intel Ingestion ---
        t0 = time.monotonic()
        set_caption(page, SCENES[0]["caption"])
        time.sleep(2.0)
        highlight_and_click(page, "button:has-text('Channel 2: Season-Wise 24 Solar Terms')", wait_after=1.8)
        highlight_and_click(page, "button:has-text('Channel 1: AI Frontier & On-Chain Alpha')", wait_after=1.8)
        highlight_and_click(page, "button:has-text('Ingest Live On-Chain & Macro Intel')", wait_after=2.5)
        page.screenshot(path=str(SCREENSHOTS_DIR / "01_multichannel_intel_ingestion.png"))
        elapsed = time.monotonic() - t0
        time.sleep(max(0.2, durations[0] - elapsed))

        # --- SCENE 2: Anti-AI-Slop Calibration & Pre-Flight Compliance ---
        t0 = time.monotonic()
        set_caption(page, SCENES[1]["caption"])
        highlight_and_click(page, "button.tab-btn:has-text('2. 去AI味校准与预检')", wait_after=1.8)
        highlight_and_click(page, "button:has-text('Run Anti-AI-Slop Calibration')", wait_after=2.5)
        page.screenshot(path=str(SCREENSHOTS_DIR / "02_anti_ai_slop_calibration.png"))
        elapsed = time.monotonic() - t0
        time.sleep(max(0.2, durations[1] - elapsed))

        # --- SCENE 3: MPT Managed Video Factory & 5 Formats ---
        t0 = time.monotonic()
        set_caption(page, SCENES[2]["caption"])
        highlight_and_click(page, "button.tab-btn:has-text('3. MPT 视频工厂与五形态')", wait_after=1.8)
        highlight_and_click(page, "button:has-text('Render MPT 9:16 Avatar Video & All 5 Formats')", wait_after=2.8)
        page.screenshot(path=str(SCREENSHOTS_DIR / "03_mpt_video_factory_5formats.png"))
        elapsed = time.monotonic() - t0
        time.sleep(max(0.2, durations[2] - elapsed))

        # --- SCENE 4: 3-Timezone Distribution, SHA-256 Provenance & 7-Day Review ---
        t0 = time.monotonic()
        set_caption(page, SCENES[3]["caption"])
        highlight_and_click(page, "button.tab-btn:has-text('4. 三时区排期与7日复盘')", wait_after=1.8)
        highlight_and_click(page, "button:has-text('Lock 3-Timezone Schedule & Mint SHA-256 Provenance')", wait_after=2.5)
        page.screenshot(path=str(SCREENSHOTS_DIR / "04_provenance_and_7day_loop.png"))
        elapsed = time.monotonic() - t0
        time.sleep(max(0.2, durations[3] - elapsed))

        context.close()
        browser.close()

    webm_files = list(video_dir.glob("*.webm"))
    if not webm_files:
        raise RuntimeError("No Playwright video recorded!")
    return webm_files[0]


def mux_video_and_audio(webm_path: Path, wav_path: Path, output_mp4: Path) -> None:
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            FFMPEG_BIN,
            "-y",
            "-i",
            str(webm_path),
            "-i",
            str(wav_path),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(output_mp4),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    print("🎬 [1/4] Starting WaveWeaver server & synthesizing English TTS narration...")
    server_proc = ensure_server_running()
    try:
        with tempfile.TemporaryDirectory(prefix="waveweaver_demo_") as tmp:
            work_dir = Path(tmp)
            full_audio, durations = build_voiceover_tracks(work_dir)
            total_dur = sum(durations)
            print(f"🔊 [2/4] Total English narration duration: {total_dur:.2f}s ({total_dur/60:.2f} min)")
            print("🎥 [3/4] Recording 1920x1080 interactive Playwright walkthrough & 4 gallery screenshots...")
            webm_file = record_browser_walkthrough(work_dir, durations)
            print("⚙️  [4/4] Muxing 1080p H.264 MP4 + AAC English voiceover...")
            mux_video_and_audio(webm_file, full_audio, OUTPUT_MP4)
            final_dur = get_audio_duration(OUTPUT_MP4)
            size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
            print(f"✅ Done! Video saved to: {OUTPUT_MP4} ({final_dur:.1f}s, {size_mb:.2f} MB)")
            print(f"🖼️  Screenshots saved to: {SCREENSHOTS_DIR}")
    finally:
        if server_proc is not None:
            server_proc.terminate()


if __name__ == "__main__":
    main()
