"""Record the tour videos (media/tour-ko.mp4, media/tour-en.mp4) by driving the demo in Chromium.

The browser plays the page's own features (request flow, scoring replay, attack evidence,
training and benchmark charts) while a caption bar and a pointer are drawn on top. Only the
recording harness adds those overlays; the site itself is unchanged.

Needs Playwright and ffmpeg on the operator workstation (not in the project's dependencies):
  pip install playwright && playwright install chromium
  python3 demo/record_tour.py --site /tmp/demo-stage --out demo/site/media

--site should hold the files that will be published, including data/recording.json and
data/extras.json. The page is served on 127.0.0.1 only, for the length of the recording.
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import hashlib
import http.server
import json
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

CAPTIONS = {
    "ko": {
        "hero": "실제 EKS 실행 기록을 다시 보여 주는 데모입니다. 클러스터에 직접 연결하지 않습니다.",
        "flow": "채점 요청 하나가 지나가는 길: trainer, 점수 계산, 라우팅 표, 샌드박스",
        "node": "상자를 누르면 설명과 측정값이 나옵니다.",
        "cheat": "속도 측정 속이기: 처음엔 정답을 내다가 속도를 잴 때는 0을 돌려주는 코드",
        "cheat2": "두 샌드박스 모두 측정하는 동안에도 결과를 확인해서 잡아냅니다.",
        "hostfile": "서버 파일 읽기: 실행하기 전 사전 검사에서 바로 막힙니다.",
        "fused": "정답 Triton 커널: A10G와 T4 모두 정답 코드보다 약 1.78배 빨랐습니다.",
        "attacks": "샌드박스 안에서 해 본 접근: 메타데이터, Kubernetes API, kubelet, 인터넷 모두 막혔습니다.",
        "term": "카드를 누르면 실제 터미널 기록에서 해당 줄을 찾아 보여 줍니다.",
        "kata": "같은 검증을 Kata GPU 샌드박스에서도 실행했습니다.",
        "grpo": "실제 모델(Qwen2.5-Coder-1.5B)로 GRPO 학습 5 step: 채점 결과와 점수",
        "switch": "학습 중 샌드박스 버전 바꾸기: 빠지는 배치 없이 v1에서 v2로 넘어갑니다.",
        "bench": "성능 비교: 런타임별 채점 시간, 시작 시간, 처리량",
        "patterns": "패턴별 아키텍처: trainer와 샌드박스를 어디에 두는지 네 가지 패턴으로 보여 줍니다.",
        "patterns2": "HyperPod 학습(B1)에서 학습 한 step을 재생합니다. 요청과 결과가 선을 따라 움직입니다.",
        "end": "GPU Sandbox on AWS: 가이드와 코드는 GitHub에 있습니다.",
    },
    "en": {
        "hero": "A replay of real EKS run records. The browser never connects to a cluster.",
        "flow": "One reward request: trainer, reward function, routing table, sandbox pool",
        "node": "Click a component for its description and measurements.",
        "cheat": "Benchmark cheat: correct at first, zeros once the benchmark starts",
        "cheat2": "Both sandboxes catch it by re-checking the timed outputs (timed_output_mismatch).",
        "hostfile": "Reading a host file: stopped by the static policy check before it runs.",
        "fused": "A correct Triton kernel: about 1.78x faster than the reference on A10G and T4.",
        "attacks": "Tried from inside the sandbox: IMDS, Kubernetes API, kubelet, internet, all blocked",
        "term": "Each card finds and highlights its line in the real terminal output.",
        "kata": "The same checks ran on the Kata QEMU GPU pool.",
        "grpo": "Five GRPO steps of a real model (Qwen2.5-Coder-1.5B): verdicts and reward",
        "switch": "Switching the sandbox version mid-training: no batch is lost from v1 to v2.",
        "bench": "Benchmark: eval latency, cold start and throughput per runtime",
        "patterns": "Architecture patterns: four ways to place the trainer and the sandboxes.",
        "patterns2": "Replaying one training step of HyperPod training (B1): requests and results move along the lines.",
        "end": "GPU Sandbox on AWS: the guide and the code are on GitHub.",
    },
}

OVERLAY = """
() => {
  document.querySelector('.video-box')?.remove();
  const heroGrid = document.querySelector('.hero-grid');
  if (heroGrid) heroGrid.style.gridTemplateColumns = '1fr';
  const cap = document.createElement('div');
  cap.id = 'tour-cap';
  Object.assign(cap.style, {position: 'fixed', left: '50%', bottom: '18px', transform: 'translateX(-50%)',
    maxWidth: '1000px', padding: '12px 22px', borderRadius: '10px', background: 'rgba(15,20,25,.88)',
    color: '#fff', font: '600 19px/1.4 system-ui, NanumSquare, sans-serif', zIndex: 9999, textAlign: 'center',
    wordBreak: 'keep-all', transition: 'opacity .25s', opacity: 0});
  document.body.append(cap);
  const ptr = document.createElement('div');
  ptr.id = 'tour-ptr';
  Object.assign(ptr.style, {position: 'fixed', left: '640px', top: '360px', width: '22px', height: '22px',
    marginLeft: '-11px', marginTop: '-11px', borderRadius: '50%', background: 'rgba(255,153,0,.85)',
    border: '3px solid #fff', boxShadow: '0 0 0 2px rgba(0,0,0,.35)', zIndex: 10000,
    transition: 'left .6s ease, top .6s ease, transform .15s', pointerEvents: 'none'});
  document.body.append(ptr);
}
"""


class Tour:
    def __init__(self, page, lang: str) -> None:
        self.page = page
        self.text = CAPTIONS[lang]

    async def caption(self, key: str | None) -> None:
        await self.page.evaluate(
            "(t) => { const c = document.getElementById('tour-cap'); c.textContent = t || ''; c.style.opacity = t ? 1 : 0; }",
            self.text[key] if key else "",
        )

    async def scroll(self, selector: str, block: str = "start") -> None:
        await self.page.evaluate(
            "([s, b]) => document.querySelector(s).scrollIntoView({behavior: 'smooth', block: b})", [selector, block])
        await self.page.wait_for_timeout(1100)

    async def click(self, selector: str, wait_ms: int = 500) -> None:
        box = await self.page.locator(selector).first.bounding_box()
        if box:
            x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            await self.page.evaluate(
                "([x, y]) => { const p = document.getElementById('tour-ptr'); p.style.left = x + 'px'; p.style.top = y + 'px'; }",
                [x, y])
            await self.page.wait_for_timeout(700)
            await self.page.evaluate("() => { document.getElementById('tour-ptr').style.transform = 'scale(.7)'; }")
            await self.page.wait_for_timeout(150)
            await self.page.evaluate("() => { document.getElementById('tour-ptr').style.transform = ''; }")
        await self.page.locator(selector).first.click()
        await self.page.wait_for_timeout(wait_ms)

    async def run(self) -> None:
        p = self.page
        await p.evaluate(OVERLAY)
        await self.caption("hero")
        await p.wait_for_timeout(4500)

        await self.scroll("#arch")
        await self.caption("flow")
        await self.click("#flow-play", 0)
        await p.wait_for_timeout(18500)
        await self.caption("node")
        await self.click('.arch-node[data-id="kata"]', 2800)

        await self.scroll("#try")
        await self.click('.sub[data-name="relu_bias_benchmark_cheat"]', 0)
        await self.caption("cheat")
        await p.wait_for_timeout(1500)
        await p.select_option("#speed", "4")
        await self.click("#run", 300)
        await self.scroll("#lanes", "center")
        await p.wait_for_timeout(2600)
        await self.caption("cheat2")
        await p.wait_for_timeout(3500)
        await self.scroll("#try")
        await self.click('.sub[data-name="read_host_file"]', 0)
        await self.caption("hostfile")
        await p.wait_for_timeout(300)
        await self.click("#run", 300)
        await self.scroll("#lanes", "center")
        await p.wait_for_timeout(3000)
        await self.scroll("#try")
        await self.click('.sub[data-name="relu_bias_triton"]', 0)
        await self.caption("fused")
        await p.wait_for_timeout(300)
        await self.click("#run", 300)
        await self.scroll("#lanes", "center")
        await p.wait_for_timeout(5000)

        await self.scroll("#defense")
        await self.caption("attacks")
        await p.wait_for_timeout(2500)
        await self.scroll(".attacks", "start")
        await self.caption("term")
        for attack in ("imds", "internet", "ns", "cheat"):
            await self.click(f'.attack[data-id="{attack}"]', 1300)
            await self.scroll(".attacks", "start")
        await self.caption("kata")
        await self.click('#term-tabs .tab[data-id="verify-kata-qemu"]', 0)
        await self.scroll(".term-box", "center")
        await p.wait_for_timeout(8000)

        await self.scroll("#train")
        await self.caption("grpo")
        await self.click("#grpo-play", 0)
        await p.wait_for_timeout(1500)
        await self.scroll("#grpo-detail", "center")
        await p.wait_for_timeout(5500)
        await self.scroll("#sim-chart", "center")
        await self.caption("switch")
        await p.wait_for_timeout(4500)

        await self.scroll("#bench")
        await self.caption("bench")
        await p.wait_for_timeout(2000)
        for metric in (1, 2, 3):
            await self.click(f"#bench-metric .tab:nth-child({metric + 1})", 1800)
        await self.click("#bench-metric .tab:nth-child(1)", 1500)

        await self.scroll("#arch")
        await self.click("#patterns-link", 0)
        await p.wait_for_selector(".ap-node")
        await p.evaluate(OVERLAY)
        await self.caption("patterns")
        await p.wait_for_timeout(3000)
        await self.click('.ap-pattern[data-id="b1"]', 1200)
        await self.click("#ap-flows .tab:nth-child(2)", 300)
        await self.scroll(".ap-toolbar", "start")
        await self.caption("patterns2")
        await self.click("#ap-play", 0)
        await p.wait_for_timeout(17500)
        await p.evaluate("() => window.scrollTo({top: 0, behavior: 'smooth'})")
        await self.caption("end")
        await p.wait_for_timeout(3500)


def serve(site: Path) -> tuple[http.server.ThreadingHTTPServer, int]:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(site)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


async def capture(site: Path, workdir: Path, langs: list[str]) -> dict[str, Path]:
    """Drive the page once per language and return the raw WebM recording of each run."""
    from playwright.async_api import async_playwright

    server, port = serve(site)
    videos = {}
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            for lang in langs:
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720}, locale="ko-KR" if lang == "ko" else "en-US",
                    record_video_dir=str(workdir / lang), record_video_size={"width": 1280, "height": 720})
                page = await context.new_page()
                await page.goto(f"http://127.0.0.1:{port}/?lang={lang}")
                await page.wait_for_selector(".sub")
                await page.wait_for_timeout(600)
                await Tour(page, lang).run()
                videos[lang] = Path(await page.video.path())
                await context.close()
            await browser.close()
    finally:
        server.shutdown()
    return videos


def encode(video: Path, out: Path, lang: str) -> Path:
    """WebM from the browser to an H.264 MP4 that starts playing before it is fully loaded."""
    mp4 = out / f"tour-{lang}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-c:v", "libx264",
                    "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-an", str(mp4)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "3", "-i", str(mp4),
                    "-frames:v", "1", "-q:v", "3", str(out / f"tour-{lang}.jpg")], check=True)
    return mp4


def main() -> int:
    parser = argparse.ArgumentParser(prog="demo/record_tour.py", description=__doc__.splitlines()[0])
    parser.add_argument("--site", type=Path, default=Path(__file__).resolve().parent / "site")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "site" / "media")
    parser.add_argument("--lang", action="append", choices=sorted(CAPTIONS), help="default: ko and en")
    args = parser.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required")
    # The videos show these files, so they get the same scan as anything else that is published.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_extras import problems

    data = {name: args.site / "data" / name for name in ("recording.json", "extras.json")}
    found = [f"{name}: {msg}" for name, path in data.items() if path.exists()
             for msg in problems(json.loads(path.read_text()))]
    if found:
        raise SystemExit("refusing to record:\n" + "\n".join(found))
    args.out.mkdir(parents=True, exist_ok=True)
    # demo/deploy.sh compares these hashes with the files it publishes.
    (args.out / "tour-data.json").write_text(json.dumps(
        {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in data.items() if path.exists()},
        indent=1) + "\n")
    with tempfile.TemporaryDirectory() as tmp:
        videos = asyncio.run(capture(args.site, Path(tmp), args.lang or ["ko", "en"]))
        for lang, video in videos.items():
            mp4 = encode(video, args.out, lang)
            print(f"[tour] {mp4} ({mp4.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
