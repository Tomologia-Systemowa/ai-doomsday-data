#!/usr/bin/env python3
"""Checks the repo before commit. Exit code 1 = errors (warnings don't fail).

Usage: python3 validate.py --repo <repo> --date YYYY-MM-DD
"""
import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (SIGNALS, BUDGETS, SUMMARY_MAX_WORDS, WEEKLY_WORDS, FRIDAY, daily_filename,
                    STATE_FILE, STATE_SERIES, STATE_NO_LEVEL, DEFAULT_RESTRICTED)

errors, warnings = [], []


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        errors.append(f"Missing file {path}")
    except json.JSONDecodeError as e:
        errors.append(f"{path} is not valid JSON: {e}")
    return None


def need_en(obj, field, where):
    if obj.get(field) and not obj.get(field + "_en"):
        errors.append(f"{where}: {field} without {field}_en")


def words(t):
    return len((t or "").split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--date", required=True)
    a = ap.parse_args()
    repo, d = a.repo, a.date
    hist = os.path.join(repo, "data", "history")

    lt = load(os.path.join(repo, "data", "latest.json"))
    if lt:
        if lt.get("date") != d:
            errors.append(f"latest.json: date {lt.get('date')} ≠ {d}")
        ids = [s["id"] for s in lt.get("signals", [])]
        if sorted(ids) != sorted(SIGNALS):
            errors.append(f"latest.json: incomplete or duplicated signals: {ids}")
        pts = sum(s["points"] for s in lt["signals"]) + sum(x["points"] for x in lt.get("adjustments", []))
        if abs(pts - lt["score"]) > 1:
            errors.append(f"latest.json: points sum {pts:.2f} ≠ score {lt['score']} (±1)")
        mx = sum(s["max_points"] for s in lt["signals"])
        if abs(mx - 1000) > 0.5:
            errors.append(f"latest.json: max_points sum {mx:.2f} ≠ 1000")
        for f in ("headline", "band", "summary", "disclaimer"):
            if not lt.get(f):
                errors.append(f"latest.json: empty {f}")
            need_en(lt, f, "latest.json")
        for s in lt["signals"]:
            need_en(s, "name", f"latest.json {s['id']}")
            need_en(s, "note", f"latest.json {s['id']}")
        for c in lt.get("calendar", []):
            need_en(c, "title", f"latest.json calendar {c.get('date')}")

    day = load(os.path.join(hist, daily_filename(d)))
    if day:
        if day.get("date") != d:
            errors.append(f"{daily_filename(d)}: date field {day.get('date')} ≠ file name")
        e = day.get("entry") or {}
        for f in ("headline", "band"):
            need_en(e, f, "daily entry")
        if lt and e.get("score") != lt.get("score"):
            errors.append(f"daily score {e.get('score')} ≠ latest.json score {lt.get('score')}")
        seen = set()
        for ev in day.get("events", []):
            need_en(ev, "title", f"event {ev.get('title')}")
            k = (ev["date"], ev.get("signal"), ev["title"])
            if k in seen:
                errors.append(f"Duplicate event: {k}")
            seen.add(k)
        r = day.get("report")
        if not r:
            errors.append("daily file has no report block")
        else:
            kind = e.get("kind")
            for f in ("summary", "curve_comment", "weekly_analysis"):
                need_en(r, f, "report")
            if not r.get("summary"):
                errors.append("report: empty summary")
            limit = SUMMARY_MAX_WORDS.get(kind)
            if limit and words(r.get("summary")) > limit:
                warnings.append(f"report: summary has {words(r['summary'])} words (> {limit})")
            if kind == "full":
                if not r.get("curve_comment"):
                    errors.append("full report: empty curve_comment")
                cc = r.get("category_comments") or {}
                for c in BUDGETS:
                    if not (cc.get(c) or {}).get("comment") or not (cc.get(c) or {}).get("comment_en"):
                        errors.append(f"full report: category_comments.{c} incomplete")
            if date.fromisoformat(d).weekday() == FRIDAY:
                if not r.get("weekly_analysis"):
                    errors.append("Friday: weekly_analysis missing")
                else:
                    n = words(r["weekly_analysis"])
                    if not WEEKLY_WORDS[0] <= n <= WEEKLY_WORDS[1]:
                        warnings.append(f"weekly_analysis has {n} words (target {WEEKLY_WORDS[0]}–{WEEKLY_WORDS[1]})")
            if lt and len(r.get("signals", [])) != len(lt.get("signals", [])):
                errors.append("report.signals differs from latest.json signals")

    idx = load(os.path.join(hist, "index.json"))
    if idx:
        files = idx.get("files", [])
        dates = [f["date"] for f in files]
        if dates != sorted(dates) or len(dates) != len(set(dates)):
            errors.append("index.json: dates unsorted or duplicated")
        on_disk = {os.path.basename(p) for p in glob.glob(os.path.join(hist, "history-*.json"))}
        for f in files:
            if f["file"] != daily_filename(f["date"]):
                errors.append(f"index.json: {f['file']} does not match date {f['date']}")
            if f["file"] not in on_disk:
                errors.append(f"index.json: missing file {f['file']}")
                continue
            body = load(os.path.join(hist, f["file"])) or {}
            es = (body.get("entry") or {}).get("score")
            if es != f.get("score"):
                errors.append(f"index.json: score {f.get('score')} ≠ {es} in {f['file']}")
        for name in sorted(on_disk - {f["file"] for f in files}):
            errors.append(f"{name} has no record in index.json")

    sp = os.path.join(repo, STATE_FILE)
    if not os.path.exists(sp):
        warnings.append(f"{STATE_FILE} missing – trend thresholds have no history.")
    else:
        stt = load(sp) or {}
        series = stt.get("series")
        if not isinstance(series, dict):
            errors.append(f"{STATE_FILE}: 'series' must be an object")
            series = {}
        for sid, rows in series.items():
            if sid not in STATE_SERIES:
                errors.append(f"{STATE_FILE}: unknown series {sid}")
                continue
            if sid in DEFAULT_RESTRICTED:
                errors.append(f"{STATE_FILE}: {sid} is licence-restricted and must not be stored")
            if not isinstance(rows, list):
                errors.append(f"{STATE_FILE}: {sid} must be a list")
                continue
            if len(rows) > STATE_SERIES[sid]:
                warnings.append(f"{STATE_FILE}: {sid} keeps {len(rows)} readings, "
                                f"limit {STATE_SERIES[sid]} – drop the oldest")
            for r in rows:
                if not r.get("as_of") or not r.get("source"):
                    errors.append(f"{STATE_FILE}: {sid} reading without as_of or source")
                if sid in STATE_NO_LEVEL and r.get("value") is not None:
                    errors.append(f"{STATE_FILE}: {sid} is licensed – store change_pct and "
                                  f"direction, not value")

    if os.path.exists(os.path.join(repo, ".git")):
        st = subprocess.run(["git", "-C", repo, "status", "--porcelain", "--", "data/history.json"],
                            capture_output=True, text=True).stdout.strip()
        if st:
            errors.append(f"data/history.json was modified: {st}")

    for w in warnings:
        print("WARNING:", w)
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("VALIDATION OK")


if __name__ == "__main__":
    main()
