"""Check the diagrams of demo/site/architecture.html for arrows and labels that collide.

For every pattern, in Korean and in English, and in every step of every flow (bold active labels,
the flashing blocked text and the status badges as drawn): each arrow starts and ends on the edge
of the box drawn around an icon (never inside it, under a node name or on a group border), runs only horizontally and vertically, and
neither it nor its arrowhead crosses a text, an icon or another line; no label, name or badge
overlaps another text, an icon or a box border; every id a flow refers to exists; everything stays
inside the picture.

Needs Playwright on the operator workstation (not in the project's dependencies), like record_tour.py:
  pip install playwright && playwright install chromium
  python3 demo/check_arch_layout.py                 # exit 1 and list the problems if any
  python3 demo/check_arch_layout.py --shots /tmp/d  # also save one PNG per pattern and language

The page is served on 127.0.0.1 only, for the length of the check.
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import http.server
import sys
import threading
from pathlib import Path

PATTERNS = ("a", "b1", "b2", "c")
LANGS = ("ko", "en")

CHECK = r"""
() => {
  const errs = new Map();                 // problem -> first state it was seen in
  const P = 3;                            // clearance between a line and text or icons
  const HALF = 1.8;                       // half the width of an active line
  const svg = document.getElementById('ap-svg');
  const p = ui.pattern;
  const vb = svg.viewBox.baseVal;
  const box = (x1, y1, x2, y2, name) => ({ x1: Math.min(x1, x2), y1: Math.min(y1, y2), x2: Math.max(x1, x2), y2: Math.max(y1, y2), name });
  const grow = (b, d) => ({ ...b, x1: b.x1 - d, y1: b.y1 - d, x2: b.x2 + d, y2: b.y2 + d });
  const hit = (a, b) => a.x1 < b.x2 && b.x1 < a.x2 && a.y1 < b.y2 && b.y1 < a.y2;
  // A node is the box drawn around its icon when it lights up (B in arch.js), or the routing document.
  const nodeBox = (n) => n.icon === 'doc' ? box(n.x - 60, n.y - 40, n.x + 60, n.y + 40, 'doc:' + n.id) : box(n.x - B, n.y - B, n.x + B, n.y + B, 'box:' + n.id);
  const nodes = Object.fromEntries(p.nodes.map((n) => [n.id, n]));
  const edges = Object.fromEntries(p.edges.map((e) => [e.id, e]));
  let state = 'drawing';
  const err = (msg) => { if (!errs.has(msg)) errs.set(msg, state); };

  // ---- data: every id a flow or an edge refers to exists ----
  for (const e of p.edges) {
    if (!nodes[e.from] || !nodes[e.to]) err(`${e.id}: unknown from/to ${e.from}->${e.to}`);
    for (const id of e.needs || []) if (!nodes[id]) err(`${e.id}: needs unknown node ${id}`);
    if (e.fork && !edges[e.fork]) err(`${e.id}: forks from unknown edge ${e.fork}`);
  }
  for (const fl of p.flows) {
    for (const id of fl.init?.hide || []) if (!nodes[id]) err(`${fl.id}: hides unknown node ${id}`);
    fl.steps.forEach((st, k) => {
      for (const m of st.moves || []) if (!edges[m.e]) err(`${fl.id}#${k}: moves along unknown edge ${m.e}`);
      for (const key of ['light', 'dim', 'show', 'hide']) for (const id of st[key] || []) if (!nodes[id]) err(`${fl.id}#${k}: ${key} unknown node ${id}`);
      if (st.badge && !nodes[st.badge.node]) err(`${fl.id}#${k}: badge on unknown node ${st.badge.node}`);
    });
  }

  // ---- geometry that does not change between steps ----
  const icons = p.nodes.map((n) => ({ ...nodeBox(n), id: n.id }));
  const borders = [];
  for (const r of svg.querySelectorAll('rect.ap-group, rect.ap-cloud')) {
    const x = +r.getAttribute('x'), y = +r.getAttribute('y'), w = +r.getAttribute('width'), h = +r.getAttribute('height');
    const nm = r.getAttribute('class') + '@' + x + ',' + y;
    borders.push({ ...box(x, y, x + w, y, nm + ':top'), owner: nm, side: 'top' }, { ...box(x, y + h, x + w, y + h, nm + ':bottom'), owner: nm, side: 'bottom' },
      { ...box(x, y, x, y + h, nm + ':left'), owner: nm, side: 'left' }, { ...box(x + w, y, x + w, y + h, nm + ':right'), owner: nm, side: 'right' });
    if (x < 0 || y < 0 || x + w > vb.width || y + h > vb.height) err(`box outside the picture: ${nm}`);
  }
  const segs = [];
  for (const e of p.edges) for (let i = 1; i < e.pts.length; i += 1) segs.push({ e, i, a: e.pts[i - 1], b: e.pts[i], first: i === 1, last: i === e.pts.length - 1 });
  const obstacles = [...icons];           // things no line or text may touch
  if (p.blocked?.line) {
    const [[x1, y1], [x2, y2]] = p.blocked.line;
    segs.push({ e: { id: 'blocked', from: 'v1' }, i: 1, a: [x1, y1], b: [x2 - 12, y2], first: true, last: true, blocked: true });
    obstacles.push({ ...box(x2 - 10, y2 - 10, x2 + 10, y2 + 10, 'blocked ✕'), id: 'blocked-x' });
  }
  // Arrowheads: HEAD units long and wide, tip on the end of the edge.
  const HEAD = 14;
  const heads = p.edges.map((e) => {
    const [ax, ay] = e.pts[e.pts.length - 2], [bx, by] = e.pts[e.pts.length - 1];
    const dx = Math.sign(bx - ax), dy = Math.sign(by - ay);
    const b = dx ? box(bx - dx * HEAD, by - HEAD / 2, bx, by + HEAD / 2) : box(bx - HEAD / 2, by - dy * HEAD, bx + HEAD / 2, by);
    return { ...b, name: 'arrowhead:' + e.id, e };
  });
  const onEdge = (pt, b) => {
    const [x, y] = pt, eps = 0.6;
    const inX = x >= b.x1 - eps && x <= b.x2 + eps, inY = y >= b.y1 - eps && y <= b.y2 + eps;
    return ((Math.abs(x - b.x1) < eps || Math.abs(x - b.x2) < eps) && inY) || ((Math.abs(y - b.y1) < eps || Math.abs(y - b.y2) < eps) && inX);
  };
  for (const e of p.edges) {
    const f = nodes[e.from], t = nodes[e.to];
    if (!f || !t) continue;
    if (!onEdge(e.pts[0], nodeBox(f))) err(`${e.id}: start ${e.pts[0]} is not on the edge of ${e.from}`);
    if (!onEdge(e.pts[e.pts.length - 1], nodeBox(t))) err(`${e.id}: end ${e.pts[e.pts.length - 1]} is not on the edge of ${e.to}`);
    const [ax, ay] = e.pts[e.pts.length - 2], [bx, by] = e.pts[e.pts.length - 1], tb = nodeBox(t);
    const into = (bx === tb.x1 && ax < bx) || (bx === tb.x2 && ax > bx) || (by === tb.y1 && ay < by) || (by === tb.y2 && ay > by);
    if (!into) err(`${e.id}: does not arrive from outside ${e.to}`);
    if (t.icon !== 'doc' && by === tb.y2) err(`${e.id}: arrives at the bottom of ${e.to}, under its name`);
  }
  for (const s of segs) {
    const [ax, ay] = s.a, [bx, by] = s.b;
    if (ax !== bx && ay !== by) err(`${s.e.id}#${s.i}: not horizontal or vertical`);
    const len = Math.abs(ax - bx) + Math.abs(ay - by);
    if (s.last && !s.blocked && len < 2 * HEAD) err(`${s.e.id}: last segment ${len} too short for the arrowhead`);
    if (len < 14) err(`${s.e.id}#${s.i}: segment ${len} too short`);
    const sb = box(ax, ay, bx, by, '');
    for (const ob of obstacles) {
      const own = (s.first && ob.id === s.e.from) || (s.last && ob.id === s.e.to) || (s.blocked && ob.id === 'blocked-x');
      if (own ? hit(grow(sb, 0.5), grow(ob, -1.2)) : hit(grow(sb, P + HALF), ob)) err(`${s.e.id}#${s.i} crosses ${ob.name}`);
    }
    if (sb.x1 < 0 || sb.y1 < 0 || sb.x2 > vb.width || sb.y2 > vb.height) err(`${s.e.id}#${s.i} leaves the picture`);
  }
  for (const h of heads) {
    for (const ob of obstacles) if (ob.id !== h.e.to && hit(grow(h, 2), ob)) err(`${h.name} touches ${ob.name}`);
    for (const s of segs) if (s.e !== h.e && !(s.e.fork === h.e.id || h.e.fork === s.e.id) && hit(grow(h, 1), grow(box(...s.a, ...s.b), HALF))) err(`${h.name} touches ${s.e.id}#${s.i}`);
    for (const g of heads) if (g !== h && hit(grow(h, 1), g)) err(`${h.name} touches ${g.name}`);
  }
  // Two edges that fork share their first stretch; past the branch point they are separate lines.
  const branch = (e1, e2) => {
    let i = 1, j = 1, at = e1.pts[0];
    if (at[0] !== e2.pts[0][0] || at[1] !== e2.pts[0][1]) return null;
    while (i < e1.pts.length && j < e2.pts.length) {
      const a = e1.pts[i], b = e2.pts[j];
      const da = [Math.sign(a[0] - at[0]), Math.sign(a[1] - at[1])], db = [Math.sign(b[0] - at[0]), Math.sign(b[1] - at[1])];
      if (da[0] !== db[0] || da[1] !== db[1]) break;
      const la = Math.abs(a[0] - at[0]) + Math.abs(a[1] - at[1]), lb = Math.abs(b[0] - at[0]) + Math.abs(b[1] - at[1]);
      at = la <= lb ? a : b;
      if (la <= lb) i += 1;
      if (lb <= la) j += 1;
    }
    const rest = (e, k) => [at, ...e.pts.slice(k)];
    return { at, r1: rest(e1, i), r2: rest(e2, j) };
  };
  const segsOf = (pts) => pts.slice(1).map((b, k) => ({ a: pts[k], b }));
  for (let i = 0; i < segs.length; i += 1) for (let j = i + 1; j < segs.length; j += 1) {
    const s = segs[i], u = segs[j];
    if (s.e === u.e || s.e.fork === u.e.id || u.e.fork === s.e.id) continue;
    const sh = s.a[1] === s.b[1], uh = u.a[1] === u.b[1];
    const sb = box(...s.a, ...s.b), ub = box(...u.a, ...u.b);
    if (sh === uh) {
      const near = sh ? Math.abs(s.a[1] - u.a[1]) : Math.abs(s.a[0] - u.a[0]);
      const ov = sh ? Math.min(sb.x2, ub.x2) - Math.max(sb.x1, ub.x1) : Math.min(sb.y2, ub.y2) - Math.max(sb.y1, ub.y1);
      if (near < 14 && ov > -10) err(`${s.e.id}#${s.i} runs ${near} units from ${u.e.id}#${u.i}`);
    } else if (hit(grow(sb, 0.5), grow(ub, 0.5))) {
      err(`${s.e.id}#${s.i} crosses ${u.e.id}#${u.i}`);
    }
  }
  for (const e of p.edges) {
    if (!e.fork || !edges[e.fork]) continue;
    const b = branch(e, edges[e.fork]);
    if (!b) { err(`${e.id}: does not start where ${e.fork} starts`); continue; }
    for (const s of segsOf(b.r1)) for (const u of segsOf(b.r2)) {
      const sb = box(...s.a, ...s.b), ub = box(...u.a, ...u.b);
      const atBranch = (seg) => seg.a[0] === b.at[0] && seg.a[1] === b.at[1];
      if (atBranch(s) && atBranch(u)) continue;   // both leave the branch point, in different directions
      if (hit(grow(sb, 0.5), grow(ub, 0.5))) err(`${e.id} meets ${e.fork} again after they split`);
    }
  }

  // ---- what changes per step: text sizes and weights, the badge ----
  const measure = () => {
    const texts = [];
    for (const t of svg.querySelectorAll('text')) {
      const b = t.getBBox();
      if (!b.width) continue;
      const cls = t.getAttribute('class') || (t.closest('#ap-badge') ? 'badge' : '');
      if (t.closest('#ap-badge')) continue;
      let owner = t.closest('.ap-node')?.dataset.id || t.dataset.edge || cls;
      if (cls.startsWith('ap-group')) owner = 'ap-group@' + (+t.getAttribute('x') - 12) + ',' + (+t.getAttribute('y') - (cls === 'ap-group-sub' ? 44 : 24));
      if (cls === 'ap-cloud-title') owner = 'ap-cloud@' + (+t.getAttribute('x') - 42) + ',6';
      texts.push({ ...box(b.x, b.y, b.x + b.width, b.y + b.height, `${cls}[${t.textContent}]`), owner, cls });
    }
    return texts;
  };
  const checkTexts = () => {
    const texts = measure();
    for (const s of segs) {
      const sb = grow(box(...s.a, ...s.b), P + HALF);
      for (const tx of texts) if (hit(sb, tx)) err(`${s.e.id}#${s.i} crosses text ${tx.name}`);
    }
    for (const h of heads) for (const tx of texts) if (hit(grow(h, 2), tx)) err(`${h.name} touches text ${tx.name}`);
    for (let i = 0; i < texts.length; i += 1) {
      const a = texts[i];
      if (a.x1 < 2 || a.y1 < 2 || a.x2 > vb.width - 2 || a.y2 > vb.height - 2) err(`text leaves the picture: ${a.name}`);
      for (let j = i + 1; j < texts.length; j += 1) {
        const c = texts[j];
        if (a.owner === c.owner && a.cls !== 'ap-edge-label') continue;  // a name and its second line, a box title and its sub
        if (hit(grow(a, 2), c)) err(`text ${a.name} overlaps ${c.name}`);
      }
      for (const b of borders) {
        // A box's own title sits at a fixed offset from its top and left side.
        if (b.owner === a.owner && (b.side === 'top' || b.side === 'left')) continue;
        if (hit(grow(a, 5), grow(b, 1))) err(`text ${a.name} touches border ${b.name}`);
      }
      for (const ob of obstacles) {
        if (a.cls.startsWith('ap-doc') && ob.id === a.owner) continue;  // the routing document's own text
        if (hit(grow(a, ob.id === a.owner ? 2 : 4), ob)) err(`text ${a.name} overlaps ${ob.name}`);
      }
    }
    const badge = document.querySelector('#ap-badge rect');
    if (badge) {
      const r = badge.getBBox(), node = badge.closest('.ap-node').dataset.id;
      const bb = box(r.x, r.y, r.x + r.width, r.y + r.height, `badge on ${node}`);
      for (const s of segs) if (hit(grow(box(...s.a, ...s.b), P + HALF), bb)) err(`${bb.name} covers ${s.e.id}#${s.i}`);
      for (const h of heads) if (hit(grow(h, 2), bb)) err(`${bb.name} covers ${h.name}`);
      for (const tx of texts) if (!(tx.owner === node && tx.cls === 'ap-sub') && hit(grow(bb, 2), tx)) err(`${bb.name} overlaps ${tx.name}`);
      for (const b of borders) if (hit(grow(bb, 4), b)) err(`${bb.name} touches ${b.name}`);
      for (const ob of obstacles) if (hit(grow(bb, 2), ob)) err(`${bb.name} overlaps ${ob.name}`);
      if (r.width > 0 && document.querySelector('#ap-badge text').getComputedTextLength() > r.width - 12) err(`${bb.name}: text wider than its pill`);
    }
  };
  const showAll = () => { for (const g of svg.querySelectorAll('.ap-node, .ap-halo, .ap-edge, .ap-edge-label')) g.classList.remove('hidden', 'dim'); };
  // Every step of every flow, with everything shown (a superset of what any step shows), so bold
  // active labels, the flashing blocked text and badges are measured as they are drawn.
  showAll();
  checkTexts();
  for (const fl of p.flows) {
    selectFlow(fl);
    fl.steps.forEach((st, k) => {
      state = `${fl.id} step ${k + 1}`;
      applyStep(k);
      showAll();
      checkTexts();
    });
  }
  selectFlow(p.flows[0]);
  return [...errs].map(([msg, where]) => `${msg}  (${where})`);
}
"""


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass


async def run(site: Path, shots: Path | None) -> int:
    from playwright.async_api import async_playwright

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(site)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}/architecture.html"
    total = 0
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page(viewport={"width": 1700, "height": 1100})
            page_errors: list[str] = []
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            for lang in LANGS:
                for pattern in PATTERNS:
                    await page.goto(f"{base}?pattern={pattern}" + ("&lang=en" if lang == "en" else ""))
                    await page.wait_for_selector(".ap-node")
                    problems = await page.evaluate(CHECK)
                    total += len(problems)
                    print(f"{lang}-{pattern}: {len(problems)} problem(s)")
                    for problem in problems:
                        print(f"  {problem}")
                    if shots:
                        await page.wait_for_timeout(450)
                        await page.locator("#ap-svg").screenshot(path=str(shots / f"{lang}-{pattern}.png"))
            for err in page_errors:
                print(f"page error: {err}")
            total += len(page_errors)
            await browser.close()
    finally:
        server.shutdown()
    return total


def main() -> int:
    parser = argparse.ArgumentParser(prog="demo/check_arch_layout.py", description=__doc__.splitlines()[0])
    parser.add_argument("--site", type=Path, default=Path(__file__).resolve().parent / "site")
    parser.add_argument("--shots", type=Path, help="save a PNG of each diagram here")
    args = parser.parse_args()
    if args.shots:
        args.shots.mkdir(parents=True, exist_ok=True)
    total = asyncio.run(run(args.site.resolve(), args.shots))
    print("ok" if total == 0 else f"{total} problem(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
