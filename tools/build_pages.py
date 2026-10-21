#!/usr/bin/env python3
"""Build SEO pages for sovereigndevelopers.org from apps/apps_data.json.

Generates (all static, GitHub Pages friendly):
  apps/<id>/index.html   one real landing page per app (JSON-LD, Open Graph,
                         Twitter card, canonical URL, related-app links)
  sitemap.xml            every public page
  robots.txt             allows all crawlers, points at the sitemap
  llms.txt               plain-text app catalog for AI assistants
  feed.xml               RSS feed of the apps (lets feed readers / aggregators
                         pick the catalog up)

Stdlib only. Safe to re-run; output is deterministic so unchanged data produces
no git diff.
"""
import html
import json
import os
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://sovereigndevelopers.org"
DATA = ROOT / "apps" / "apps_data.json"
BRAND = "Sovereign Developers"
# Community links shown on every app page (leave "" to hide one).
TELEGRAM_URL = "https://t.me/sovereignapps"
MASTODON_URL = "https://mastodon.social/@sovereign_developers"
BLUESKY_URL = "https://bsky.app/profile/sovereigndeveloper.bsky.social"
DISCORD_URL = ""


def community_links():
  links = []
  if TELEGRAM_URL:
    links.append(f'<a href="{TELEGRAM_URL}" rel="noopener">Telegram</a>')
  if MASTODON_URL:
    links.append(f'<a href="{MASTODON_URL}" rel="me noopener">Mastodon</a>')
  if BLUESKY_URL:
    links.append(f'<a href="{BLUESKY_URL}" rel="noopener">Bluesky</a>')
  if DISCORD_URL:
    links.append(f'<a href="{DISCORD_URL}" rel="noopener">Discord</a>')
  return links


def community_block():
  links = community_links()
  if not links:
    return ""
  return ('<section style="background:#0a1f3a;border:1px solid #0d2847;border-radius:12px;padding:16px 18px">'
          '<h2>Get a free app pick every day</h2>'
          f'<p>Follow {BRAND} on ' + " or ".join(links) +
          ' for a new free Android app every day, plus updates on new releases.</p></section>')

E = html.escape


