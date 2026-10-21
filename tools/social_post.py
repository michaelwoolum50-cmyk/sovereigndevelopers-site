#!/usr/bin/env python3
"""Daily "App of the Day" post to Discord, Telegram, Mastodon, and Bluesky.

Runs in GitHub Actions (stdlib only). Secrets come from env vars:
  DISCORD_WEBHOOK_URL   (optional)
  TELEGRAM_BOT_TOKEN    (optional)
  TELEGRAM_CHANNEL      (optional, e.g. @sovereignapps)
  MASTODON_TOKEN        (optional)
  MASTODON_INSTANCE     (optional, defaults to https://mastodon.social)
  BLUESKY_HANDLE        (optional, e.g. sovereigndeveloper.bsky.social)
  BLUESKY_APP_PASSWORD  (optional)
Picks one live app per day, rotating through the catalog (stateless: day number
mod app count). Skips apps whose Google Play page returns 404.
Use --dry-run to print without posting; --index N to force a specific app.
"""
import datetime
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


def post_json(url, payload, extra_headers=None):
  hdrs = {**UA, "Content-Type": "application/json"}
  if extra_headers:
    hdrs.update(extra_headers)
  req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=hdrs)
  with urllib.request.urlopen(req, timeout=30) as r:
    return r.status, json.loads(r.read().decode("utf-8") or "{}")


def fetch_icon_bytes(icon_path_or_url):
  if not icon_path_or_url:
    return None, "image/png"
  if icon_path_or_url.startswith("/"):
    local = ROOT / icon_path_or_url.lstrip("/")
    if local.exists():
      mime = "image/jpeg" if local.suffix.lower() in (".jpg", ".jpeg") else "image/png"
      return local.read_bytes(), mime
    icon_path_or_url = SITE + icon_path_or_url
  try:
    req = urllib.request.Request(icon_path_or_url, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:
      return r.read(), r.headers.get("Content-Type", "image/png")
  except Exception:
    return None, "image/png"


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
  clean_tags = [re.sub(r"[^A-Za-z0-9]", "", t) for t in (app.get("tags") or [])[:3]]
  clean_tags = [t for t in clean_tags if t] + ["Android", "GooglePlay", "AppOfTheDay"]
  tags = " ".join("#" + t for t in clean_tags)

  print(f"App of the Day: {name} -> {page}")
  if dry:
    return

  # 1. Discord
  hook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
  if hook:
    try:
      st, _ = post_json(hook + ("&" if "?" in hook else "?") + "wait=true", {
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

  # 2. Telegram
  tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
  chan = os.environ.get("TELEGRAM_CHANNEL", "").strip()
  if tok and chan:
    text = (f"📱 <b>App of the Day: {name}</b>\n<i>{sub}</i>\n\n{desc}\n\n"
            f"⬇️ <a href=\"{play}\">Get it free on Google Play</a>\n🌐 <a href=\"{page}\">More info</a>\n{tags}")
    try:
      if icon_url:
        st, _ = post_json(f"https://api.telegram.org/bot{tok}/sendPhoto",
                          {"chat_id": chan, "photo": icon_url, "caption": text[:1024], "parse_mode": "HTML"})
      else:
        st, _ = post_json(f"https://api.telegram.org/bot{tok}/sendMessage",
                          {"chat_id": chan, "text": text, "parse_mode": "HTML"})
      print("telegram:", st)
    except urllib.error.HTTPError as e:
      print("telegram failed:", e.code, e.read()[:200])
    except Exception as e:
      print("telegram failed:", str(e)[:200])

  # 3. Mastodon
  m_tok = os.environ.get("MASTODON_TOKEN", "").strip()
  m_inst = (os.environ.get("MASTODON_INSTANCE", "").strip() or "https://mastodon.social").rstrip("/")
  if m_tok:
    m_desc = desc if len(desc) <= 220 else (desc[:217] + "...")
    m_status = (
        f"📱 App of the Day: {name}\n"
        f"{sub}\n\n"
        f"{m_desc}\n\n"
        f"⬇️ Free on Google Play: {play}\n"
        f"🌐 {page}\n"
        f"{tags}"
    )[:495]
    try:
      st, resp = post_json(
          f"{m_inst}/api/v1/statuses",
          {"status": m_status, "visibility": "public"},
          {"Authorization": f"Bearer {m_tok}"},
      )
      print("mastodon:", st, resp.get("url", ""))
    except urllib.error.HTTPError as e:
      print("mastodon failed:", e.code, e.read()[:200])
    except Exception as e:
      print("mastodon failed:", str(e)[:200])

  # 4. Bluesky
  b_handle = os.environ.get("BLUESKY_HANDLE", "").strip()
  b_pw = os.environ.get("BLUESKY_APP_PASSWORD", "").strip()
  if b_handle and b_pw:
    try:
      _, ses = post_json(
          "https://bsky.social/xrpc/com.atproto.server.createSession",
          {"identifier": b_handle, "password": b_pw},
      )
      jwt = ses["accessJwt"]
      did = ses["did"]
      auth_hdr = {"Authorization": f"Bearer {jwt}"}

      blob = None
      img_bytes, mime = fetch_icon_bytes(icon)
      if img_bytes and len(img_bytes) < 950_000:
        try:
          req = urllib.request.Request(
              "https://bsky.social/xrpc/com.atproto.repo.uploadBlob",
              data=img_bytes,
              headers={**UA, **auth_hdr, "Content-Type": mime},
          )
          with urllib.request.urlopen(req, timeout=20) as r:
            blob = json.loads(r.read().decode("utf-8")).get("blob")
        except Exception:
          blob = None

      short_desc = desc if len(desc) <= 130 else (desc[:127] + "...")
      b_text = (
          f"📱 App of the Day: {name}\n"
          f"{ short_desc }\n\n"
          f"🌐 {page}\n"
          f"#Android #GooglePlay #AppOfTheDay"
      )
      if len(b_text) > 295:
        b_text = b_text[:295]

      b_bytes = b_text.encode("utf-8")
      facets = []
      p_bytes = page.encode("utf-8")
      idx = b_bytes.find(p_bytes)
      if idx >= 0:
        facets.append({
            "index": {"byteStart": idx, "byteEnd": idx + len(p_bytes)},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": page}],
        })
      for tg in ["Android", "GooglePlay", "AppOfTheDay"]:
        tb = f"#{tg}".encode("utf-8")
        t_idx = b_bytes.find(tb)
        if t_idx >= 0:
          facets.append({
              "index": {"byteStart": t_idx, "byteEnd": t_idx + len(tb)},
              "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tg}],
          })

      external = {
          "uri": play,
          "title": f"{name} — Free on Google Play",
          "description": sub or desc[:160],
      }
      if blob:
        external["thumb"] = blob

      now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
      st, b_resp = post_json(
          "https://bsky.social/xrpc/com.atproto.repo.createRecord",
          {
              "repo": did,
              "collection": "app.bsky.feed.post",
              "record": {
                  "$type": "app.bsky.feed.post",
                  "text": b_text,
                  "createdAt": now_iso,
                  "facets": facets,
                  "embed": {"$type": "app.bsky.embed.external", "external": external},
              },
          },
          auth_hdr,
      )
      print("bluesky:", st, b_resp.get("uri", ""))
    except urllib.error.HTTPError as e:
      print("bluesky failed:", e.code, e.read()[:200])
    except Exception as e:
      print("bluesky failed:", str(e)[:200])


if __name__ == "__main__":
  main()
