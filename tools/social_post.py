#!/usr/bin/env python3
"""Daily "App of the Day" post to Discord (webhook) and Telegram (bot -> channel).

Runs in GitHub Actions. Secrets come from env vars:
  DISCORD_WEBHOOK_URL   (optional)
  TELEGRAM_BOT_TOKEN    (optional)
  TELEGRAM_CHANNEL      (optional, e.g. @mychannel or -100123...)
Picks one live app per day, rotating through the catalog (stateless: day number
mod app count). Skips apps whose Google Play page returns 404.
Use --dry-run to print without posting; --index N to force a specific app.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://sovereigndevelopers.org"
UA = {"User-Agent": "Mozilla/5.0 (compatible; SovereignAppBot/1.0)"}


def slug(app):
  s = app.get("id") or app["name"]
  return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def play_ok(pkg):
  try:
    req = urllib.request.Request(f"https://play.google.com/store/apps/details?id={pkg}&hl=en_US", headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
      return r.status == 200
  except urllib.error.HTTPError as e:
    return e.code != 404
  except Exception:
    return True  # network trouble: don't skip


def live_apps():
  apps = json.loads((ROOT / "apps" / "apps_data.json").read_text(encoding="utf-8"))
  return [a for a in apps if a.get("playLink") and "LIVE ON GOOGLE PLAY" in (a.get("badge") or "")]


def pick(apps, forced=None):
  n = len(apps)
  start = forced if forced is not None else date.today().toordinal() % n
  for k in range(n):
    a = apps[(start + k) % n]
    if play_ok(a["packageName"]):
      return a
  return None


def post_json(url, payload):
  req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                               headers={**UA, "Content-Type": "application/json"})
  with urllib.request.urlopen(req, timeout=30) as r:
    return r.status


def main():
  dry = "--dry-run" in sys.argv
  forced = None
  if "--index" in sys.argv:
    forced = int(sys.argv[sys.argv.index("--index") + 1])
  app = pick(live_apps(), forced)
  if not app:
    print("no live app found")
    return

  s = slug(app)
  page = f"{SITE}/apps/{s}/"
  icon = app.get("icon") or ""
  icon_url = SITE + icon if icon.startswith("/") else icon
  play = app["playLink"]
  name = app["name"]
  sub = app.get("subtitle") or ""
  desc = app.get("description") or sub
  tags = " ".join("#" + re.sub(r"[^A-Za-z0-9]", "", t) for t in (app.get("tags") or [])[:3])

  print(f"App of the Day: {name} -> {page}")
  if dry:
    return

  hook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
  if hook:
    try:
      st = post_json(hook + ("&" if "?" in hook else "?") + "wait=true", {
          "username": "Sovereign Developers",
          "embeds": [{
              "title": f"📱 App of the Day: {name}",
              "url": page,
              "description": f"**{sub}**\n\n{desc}\n\n[⬇️ Get it free on Google Play]({play})",
              "color": 0x00D4FF,
              "thumbnail": {"url": icon_url} if icon_url else None,
              "footer": {"text": "sovereigndevelopers.org"},
          }],
      })
      print("discord:", st)
    except Exception as e:
      print("discord failed:", str(e)[:200])

  tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
  chan = os.environ.get("TELEGRAM_CHANNEL", "").strip()
  if tok and chan:
    text = (f"📱 <b>App of the Day: {name}</b>\n<i>{sub}</i>\n\n{desc}\n\n"
            f"⬇️ <a href=\"{play}\">Get it free on Google Play</a>\n🌐 <a href=\"{page}\">More info</a>\n{tags}")
    try:
      if icon_url:
        st = post_json(f"https://api.telegram.org/bot{tok}/sendPhoto",
                       {"chat_id": chan, "photo": icon_url, "caption": text[:1024], "parse_mode": "HTML"})
      else:
        st = post_json(f"https://api.telegram.org/bot{tok}/sendMessage",
                       {"chat_id": chan, "text": text, "parse_mode": "HTML"})
      print("telegram:", st)
    except urllib.error.HTTPError as e:
      print("telegram failed:", e.code, e.read()[:200])
    except Exception as e:
      print("telegram failed:", str(e)[:200])


if __name__ == "__main__":
  main()
