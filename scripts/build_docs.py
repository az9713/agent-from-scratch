"""Build the self-contained GitHub Pages documentation from Markdown sources."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

import markdown


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Page:
    source: str
    output: str
    eyebrow: str
    short_title: str
    description: str
    metrics: tuple[tuple[str, str], ...]


PAGES = (
    Page(
        source="TESTS-EXPLAINED.md",
        output="tests-explained.html",
        eyebrow="Verification record / 09 tests",
        short_title="Tests, explained",
        description=(
            "What the suite proves, where its 63% branch coverage stops, "
            "and which failures deserve the next tests."
        ),
        metrics=(
            ("09", "deterministic tests"),
            ("63%", "branch coverage"),
            ("01", "real-SDK boundary test"),
        ),
    ),
    Page(
        source="DEVELOPMENT-JOURNEY.md",
        output="development-journey.html",
        eyebrow="Build trace / reconstructed session",
        short_title="Development journey",
        description=(
            "A warts-and-all account of extracting, reconstructing, teaching, "
            "and testing a coding agent from Tim's video."
        ),
        metrics=(
            ("37:24", "source video"),
            ("04", "local tools"),
            ("09", "passing tests"),
        ),
    ),
)


CSS = r"""
:root {
  --paper: #f5f7fa;
  --surface: #ffffff;
  --ink: #151b26;
  --muted: #5c6678;
  --rule: #d8dee9;
  --blue: #2857d9;
  --cyan: #008f95;
  --amber: #d88a00;
  --code: #111827;
  --code-ink: #dbeafe;
  --shadow: 0 24px 70px rgba(24, 39, 75, 0.10);
  --display: "Aptos Display", "Segoe UI Variable Display", "Trebuchet MS", sans-serif;
  --body: Charter, "Bitstream Charter", "Iowan Old Style", Georgia, serif;
  --utility: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  overflow-x: hidden;
  color: var(--ink);
  background:
    linear-gradient(rgba(40, 87, 217, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(40, 87, 217, 0.035) 1px, transparent 1px),
    var(--paper);
  background-size: 28px 28px;
  font-family: var(--body);
  font-size: 18px;
  line-height: 1.72;
}
a { color: var(--blue); text-underline-offset: 0.18em; }
a:hover { color: var(--cyan); }
a:focus-visible, button:focus-visible, summary:focus-visible {
  outline: 3px solid var(--amber);
  outline-offset: 4px;
}
.skip-link {
  position: fixed;
  z-index: 100;
  top: 10px;
  left: 10px;
  padding: 8px 12px;
  color: white;
  background: var(--ink);
  transform: translateY(-160%);
}
.skip-link:focus { transform: translateY(0); }
.progress {
  position: fixed;
  z-index: 50;
  inset: 0 0 auto 0;
  height: 3px;
  background: linear-gradient(90deg, var(--blue), var(--cyan));
  transform: scaleX(0);
  transform-origin: left;
}
.site-bar {
  min-height: 58px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 0 4vw;
  border-bottom: 1px solid rgba(216, 222, 233, 0.9);
  background: rgba(245, 247, 250, 0.90);
  backdrop-filter: blur(14px);
  font-family: var(--utility);
  font-size: 12px;
  letter-spacing: 0.04em;
}
.brand { color: var(--ink); text-decoration: none; font-weight: 700; }
.brand-mark { color: var(--cyan); }
.site-links { display: flex; gap: 18px; align-items: center; }
.site-links a { color: var(--muted); text-decoration: none; }
.hero {
  position: relative;
  overflow: hidden;
  padding: clamp(70px, 10vw, 132px) 5vw clamp(60px, 8vw, 110px);
  color: white;
  background: var(--ink);
}
.hero::after {
  content: "";
  position: absolute;
  width: min(52vw, 720px);
  aspect-ratio: 1;
  right: -17vw;
  top: -33%;
  border: 1px solid rgba(0, 184, 193, 0.32);
  border-radius: 50%;
  box-shadow:
    0 0 0 52px rgba(40, 87, 217, 0.08),
    0 0 0 104px rgba(0, 143, 149, 0.06);
}
.hero-inner { position: relative; z-index: 1; max-width: 1180px; margin: auto; }
.eyebrow {
  margin: 0 0 20px;
  color: #75e3e1;
  font: 700 12px/1.3 var(--utility);
  letter-spacing: 0.16em;
  text-transform: uppercase;
}
.hero h1 {
  max-width: 880px;
  margin: 0;
  font: 760 clamp(48px, 8vw, 104px)/0.94 var(--display);
  letter-spacing: -0.055em;
}
.hero-copy {
  max-width: 700px;
  margin: 28px 0 0;
  color: #bfc9d9;
  font: 400 clamp(18px, 2vw, 23px)/1.5 var(--body);
}
.metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  width: min(100%, 690px);
  max-width: 690px;
  margin-top: 44px;
  background: #354053;
  border: 1px solid #354053;
}
.metric { padding: 18px 20px; background: #1c2432; }
.metric strong {
  display: block;
  color: white;
  font: 720 25px/1 var(--display);
  letter-spacing: -0.03em;
}
.metric span {
  display: block;
  margin-top: 7px;
  color: #9faabc;
  font: 500 10px/1.3 var(--utility);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.mobile-index { display: none; }
.shell {
  display: grid;
  grid-template-columns: 250px minmax(0, 820px);
  gap: clamp(40px, 7vw, 100px);
  max-width: 1240px;
  margin: auto;
  padding: 72px 5vw 120px;
  align-items: start;
}
.rail {
  position: sticky;
  top: 32px;
  font-family: var(--utility);
}
.rail-label {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 18px;
  color: var(--muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.rail-label::before {
  content: "";
  width: 8px;
  height: 8px;
  background: var(--cyan);
  box-shadow: 0 0 0 5px rgba(0, 143, 149, 0.12);
  border-radius: 50%;
}
.toc { position: relative; margin: 0; padding: 0 0 0 18px; }
.toc > ul { margin: 0; padding: 0; list-style: none; }
.toc::before {
  content: "";
  position: absolute;
  left: 3px;
  top: 6px;
  bottom: 8px;
  width: 1px;
  background: var(--rule);
}
.toc ul ul { display: none; }
.toc li { margin: 0; }
.toc a {
  position: relative;
  display: block;
  padding: 7px 4px;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.35;
  text-decoration: none;
}
.toc a::before {
  content: "";
  position: absolute;
  left: -18px;
  top: 13px;
  width: 7px;
  height: 7px;
  border: 1px solid #9aa6b8;
  border-radius: 50%;
  background: var(--paper);
}
.toc a.active { color: var(--blue); font-weight: 700; }
.toc a.active::before { background: var(--blue); border-color: var(--blue); }
.article {
  min-width: 0;
  padding: clamp(28px, 5vw, 72px);
  background: var(--surface);
  border: 1px solid var(--rule);
  box-shadow: var(--shadow);
}
.article > h1 { display: none; }
.article h2 {
  margin: 3.4em 0 0.9em;
  padding-top: 0.35em;
  color: var(--ink);
  font: 720 clamp(30px, 4vw, 45px)/1.08 var(--display);
  letter-spacing: -0.035em;
  scroll-margin-top: 28px;
}
.article h2:first-of-type { margin-top: 0; }
.article h2::after {
  content: "";
  display: block;
  width: 72px;
  height: 4px;
  margin-top: 18px;
  background: linear-gradient(90deg, var(--blue), var(--cyan));
}
.article h3 {
  margin: 2.5em 0 0.65em;
  color: #24304a;
  font: 700 clamp(22px, 2.4vw, 28px)/1.2 var(--display);
  letter-spacing: -0.02em;
  scroll-margin-top: 28px;
}
.article p { margin: 0.9em 0; }
.article strong { color: #172c66; }
.article blockquote {
  margin: 1.8em 0;
  padding: 1px 0 1px 24px;
  color: #3e495b;
  border-left: 4px solid var(--cyan);
}
.article ul, .article ol { padding-left: 1.4em; }
.article li { margin: 0.38em 0; padding-left: 0.2em; }
.article li::marker { color: var(--blue); font-family: var(--utility); }
.article hr { border: 0; border-top: 1px solid var(--rule); margin: 3em 0; }
.article code {
  padding: 0.1em 0.35em;
  border: 1px solid #dbe2ef;
  border-radius: 3px;
  color: #113d91;
  background: #edf3ff;
  font: 0.82em/1.5 var(--utility);
  overflow-wrap: anywhere;
}
.article pre {
  position: relative;
  overflow-x: auto;
  margin: 1.6em 0;
  padding: 24px;
  color: var(--code-ink);
  background: var(--code);
  border-left: 4px solid var(--cyan);
  box-shadow: 0 14px 34px rgba(17, 24, 39, 0.16);
}
.article pre code { padding: 0; border: 0; color: inherit; background: transparent; }
.copy-code {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 5px 8px;
  color: #a8b4c8;
  background: #202b3c;
  border: 1px solid #3a4659;
  font: 600 10px/1 var(--utility);
  cursor: pointer;
}
.article table {
  width: 100%;
  margin: 1.8em 0;
  border-collapse: collapse;
  font-size: 0.91em;
}
.article th, .article td { padding: 12px 14px; border: 1px solid var(--rule); text-align: left; vertical-align: top; }
.article th { color: white; background: #263147; font-family: var(--utility); font-size: 0.78em; }
.page-footer {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 36px 5vw;
  color: #aeb8c8;
  background: var(--ink);
  font: 11px/1.5 var(--utility);
}
.page-footer a { color: #75e3e1; }

/* Landing page */
.landing { max-width: 1180px; margin: auto; padding: 72px 5vw 120px; }
.landing-intro { max-width: 760px; font-size: 22px; }
.doc-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-top: 52px; }
.doc-card {
  position: relative;
  min-height: 340px;
  padding: clamp(28px, 5vw, 54px);
  color: inherit;
  background: white;
  border: 1px solid var(--rule);
  box-shadow: var(--shadow);
  text-decoration: none;
  transition: transform 180ms ease, border-color 180ms ease;
}
.doc-card:hover { color: inherit; transform: translateY(-5px); border-color: var(--blue); }
.card-tag { color: var(--cyan); font: 700 11px/1 var(--utility); letter-spacing: 0.12em; text-transform: uppercase; }
.doc-card h2 { margin: 70px 0 18px; font: 740 clamp(30px, 4vw, 48px)/1 var(--display); letter-spacing: -0.04em; }
.doc-card p { color: var(--muted); }
.card-arrow { position: absolute; right: 32px; bottom: 28px; color: var(--blue); font: 700 24px/1 var(--utility); }
.loop-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  margin: 68px 0 0;
  border: 1px solid var(--rule);
  background: white;
}
.loop-step { position: relative; padding: 24px 16px; font: 600 11px/1.4 var(--utility); text-align: center; }
.loop-step + .loop-step { border-left: 1px solid var(--rule); }
.loop-step + .loop-step::before { content: "→"; position: absolute; left: -8px; color: var(--cyan); background: white; }

@media (max-width: 860px) {
  body { font-size: 17px; }
  .site-links { display: none; }
  .hero { padding-inline: 7vw; }
  .hero h1 { font-size: clamp(46px, 15vw, 72px); }
  .metrics { grid-template-columns: 1fr; max-width: 340px; }
  .shell { display: block; padding: 34px 4vw 70px; }
  .rail { display: none; }
  .mobile-index { display: block; margin: 0 0 20px; padding: 12px 16px; background: white; border: 1px solid var(--rule); font-family: var(--utility); font-size: 12px; }
  .mobile-index .toc { margin-top: 12px; }
  .article { padding: 32px 6vw 64px; box-shadow: none; }
  .doc-grid { grid-template-columns: 1fr; }
  .loop-strip { grid-template-columns: 1fr; }
  .loop-step + .loop-step { border-left: 0; border-top: 1px solid var(--rule); }
  .loop-step + .loop-step::before { content: "↓"; top: -8px; left: 50%; }
  .page-footer { flex-direction: column; }
}

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { transition: none !important; }
}

@media print {
  body { background: white; font-size: 11pt; }
  .progress, .site-bar, .rail, .mobile-index, .copy-code { display: none !important; }
  .hero { padding: 30px; color: black; background: white; border-bottom: 2px solid black; }
  .hero h1 { font-size: 34pt; }
  .hero-copy, .eyebrow { color: #333; }
  .metrics { background: white; border-color: #aaa; }
  .metric { color: black; background: white; }
  .metric strong, .metric span { color: black; }
  .shell { display: block; max-width: none; padding: 24px 0; }
  .article { max-width: none; padding: 0; border: 0; box-shadow: none; }
  .article h2, .article h3 { break-after: avoid; }
  .article pre, .article blockquote { break-inside: avoid; }
  .page-footer { color: black; background: white; border-top: 1px solid #aaa; }
}
"""


JS = r"""
const progress = document.querySelector('.progress');
const headings = [...document.querySelectorAll('.article h2, .article h3')];
const tocLinks = [...document.querySelectorAll('.toc a')];

function updateProgress() {
  const max = document.documentElement.scrollHeight - window.innerHeight;
  const ratio = max > 0 ? window.scrollY / max : 0;
  progress.style.transform = `scaleX(${Math.min(1, Math.max(0, ratio))})`;
}

const observer = new IntersectionObserver((entries) => {
  const visible = entries.filter((entry) => entry.isIntersecting).pop();
  if (!visible) return;
  tocLinks.forEach((link) => {
    link.classList.toggle('active', link.getAttribute('href') === `#${visible.target.id}`);
  });
}, { rootMargin: '-18% 0px -72% 0px', threshold: 0 });

headings.forEach((heading) => observer.observe(heading));
window.addEventListener('scroll', updateProgress, { passive: true });
updateProgress();

document.querySelectorAll('pre').forEach((pre) => {
  const button = document.createElement('button');
  button.className = 'copy-code';
  button.type = 'button';
  button.textContent = 'COPY';
  button.setAttribute('aria-label', 'Copy code block');
  button.addEventListener('click', async () => {
    await navigator.clipboard.writeText(pre.innerText.replace(/^COPY\n/, ''));
    button.textContent = 'COPIED';
    setTimeout(() => { button.textContent = 'COPY'; }, 1400);
  });
  pre.appendChild(button);
});
"""


def split_title(source: str) -> tuple[str, str]:
    lines = source.splitlines()
    if lines and lines[0].startswith("# "):
        return lines[0][2:].strip(), "\n".join(lines[1:])
    raise ValueError("Markdown source must begin with one H1 heading")


def convert(page: Page) -> str:
    source = (ROOT / page.source).read_text(encoding="utf-8")
    _source_title, body_source = split_title(source)
    engine = markdown.Markdown(
        extensions=["fenced_code", "tables", "toc", "sane_lists"],
        extension_configs={"toc": {"toc_depth": "2-3", "permalink": False}},
    )
    body = engine.convert(body_source)
    toc = engine.toc
    metrics = "".join(
        f'<div class="metric"><strong>{html.escape(value)}</strong>'
        f'<span>{html.escape(label)}</span></div>'
        for value, label in page.metrics
    )
    sibling = next(item for item in PAGES if item.output != page.output)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(page.description, quote=True)}">
  <meta name="theme-color" content="#151b26">
  <link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2064%2064'%3E%3Crect%20width='64'%20height='64'%20rx='8'%20fill='%23151b26'/%3E%3Ctext%20x='8'%20y='43'%20font-size='32'%20fill='%2375e3e1'%3E%3E_%3C/text%3E%3C/svg%3E">
  <title>{html.escape(page.short_title)} · Agent from scratch</title>
  <style>{CSS}</style>
</head>
<body>
  <a class="skip-link" href="#content">Skip to content</a>
  <div class="progress" aria-hidden="true"></div>
  <nav class="site-bar" aria-label="Site navigation">
    <a class="brand" href="index.html"><span class="brand-mark">&gt;_</span> agent/from-scratch</a>
    <div class="site-links">
      <a href="{sibling.output}">{html.escape(sibling.short_title)}</a>
      <a class="optional" href="https://github.com/az9713/agent-from-scratch">Source on GitHub</a>
    </div>
  </nav>
  <header class="hero">
    <div class="hero-inner">
      <p class="eyebrow">{html.escape(page.eyebrow)}</p>
      <h1>{html.escape(page.short_title)}</h1>
      <p class="hero-copy">{html.escape(page.description)}</p>
      <div class="metrics" aria-label="Document summary">{metrics}</div>
    </div>
  </header>
  <main class="shell" id="content">
    <aside class="rail" aria-label="Document trace">
      <div class="rail-label">Execution trace</div>
      {toc}
    </aside>
    <details class="mobile-index">
      <summary>Document index</summary>
      {toc}
    </details>
    <article class="article">
      {body}
    </article>
  </main>
  <footer class="page-footer">
    <span>Source: {html.escape(page.source)} · Generated deterministically</span>
    <span><a href="https://www.youtube.com/watch?v=c9AnqCeyxbI">Watch Tim's original video</a></span>
  </footer>
  <script>{JS}</script>
</body>
</html>
"""


def landing() -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="A tested, transcript-grounded reconstruction of Tech With Tim's pure-Python coding agent.">
  <meta name="theme-color" content="#151b26">
  <link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2064%2064'%3E%3Crect%20width='64'%20height='64'%20rx='8'%20fill='%23151b26'/%3E%3Ctext%20x='8'%20y='43'%20font-size='32'%20fill='%2375e3e1'%3E%3E_%3C/text%3E%3C/svg%3E">
  <title>Agent from scratch · Documentation</title>
  <style>{CSS}</style>
</head>
<body>
  <a class="skip-link" href="#content">Skip to content</a>
  <nav class="site-bar" aria-label="Site navigation">
    <a class="brand" href="index.html"><span class="brand-mark">&gt;_</span> agent/from-scratch</a>
    <div class="site-links">
      <a href="https://github.com/az9713/agent-from-scratch">Source on GitHub</a>
      <a class="optional" href="https://www.youtube.com/watch?v=c9AnqCeyxbI">Tim's video</a>
    </div>
  </nav>
  <header class="hero">
    <div class="hero-inner">
      <p class="eyebrow">Pure Python / visible machinery</p>
      <h1>Agent from scratch</h1>
      <p class="hero-copy">One model. Four local tools. A loop you can inspect. Reconstructed from Tech With Tim's tutorial, annotated from the transcript, and tested without hiding behind a framework.</p>
      <div class="metrics" aria-label="Project summary">
        <div class="metric"><strong>01</strong><span>model</span></div>
        <div class="metric"><strong>04</strong><span>local tools</span></div>
        <div class="metric"><strong>09</strong><span>passing tests</span></div>
      </div>
    </div>
  </header>
  <main class="landing" id="content">
    <p class="eyebrow" style="color: var(--blue)">Read the evidence</p>
    <p class="landing-intro">The code is deliberately small. The documentation is deliberately explicit. Start with the test record for confidence boundaries, or read the development journey for the choices, failures, and reconstruction gaps behind the finished agent.</p>
    <div class="doc-grid">
      <a class="doc-card" href="tests-explained.html">
        <span class="card-tag">Verification / coverage</span>
        <h2>Tests, explained</h2>
        <p>Every test, what it proves, what remains untested, and why 63% branch coverage is useful but not production assurance.</p>
        <span class="card-arrow" aria-hidden="true">→</span>
      </a>
      <a class="doc-card" href="development-journey.html">
        <span class="card-tag">Decisions / failures</span>
        <h2>Development journey</h2>
        <p>The full build trace: source recovery, gap-fills, near-misses, the exhausted-credit live test, and the final evidence boundary.</p>
        <span class="card-arrow" aria-hidden="true">→</span>
      </a>
    </div>
    <div class="loop-strip" aria-label="Agent execution loop">
      <div class="loop-step">01 · Prompt</div>
      <div class="loop-step">02 · Model</div>
      <div class="loop-step">03 · Tool call</div>
      <div class="loop-step">04 · Observation</div>
      <div class="loop-step">05 · Repeat or answer</div>
    </div>
  </main>
  <footer class="page-footer">
    <span>Transcript-grounded reconstruction · Python · OpenAI Chat Completions</span>
    <span><a href="https://github.com/az9713/agent-from-scratch">Read the source</a></span>
  </footer>
</body>
</html>
"""


def main() -> None:
    for page in PAGES:
        (ROOT / page.output).write_text(convert(page), encoding="utf-8", newline="\n")
        print(f"built {page.output} from {page.source}")
    (ROOT / "index.html").write_text(landing(), encoding="utf-8", newline="\n")
    print("built index.html")


if __name__ == "__main__":
    main()