def slug(app):
  s = app.get("id") or app["name"]
  return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def is_live(app):
  return bool(app.get("playLink")) and "LIVE ON GOOGLE PLAY" in (app.get("badge") or "")


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<link rel="canonical" href="{url}">
<meta name="robots" content="{robots}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{brand}">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{meta_desc}">
<meta name="twitter:image" content="{image}">
<meta name="theme-color" content="#020818">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script type="application/ld+json">{jsonld}</script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#020818;color:#e0eaff;font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.6}}
a{{color:#00d4ff}}
nav{{display:flex;justify-content:space-between;align-items:center;padding:16px 24px;border-bottom:1px solid rgba(0,212,255,.12)}}
nav a{{text-decoration:none;font-weight:700;letter-spacing:2px;color:#fff}}
main{{max-width:860px;margin:0 auto;padding:40px 20px 64px}}
.hero{{display:flex;gap:24px;align-items:center;flex-wrap:wrap}}
.hero img{{width:112px;height:112px;border-radius:24px;background:#0a1f3a}}
h1{{font-size:clamp(1.7rem,4vw,2.5rem);line-height:1.2}}
.sub{{color:#7a9cc0;font-size:1.1rem;margin-top:6px}}
.cta{{display:inline-block;margin-top:22px;background:#00d4ff;color:#020818;font-weight:700;padding:14px 26px;border-radius:10px;text-decoration:none}}
.cta:hover{{background:#00ff88}}
.soon{{display:inline-block;margin-top:22px;border:1px solid #7a9cc0;color:#7a9cc0;padding:12px 22px;border-radius:10px}}
section{{margin-top:40px}}
h2{{font-size:1.25rem;margin-bottom:12px;color:#fff}}
.tags{{display:flex;flex-wrap:wrap;gap:8px}}
.tags span{{background:#0a1f3a;border:1px solid #0d2847;padding:4px 12px;border-radius:999px;font-size:.9rem}}
.rel{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}}
.rel a{{display:flex;gap:10px;align-items:center;background:#0a1f3a;border:1px solid #0d2847;border-radius:12px;padding:10px;text-decoration:none;color:#e0eaff}}
.rel img{{width:40px;height:40px;border-radius:10px}}
footer{{text-align:center;color:#7a9cc0;font-size:.85rem;padding:24px;border-top:1px solid rgba(0,212,255,.12)}}
</style>
</head>
<body>
<nav><a href="/">SOVEREIGN DEVELOPERS</a><a href="/apps/">All apps</a></nav>
<main>
<div class="hero">
<img src="{icon}" alt="{name} app icon" width="112" height="112">
<div><h1>{name}</h1><p class="sub">{subtitle}</p></div>
</div>
{cta}
<section><h2>About {name}</h2><p>{description}</p></section>
{tags_block}
<section><h2>Details</h2>
<p>Category: {category}<br>Platform: Android<br>Developer: {brand}{pkg_line}</p></section>
{community_block}
{related_block}
</main>
<footer>&copy; {year} {brand} &middot; <a href="/privacy-policy.html">Privacy</a> &middot; <a href="/terms.html">Terms</a> &middot; <a href="/apps/">All apps</a>{community_footer}</footer>
</body>
</html>
"""


def build_app_page(app, all_apps):
  s = slug(app)
  url = f"{SITE}/apps/{s}/"
  live = is_live(app)
  icon = app.get("icon") or "/favicon.svg"
  image = SITE + icon if icon.startswith("/") else icon
  name = app["name"]
  subtitle = app.get("subtitle") or ""
  desc = app.get("description") or subtitle
  title = f"{name} — {subtitle} | Android App" if subtitle else f"{name} | Android App"
  meta_desc = (desc[:155] + "…") if len(desc) > 158 else desc

  ld = {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": name,
      "description": desc,
      "applicationCategory": app.get("category") or "Application",
      "operatingSystem": "Android",
      "url": url,
      "image": image,
      "author": {"@type": "Organization", "name": BRAND, "url": SITE},
      "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
  }
  if live:
    ld["downloadUrl"] = app["playLink"]
    ld["installUrl"] = app["playLink"]
    ld["sameAs"] = [app["playLink"]]

  if live:
    play = app["playLink"] + ("&" if "?" in app["playLink"] else "?") + "referrer=utm_source%3Dsovereigndevelopers.org%26utm_medium%3Dapp_page"
    cta = f'<a class="cta" href="{E(play)}" rel="noopener">Get it on Google Play</a>'
  else:
    cta = f'<span class="soon">{E(app.get("badge") or "Coming soon")}</span>'

  tags = app.get("tags") or []
  tags_block = ""
  if tags:
    tags_block = '<section><h2>Highlights</h2><div class="tags">' + "".join(
        f"<span>{E(t)}</span>" for t in tags) + "</div></section>"

  same_cat = [a for a in all_apps if a is not app and is_live(a) and a.get("category") == app.get("category")]
  others = [a for a in all_apps if a is not app and is_live(a) and a not in same_cat]
  related = (same_cat + others)[:6]
  related_block = ""
  if related:
    related_block = '<section><h2>More apps from ' + BRAND + '</h2><div class="rel">' + "".join(
        f'<a href="/apps/{slug(a)}/"><img src="{E(a.get("icon") or "/favicon.svg")}" alt="" width="40" height="40" loading="lazy">'
        f'<span>{E(a["name"])}</span></a>' for a in related) + "</div></section>"

  pkg = app.get("packageName")
  return s, PAGE.format(
      title=E(title), meta_desc=E(meta_desc), url=url, brand=BRAND,
      robots="index,follow" if live else "noindex,follow",
      og_title=E(f"{name} — {subtitle}" if subtitle else name),
      image=E(image), icon=E(icon), name=E(name), subtitle=E(subtitle),
      jsonld=json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"),
      cta=cta, description=E(desc), tags_block=tags_block,
      category=E(app.get("category") or "Apps"),
      pkg_line=f"<br>Package: {E(pkg)}" if pkg else "",
      related_block=related_block, year=date.today().year,
      community_block=community_block(),
      community_footer="".join(" &middot; " + l for l in community_links()),
  ), live


def main():
  apps = json.loads(DATA.read_text(encoding="utf-8"))
  urls = [f"{SITE}/", f"{SITE}/apps/"]
  live_apps = []
  for app in apps:
    s, page, live = build_app_page(app, apps)
    out = ROOT / "apps" / s / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists() or out.read_text(encoding="utf-8") != page:
      out.write_text(page, encoding="utf-8", newline="\n")
    if live:
      urls.append(f"{SITE}/apps/{s}/")
      live_apps.append((s, app))

  for extra in ("privacy-policy.html", "terms.html", "child-safety-standards.html", "data-deletion.html"):
    if (ROOT / extra).exists():
      urls.append(f"{SITE}/{extra}")

  sm = ['<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
  sm += [f"  <url><loc>{E(u)}</loc></url>" for u in urls]
  sm.append("</urlset>")
  (ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8", newline="\n")

  (ROOT / "robots.txt").write_text(
      f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8", newline="\n")

  llms = [f"# {BRAND}", "",
          f"> Independent Android developer. {len(live_apps)} apps live on Google Play.", "",
          f"- Catalog: {SITE}/apps/", "", "## Apps on Google Play", ""]
  for s, a in live_apps:
    llms.append(f"- [{a['name']}]({SITE}/apps/{s}/): {a.get('subtitle') or ''} — Google Play: {a['playLink']}")
  (ROOT / "llms.txt").write_text("\n".join(llms) + "\n", encoding="utf-8", newline="\n")

  items = []
  for s, a in live_apps:
    items.append(
        f"<item><title>{E(a['name'])}</title><link>{SITE}/apps/{s}/</link>"
        f"<guid isPermaLink=\"true\">{SITE}/apps/{s}/</guid>"
        f"<description>{E(a.get('description') or '')}</description></item>")
  rss = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
         f"<title>{BRAND} — Android Apps</title><link>{SITE}/apps/</link>"
         f"<description>Apps by {BRAND} on Google Play</description>" + "".join(items) +
         "</channel></rss>\n")
  (ROOT / "feed.xml").write_text(rss, encoding="utf-8", newline="\n")

  print(f"pages: {len(apps)} (indexable: {len(live_apps)}), sitemap urls: {len(urls)}")
  inject_links(live_apps)


def inject_links(live_apps):
  idx = ROOT / "apps" / "index.html"
  if not idx.exists():
    return
  with open(idx, encoding="utf-8", newline="") as fh:
    src = fh.read()
  block = ("<!-- APP-PAGES:START -->\n"
           '<section style="max-width:1240px;margin:40px auto 0;padding:0 32px;font-size:.9rem;color:#7a9cc0">'
           '<h2 style="font-size:1rem;margin-bottom:8px;color:#e0eaff">App pages</h2><p>' +
           " &middot; ".join(f'<a href="/apps/{s}/" style="color:#00d4ff">{E(a["name"])}</a>' for s, a in live_apps) +
           "</p>" +
           ("<p style=\"margin-top:10px\">Free app pick every day: " + " &middot; ".join(community_links()) + "</p>"
            if community_links() else "") +
           "</section>\n<!-- APP-PAGES:END -->")
  if "<!-- APP-PAGES:START -->" in src:
    new = re.sub(r"<!-- APP-PAGES:START -->.*?<!-- APP-PAGES:END -->", lambda m: block, src, flags=re.S)
  elif "</main>" in src:
    new = src.replace("</main>", block + "\n</main>", 1)
  else:
    new = src.replace("</body>", block + "\n</body>", 1)
  if new != src:
    with open(idx, "w", encoding="utf-8", newline="") as fh:
      fh.write(new)


if __name__ == "__main__":
  main()
