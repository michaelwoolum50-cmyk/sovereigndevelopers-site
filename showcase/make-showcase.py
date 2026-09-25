#!/usr/bin/env python3
"""Generate a per-app showcase page for sovereigndevelopers.org.

Usage: python3 make-showcase.py <manifest.json>
  Reads showcase/<slug>.json, writes apps/<slug>.html

Manifest fields:
  slug         url-safe id, e.g. "spinstakes"
  name         display name, e.g. "SpinStakes"
  tagline      one-line hook under the name
  description  2-4 sentence product description (plain words)
  icon         path relative to site root, e.g. "static/apps/spinstakes-icon.png"
  screenshots  list of {src, caption} — exactly what a user sees in the app
  play_url     full Google Play listing URL, or null when not public yet
  status       "live" | "coming_soon" | "early_access"

Asset rules (enforced, not suggested):
  - icon: 512x512 PNG, no stretching, no clipped edges, no text baked over UI
  - screenshots: real app screens as the user sees them (device-walk captures),
    1080x1920 portrait preferred; never mockups of upload dialogs, never
    browser chrome, never instructional text baked into the image
"""
import json, os, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<title>{name} — Sovereign Developers</title>
<meta name="description" content="{tagline}" />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=DM+Sans:wght@300;400;500;600&display=swap" />
<style>
  :root {{ --bg:#070d14; --gold:#c9a84c; --ink:#eef2f6; --mut:#8ba4b8; --card:#0d1622; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:var(--bg); color:var(--ink); font-family:'DM Sans',sans-serif; line-height:1.6; }}
  a {{ color:var(--gold); }}
  .wrap {{ max-width:1080px; margin:0 auto; padding:0 24px; }}
  header.top {{ padding:22px 0; border-bottom:1px solid #16222f; }}
  header.top a.home {{ display:inline-flex; align-items:center; gap:12px; text-decoration:none; color:var(--ink);
    font-family:'Cinzel',serif; letter-spacing:2px; font-size:14px; }}
  header.top img {{ width:34px; height:34px; border-radius:8px; object-fit:cover; }}
  .hero {{ display:flex; gap:36px; align-items:center; padding:56px 0 40px; flex-wrap:wrap; }}
  .hero img.icon {{ width:168px; height:168px; border-radius:36px; object-fit:cover;
    box-shadow:0 18px 50px rgba(0,0,0,.55), 0 0 0 1px #1d2c3d; }}
  .hero h1 {{ font-family:'Cinzel',serif; font-size:44px; letter-spacing:1px; margin-bottom:6px; }}
  .hero p.tag {{ color:var(--gold); font-size:18px; margin-bottom:18px; }}
  .storebtn {{ display:inline-block; background:var(--gold); color:#0a0f16; font-weight:600;
    padding:14px 30px; border-radius:12px; text-decoration:none; font-size:17px; }}
  .storebtn:hover {{ filter:brightness(1.08); }}
  .storebtn.disabled {{ background:#24303d; color:var(--mut); cursor:default; }}
  .badge {{ display:inline-block; font-size:12px; letter-spacing:2px; text-transform:uppercase; color:var(--mut);
    border:1px solid #22303f; border-radius:999px; padding:6px 14px; margin-bottom:14px; }}
  section {{ padding:34px 0; }}
  h2 {{ font-family:'Cinzel',serif; font-size:26px; margin-bottom:18px; letter-spacing:1px; }}
  .shots {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:20px; }}
  figure.shot {{ background:var(--card); border:1px solid #16222f; border-radius:16px; overflow:hidden; }}
  figure.shot img {{ width:100%; aspect-ratio:9/16; object-fit:cover; display:block; background:#000; }}
  figure.shot figcaption {{ padding:12px 14px; font-size:14px; color:var(--mut); }}
  .desc {{ font-size:18px; font-weight:300; max-width:760px; color:#d7dee6; }}
  .pending {{ border:1px dashed #2a3a4d; border-radius:16px; padding:28px; color:var(--mut); text-align:center; }}
  footer {{ border-top:1px solid #16222f; margin-top:40px; padding:26px 0 60px; color:var(--mut); font-size:13px; }}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <a class="home" href="/"><img src="/static/sovereign-developers-logo.png" alt="Sovereign Developers" />SOVEREIGN DEVELOPERS</a>
</div></header>
<div class="wrap">
  <div class="hero">
    <img class="icon" src="/{icon}" alt="{name} app icon" />
    <div>
      <span class="badge">{status_label}</span>
      <h1>{name}</h1>
      <p class="tag">{tagline}</p>
      {cta}
    </div>
  </div>
  <section>
    <h2>Inside the app</h2>
    {gallery}
  </section>
  <section>
    <h2>About {name}</h2>
    <p class="desc">{description}</p>
  </section>
</div>
<footer><div class="wrap">© Sovereign Developers · Every product scaled, every line of code owned by us.</div></footer>
</body>
</html>
"""

def main():
    mf_path = sys.argv[1]
    m = json.load(open(mf_path))
    for k in ("slug","name","tagline","description","icon","screenshots","status"):
        assert k in m, f"manifest missing '{k}'"
    shots = m["screenshots"]
    assert 0 <= len(shots) <= 4, "0-4 screenshots"
    if shots:
        gallery = '<div class="shots">\n' + "\n".join(
            '  <figure class="shot"><img src="/%s" alt="%s" loading="lazy" /><figcaption>%s</figcaption></figure>'
            % (html.escape(s["src"]), html.escape(m["name"]+" screenshot"),
               html.escape(s.get("caption",""))) for s in shots) + "\n</div>"
    else:
        gallery = ('<div class="pending">Walkthrough screenshots land here straight from the '
                   'device walk — real screens, exactly as a user sees them. No mockups, ever.</div>')
    labels = {"live":"Live on Google Play","coming_soon":"Coming soon","early_access":"Early access"}
    if m["status"]=="live" and m.get("play_url"):
        cta = '<a class="storebtn" href="%s">Get it on Google Play</a>' % html.escape(m["play_url"], quote=True)
    else:
        cta = '<span class="storebtn disabled">Coming soon to Google Play</span>'
    page = PAGE.format(
        name=html.escape(m["name"]), tagline=html.escape(m["tagline"]),
        description=html.escape(m["description"]),
        icon=html.escape(m["icon"]), gallery=gallery,
        status_label=labels.get(m["status"], m["status"]), cta=cta)
    out = os.path.join(ROOT, "apps", m["slug"] + ".html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out,"w").write(page)
    print("wrote", out, "(%d screenshots, status=%s)" % (len(shots), m["status"]))

if __name__ == "__main__":
    main()
