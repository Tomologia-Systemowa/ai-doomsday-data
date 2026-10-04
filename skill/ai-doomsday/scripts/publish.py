#!/usr/bin/env python3
"""Writes AI Doomsday data into a cloned repo (no commit).

Usage:
  python3 publish.py report --scored scored.json --repo <repo>
  python3 publish.py seed --entries seed.json --repo <repo>

report: overwrites data/latest.json, creates/updates the daily file
        data/history/history-DD-MM-YYYY.json (score, categories, events and
        the full report text in both languages) and data/history/index.json,
        adds threshold_cross events automatically (status change vs the
        previous latest.json), creates scale.json and README.md if missing.
        Never touches data/history.json.
seed:   creates daily files from historical entries
        [{date, kind, score, categories, headline, headline_en}],
        skipping dates whose file already exists.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from config import (SCHEMA_VERSION, TZ, DISCLAIMER, DISCLAIMER_EN, BUDGETS, BANDS,
                    CATEGORY_NAMES, STATUS_EMOJI, EVENT_TYPES, SEVERITIES,
                    band_for, daily_filename)



def repo_urls(repo):
    """Web URL and raw base URL derived from the clone's own origin remote."""
    try:
        url = subprocess.run(["git", "-C", repo, "remote", "get-url", "origin"],
                             capture_output=True, text=True, check=True).stdout.strip()
        branch = subprocess.run(["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip() or "main"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None
    url = re.sub(r"^git@github\.com:", "https://github.com/", url)
    url = re.sub(r"https://[^@/]+@", "https://", url)          # strip credentials
    url = re.sub(r"\.git$", "", url)
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)$", url)
    raw = f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{branch}" if m else None
    return url, raw


def now_iso():
    return datetime.now(ZoneInfo(TZ)).isoformat(timespec="seconds")


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def die(msg):
    sys.exit(f"ERROR: {msg}")


def ensure_static(repo):
    scale_p = os.path.join(repo, "data", "scale.json")
    if not os.path.exists(scale_p):
        dump(scale_p, {
            "schema_version": SCHEMA_VERSION,
            "bands": [{"min": lo, "max": hi, "band": pl, "band_en": en} for lo, hi, pl, en in BANDS],
            "categories": {c: {"name": CATEGORY_NAMES[c][0], "name_en": CATEGORY_NAMES[c][1],
                               "budget": b} for c, b in BUDGETS.items()},
            "total": 1000,
        })
        print("Created data/scale.json")
    readme = os.path.join(repo, "README.md")
    if not os.path.exists(readme):
        web, raw = repo_urls(repo)
        text = open(os.path.join(HERE, "..", "assets", "README.md"), encoding="utf-8").read()
        text = text.replace("{{RAW_BASE}}", raw or "<raw-base-url>")
        text = text.replace("{{REPO_URL}}", web or "<repo-url>")
        with open(readme, "w", encoding="utf-8") as f:
            f.write(text)
        print("Created README.md")


def upsert_index(repo, d, kind, score, band):
    p = os.path.join(repo, "data", "history", "index.json")
    idx = load(p, {"files": []})
    files = [f for f in idx.get("files", []) if f["date"] != d]
    files.append({"date": d, "file": daily_filename(d), "kind": kind, "score": score, "band": band})
    files.sort(key=lambda f: f["date"])
    dump(p, {"schema_version": SCHEMA_VERSION, "updated_at": now_iso(), "files": files})


def write_daily(repo, d, entry, new_events, report=None):
    p = os.path.join(repo, "data", "history", daily_filename(d))
    old = load(p, {})
    events = list(old.get("events", []))
    keys = {(e["date"], e.get("signal"), e["title"]) for e in events}
    added = 0
    for e in new_events:
        k = (e["date"], e.get("signal"), e["title"])
        if k not in keys:
            events.append(e); keys.add(k); added += 1
    body = {"schema_version": SCHEMA_VERSION, "date": d, "updated_at": now_iso(),
            "entry": entry, "events": events}
    if report is not None:
        body["report"] = report
    elif "report" in old:
        body["report"] = old["report"]
    dump(p, body)
    return p, added


def check_event(e):
    req = ("date", "type", "severity", "title", "title_en") + (() if e.get("type") == "threshold_cross" else ("source",))
    missing = [k for k in req if not e.get(k)]
    if missing:
        die(f"event {e.get('title')!r} is missing {missing}")
    if e["type"] not in EVENT_TYPES or e["severity"] not in SEVERITIES:
        die(f"event {e['title']!r}: invalid type/severity")


def pair(sc, key, required):
    pl, en = sc.get(key), sc.get(key + "_en")
    if required and not pl:
        die(f"report is missing {key}")
    if pl and not en:
        die(f"report has {key} but no {key}_en")
    return pl or None, en or None


def build_report(sc, out_signals):
    full = sc["report_type"] == "full"
    summary, summary_en = pair(sc, "summary", True)
    curve, curve_en = pair(sc, "curve_comment", full)
    weekly, weekly_en = pair(sc, "weekly_analysis", False)
    comments = {}
    for c in BUDGETS:
        cc = (sc.get("category_comments") or {}).get(c)
        if cc:
            if not cc.get("comment") or not cc.get("comment_en"):
                die(f"category_comments.{c} needs comment and comment_en")
            comments[c] = {"comment": cc["comment"], "comment_en": cc["comment_en"]}
        elif full:
            die(f"full report is missing category_comments.{c}")
    top = sorted([s for s in sc["signals"] if s["points"] > 0], key=lambda s: -s["points"])[:3]
    return {
        "summary": summary, "summary_en": summary_en,
        "curve_comment": curve, "curve_comment_en": curve_en,
        "category_comments": comments or None,
        "top_signals": [s["id"] for s in top],
        "near_boundary": bool(sc.get("near_boundary")),
        "weekly_analysis": weekly, "weekly_analysis_en": weekly_en,
        "adjustments": sc.get("adjustments", []),
        "signals": out_signals,
        "calendar": sc.get("calendar", []),
    }


def cmd_report(a):
    sc = load(a.scored)
    repo, d = a.repo, sc["date"]
    ensure_static(repo)
    latest_p = os.path.join(repo, "data", "latest.json")
    prev_latest = load(latest_p, {}) or {}
    prev_status = {s["id"]: s.get("status") for s in prev_latest.get("signals", [])}

    idx = load(os.path.join(repo, "data", "history", "index.json"), {"files": []})
    prev_scores = [f for f in idx.get("files", []) if f["date"] < d and f.get("score") is not None]
    change = sc["score"] - prev_scores[-1]["score"] if prev_scores else None

    headline, headline_en = pair(sc, "headline", True)
    for t in sc.get("triggers", []):
        if not t.get("name_en"):
            die(f"trigger {t.get('name')!r} needs name_en")
    for c in sc.get("calendar", []):
        if not c.get("title") or not c.get("title_en"):
            die(f"calendar item {c!r} needs title and title_en")

    events = list(sc.get("events", []))
    repo_web = repo_urls(repo)[0]
    for s in sc["signals"]:
        old, new = prev_status.get(s["id"]), s["status"]
        if old and old != new:
            events.append({
                "date": d, "type": "threshold_cross", "signal": s["id"],
                "severity": "medium" if new == "red" else "info",
                "title": f"{s['id']} {s['name']}: zmiana statusu {STATUS_EMOJI[old]} → {STATUS_EMOJI[new]}",
                "title_en": f"{s['id']} {s['name_en']}: status change {STATUS_EMOJI[old]} → {STATUS_EMOJI[new]}",
                "source": s.get("source") or repo_web or "",
            })
    for e in events:
        check_event(e)

    out_signals = []
    for s in sc["signals"]:
        if s.get("note") and not s.get("note_en"):
            die(f"{s['id']}: note without note_en")
        o = {"id": s["id"], "category": s["category"], "name": s["name"], "name_en": s["name_en"],
             "value": None if s.get("license_restricted") else s.get("value"),
             "unit": s.get("unit"), "as_of": s.get("as_of"), "status": s["status"],
             "points": s["points"], "max_points": s["max_points"],
             "preliminary": bool(s.get("preliminary")), "source": s.get("source")}
        for k in ("note", "note_en", "expires", "conflict_of_interest", "unconfirmed"):
            if s.get(k) not in (None, ""):
                o[k] = s[k]
        out_signals.append(o)

    report = build_report(sc, out_signals)
    latest = {
        "schema_version": SCHEMA_VERSION, "date": d, "report_type": sc["report_type"],
        "score": sc["score"], "band": sc["band"], "band_en": sc["band_en"],
        "change_vs_previous": change, "headline": headline, "headline_en": headline_en,
        "summary": report["summary"], "summary_en": report["summary_en"],
        "report_file": f"history/{daily_filename(d)}",
        "triggers": [t["name"] for t in sc.get("triggers", [])],
        "triggers_en": [t.get("name_en") or t["name"] for t in sc.get("triggers", [])],
        "heavy_credit_event": sc["heavy_credit_event"],
        "skipped_signals": sc["skipped_signals"],
        "adjustments": sc.get("adjustments", []),
        "signals": out_signals,
        "calendar": sc.get("calendar", []),
        "disclaimer": DISCLAIMER, "disclaimer_en": DISCLAIMER_EN,
    }
    dump(latest_p, latest)

    entry = {"kind": sc["report_type"], "score": sc["score"], "band": sc["band"],
             "band_en": sc["band_en"],
             "categories": {c: round(v, 1) for c, v in sc["categories"].items()},
             "headline": headline, "headline_en": headline_en}
    p, added = write_daily(repo, d, entry, events, report)
    upsert_index(repo, d, sc["report_type"], sc["score"], sc["band"])
    print(f"Wrote data/latest.json, {os.path.relpath(p, repo)} (+{added} events), index.json")
    print(f"change_vs_previous: {change}")


def cmd_seed(a):
    entries = load(a.entries)
    ensure_static(a.repo)
    n = 0
    for e in sorted(entries, key=lambda x: x["date"]):
        p = os.path.join(a.repo, "data", "history", daily_filename(e["date"]))
        if os.path.exists(p):
            print(f"Skipping {e['date']} – file exists.")
            continue
        if not e.get("headline") or not e.get("headline_en"):
            die(f"seed entry {e['date']} needs headline and headline_en")
        band, band_en = band_for(e["score"])
        entry = {"kind": e.get("kind", "full"), "score": e["score"], "band": band, "band_en": band_en,
                 "categories": e.get("categories", {}), "headline": e["headline"],
                 "headline_en": e["headline_en"]}
        write_daily(a.repo, e["date"], entry, e.get("events", []))
        upsert_index(a.repo, e["date"], entry["kind"], e["score"], band)
        n += 1
    print(f"Seeded {n} daily files.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report"); r.add_argument("--scored", required=True); r.add_argument("--repo", required=True)
    s = sub.add_parser("seed"); s.add_argument("--entries", required=True); s.add_argument("--repo", required=True)
    a = ap.parse_args()
    cmd_report(a) if a.cmd == "report" else cmd_seed(a)


if __name__ == "__main__":
    main()
