#!/usr/bin/env python3
"""Computes AI Doomsday points from report.json.

Usage:
  python3 score.py --report report.json --out scored.json \
      [--previous <repo>/data/latest.json]

- Signals missing from report.json are carried over from --previous (short report).
- A signal whose reading (as_of) is older than 90 days becomes skipped and its
  points are redistributed proportionally within its category.
- An unconfirmed (single-source) reading pointing to a higher-risk status adds
  UNCONFIRMED_SHARE of the gap between the confirmed and the unconfirmed status,
  for at most UNCONFIRMED_MAX_DAYS days from its as_of.
- status_since: the date a signal's current status began (kept while the status matches
  --previous, otherwise the report date).
- Correlated moves (report.json "correlated_moves", carried from --previous): within a
  CORRELATION_GROUPS group the highest-scoring member counts in full, the others at
  CORRELATED_SHARE of their rise in the move, while each keeps the status it had in it.
- Calibration review: flagged when the score has been >= REVIEW_SCORE for REVIEW_DAYS
  (from data/history/index.json next to --previous), or a signal has been at
  REVIEW_SHARE or more for REVIEW_DAYS.
- Triggers and a heavy credit event raise the category score to its floor
  (the top-up is stored in "adjustments").
Prints the calculation as a Polish Markdown table to paste into the report.
"""
import argparse
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, __import__("os").path.dirname(__file__))
from config import (BUDGETS, SIGNALS, STATUS_SHARE, STATUS_EMOJI, DEFAULT_RESTRICTED,
                    TRIGGER_FLOOR_SHARE, HEAVY_CREDIT_FLOOR_A, STALE_DAYS,
                    UNCONFIRMED_SHARE, UNCONFIRMED_MAX_DAYS,
                    REVIEW_SCORE, REVIEW_DAYS, REVIEW_SHARE,
                    CORRELATION_GROUPS, CORRELATION_GROUP_NAMES, CORRELATED_SHARE,
                    CORRELATED_WINDOW_DAYS,
                    band_for, near_boundary, CATEGORY_NAMES)

CARRY_FIELDS = ("value", "unit", "as_of", "status", "preliminary", "source", "note",
                "note_en", "expires", "conflict_of_interest", "license_restricted",
                "unconfirmed", "status_since", "status_prev")


def parse_date(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--previous")
    a = ap.parse_args()

    rep = json.load(open(a.report, encoding="utf-8"))
    today = parse_date(rep.get("date"))
    if not today:
        sys.exit("ERROR: report.json needs a date field (YYYY-MM-DD).")
    if rep.get("report_type") not in ("full", "short"):
        sys.exit("ERROR: report_type must be 'full' or 'short'.")

    prev, prev_moves = {}, []
    if a.previous:
        try:
            prev_doc = json.load(open(a.previous, encoding="utf-8"))
            for s in prev_doc.get("signals", []):
                prev[s["id"]] = s
            prev_moves = prev_doc.get("correlated_moves", []) or []
        except FileNotFoundError:
            print(f"WARNING: {a.previous} not found – scoring without previous state.", file=sys.stderr)

    given = {s["id"]: s for s in rep.get("signals", [])}
    unknown = set(given) - set(SIGNALS)
    if unknown:
        sys.exit(f"ERROR: unknown signals: {sorted(unknown)}")

    warnings, signals = [], []
    for sid, (name, name_en, base) in SIGNALS.items():
        if sid in given:
            s = dict(given[sid]); s["carried"] = False
            s.pop("correlated", None)
        elif sid in prev:
            s = {k: prev[sid][k] for k in CARRY_FIELDS if k in prev[sid]}
            s["carried"] = True
        else:
            s = {"status": "skipped", "carried": False,
                 "note": "Brak odczytu.", "note_en": "No reading available."}
            if rep["report_type"] == "full":
                warnings.append(f"{sid}: missing from a full report – marked skipped.")
        s.update(id=sid, category=sid[0], name=name, name_en=name_en, base_max=base)
        if s.get("status") not in STATUS_SHARE:
            sys.exit(f"ERROR: {sid} has invalid status {s.get('status')!r}.")
        if "license_restricted" not in s:
            s["license_restricted"] = sid in DEFAULT_RESTRICTED
        s.setdefault("preliminary", False)
        asof = parse_date(s.get("as_of"))
        if s["status"] != "skipped":
            if asof is None:
                warnings.append(f"{sid}: as_of is not a YYYY-MM-DD date – reading age not checked.")
            elif (today - asof).days > STALE_DAYS:
                s["status"] = "skipped"
                s["note"] = f"Ostatni odczyt z {asof} jest starszy niż {STALE_DAYS} dni – sygnał pominięty."
                s["note_en"] = f"Last reading from {asof} is older than {STALE_DAYS} days – signal skipped."
                warnings.append(f"{sid}: reading from {asof} older than {STALE_DAYS} days → skipped.")
        u = s.get("unconfirmed")
        if u:
            uasof = parse_date(u.get("as_of"))
            if s["status"] == "skipped":
                warnings.append(f"{sid}: unconfirmed reading ignored – signal has no confirmed status.")
                s.pop("unconfirmed")
            elif u.get("status") not in STATUS_SHARE or u["status"] == "skipped":
                sys.exit(f"ERROR: {sid} unconfirmed.status invalid: {u.get('status')!r}.")
            elif not u.get("source") or uasof is None:
                sys.exit(f"ERROR: {sid} unconfirmed reading needs source and as_of (YYYY-MM-DD).")
            elif (today - uasof).days > UNCONFIRMED_MAX_DAYS:
                warnings.append(f"{sid}: unconfirmed reading from {uasof} older than "
                                f"{UNCONFIRMED_MAX_DAYS} days → expired, dropped.")
                s.pop("unconfirmed")
            elif STATUS_SHARE[u["status"]] <= STATUS_SHARE[s["status"]]:
                warnings.append(f"{sid}: unconfirmed status is not higher-risk than confirmed → ignored.")
                s.pop("unconfirmed")
        p = prev.get(sid)
        since = parse_date(p.get("status_since")) if p else None
        if p and p.get("status") == s["status"] and since and since <= today:
            s["status_since"] = since.isoformat()
            s["status_prev"] = p.get("status_prev")
        else:
            s["status_since"] = today.isoformat()
            s["status_prev"] = p.get("status") if p else None
        signals.append(s)

    # Redistribute skipped signals' points within each category.
    cats = {}
    for c, budget in BUDGETS.items():
        members = [s for s in signals if s["category"] == c]
        active = [s for s in members if s["status"] != "skipped"]
        active_base = sum(s["base_max"] for s in active)
        for s in members:
            if s["status"] == "skipped":
                s["max_points"], s["points"] = 0, 0
            else:
                s["max_points"] = round(s["base_max"] * budget / active_base, 2)
                share = STATUS_SHARE[s["status"]]
                if s.get("unconfirmed"):
                    share += UNCONFIRMED_SHARE * (STATUS_SHARE[s["unconfirmed"]["status"]] - share)
                    s["unconfirmed"]["added_points"] = round(
                        (share - STATUS_SHARE[s["status"]]) * s["max_points"], 2)
                s["points"] = round(share * s["max_points"], 2)
        if not active:
            warnings.append(f"Category {c}: all signals skipped – budget {budget} is lost.")
        cats[c] = {"raw": round(sum(s["points"] for s in members), 2), "budget": budget,
                   "redistributed": len(active) < len(members)}

    # Correlated moves: carried ones first, then new or re-declared ones from report.json.
    sig_by = {s["id"]: s for s in signals}
    moves = {m["group"]: m for m in prev_moves if m.get("group") in CORRELATION_GROUPS}
    for m in rep.get("correlated_moves", []) or []:
        g = m.get("group")
        if g not in CORRELATION_GROUPS:
            sys.exit(f"ERROR: correlated_moves: unknown group {g!r}.")
        if not m.get("reason") or not m.get("reason_en"):
            sys.exit(f"ERROR: correlated_moves {g}: reason and reason_en are required.")
        ids = m.get("signals") or []
        if isinstance(ids, dict):
            ids = list(ids)
        bad = [i for i in ids if i not in CORRELATION_GROUPS[g]]
        if bad:
            sys.exit(f"ERROR: correlated_moves {g}: {bad} not in group {CORRELATION_GROUPS[g]}.")
        old = moves.get(g, {})
        ok = {}
        for i in ids:
            s = sig_by[i]
            before = s.get("status_prev") or "green"
            if STATUS_SHARE.get(before) is None:
                before = "green"
            mine = old.get("signals", {}).get(i)
            if s["status"] == "skipped" or not STATUS_SHARE[s["status"]]:
                warnings.append(f"{i}: no raised status – left out of correlated move {g}.")
            elif mine and mine.get("status") == s["status"]:
                ok[i] = mine                 # already in this move with the same status
            elif STATUS_SHARE[s["status"]] <= STATUS_SHARE[before]:
                warnings.append(f"{i}: status did not rise – left out of correlated move {g}.")
            elif (today - parse_date(s["status_since"])).days > CORRELATED_WINDOW_DAYS:
                warnings.append(f"{i}: status held since {s['status_since']} – not part of a move "
                                f"within {CORRELATED_WINDOW_DAYS} days, left out of {g}.")
            else:
                ok[i] = {"status": s["status"], "from": before}
        moves[g] = {"group": g, "signals": ok, "since": old.get("since") or today.isoformat(),
                    "reason": m["reason"], "reason_en": m["reason_en"]}
    correlated_moves = []
    for g, m in moves.items():
        keep = {i: v for i, v in m.get("signals", {}).items()
                if isinstance(v, dict) and i in sig_by and sig_by[i]["status"] == v.get("status")}
        for i in set(m.get("signals", {})) - set(keep):
            warnings.append(f"{i}: status changed – left correlated move {g}.")
        if len(keep) < 2:
            if m.get("signals"):
                warnings.append(f"Correlated move {g} ended (fewer than 2 members left).")
            continue
        order = CORRELATION_GROUPS[g]
        rise = {i: max(0.0, sig_by[i]["points"]
                       - STATUS_SHARE[keep[i]["from"]] * sig_by[i]["max_points"]) for i in keep}
        ranked = sorted(keep, key=lambda i: (-rise[i], order.index(i)))
        total = 0
        sig_by[ranked[0]]["correlated"] = {"group": g, "discount_points": 0}
        for i in ranked[1:]:
            s = sig_by[i]
            cut = round(rise[i] * (1 - CORRELATED_SHARE), 2)
            s["points"] = round(s["points"] - cut, 2)
            s["correlated"] = {"group": g, "discount_points": cut}
            total += cut
        correlated_moves.append(dict(m, signals=keep, discount_points=round(total, 2)))
    for c in cats:
        cats[c]["raw"] = round(sum(s["points"] for s in signals if s["category"] == c), 2)

    # Floors: triggers and heavy credit event.
    floors = {}
    for t in rep.get("triggers", []):
        c = t.get("category")
        if c not in BUDGETS:
            sys.exit(f"ERROR: trigger {t!r} has no valid category.")
        floors.setdefault(c, []).append((TRIGGER_FLOOR_SHARE * BUDGETS[c], f"wyzwalacz: {t['name']}",
                                         f"trigger: {t.get('name_en', t['name'])}"))
    heavy = bool(rep.get("heavy_credit_event"))
    if heavy:
        floors.setdefault("A", []).append((HEAVY_CREDIT_FLOOR_A, "ciężkie zdarzenie kredytowe",
                                           "heavy credit event"))
    adjustments = []
    for c, lst in floors.items():
        floor, reason, reason_en = max(lst, key=lambda x: x[0])
        if cats[c]["raw"] < floor:
            add = round(floor - cats[c]["raw"], 2)
            adjustments.append({"category": c, "points": add, "floor": floor,
                                "reason": reason, "reason_en": reason_en})
    for c in cats:
        cats[c]["final"] = round(cats[c]["raw"] + sum(x["points"] for x in adjustments
                                                      if x["category"] == c), 2)

    score = int(round(sum(v["final"] for v in cats.values())))
    band, band_en = band_for(score)

    # Calibration review.
    high_since = None
    if score >= REVIEW_SCORE:
        high_since = today
        files = []
        if a.previous:
            idx_p = os.path.join(os.path.dirname(a.previous), "history", "index.json")
            try:
                files = json.load(open(idx_p, encoding="utf-8")).get("files", [])
            except (FileNotFoundError, ValueError):
                files = []
        for f in sorted(files, key=lambda f: f.get("date", ""), reverse=True):
            d = parse_date(f.get("date"))
            if d is None or d >= today:
                continue
            if (f.get("score") or 0) < REVIEW_SCORE:
                break
            high_since = d
    long_held = [{"id": s["id"], "status": s["status"], "since": s["status_since"],
                  "days": (today - parse_date(s["status_since"])).days}
                 for s in signals if s["status"] != "skipped"
                 and STATUS_SHARE[s["status"]] >= REVIEW_SHARE
                 and (today - parse_date(s["status_since"])).days >= REVIEW_DAYS]
    high_days = (today - high_since).days if high_since else 0
    review = {"needed": bool(long_held) or high_days >= REVIEW_DAYS,
              "high_score_since": high_since.isoformat() if high_since else None,
              "high_score_days": high_days, "long_held_signals": long_held}

    out = dict(rep)
    out.update(signals=signals, categories={c: v["final"] for c, v in cats.items()},
               category_detail=cats, adjustments=adjustments, score=score, band=band,
               band_en=band_en, near_boundary=near_boundary(score),
               heavy_credit_event=heavy, calibration_review=review,
               correlated_moves=correlated_moves,
               skipped_signals=[s["id"] for s in signals if s["status"] == "skipped"],
               warnings=warnings)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # Calculation table for the (Polish) report.
    print(f"## Wyliczenie – {today}\n")
    print("| Kat. | Sygnały (punkty/maks.) | Korekta | Wynik/budżet |")
    print("|---|---|---|---|")
    for c, v in cats.items():
        parts = ", ".join(
            f"{s['id']} {STATUS_EMOJI[s['status']]}"
            + (f"(→{STATUS_EMOJI[s['unconfirmed']['status']]}?)" if s.get("unconfirmed") else "")
            + f" {s['points']:g}/{s['max_points']:g}"
            + (f" (skorel. −{s['correlated']['discount_points']:g})"
               if s.get("correlated", {}).get("discount_points") else "")
            for s in signals if s["category"] == c)
        adj = sum(x["points"] for x in adjustments if x["category"] == c)
        red = " (redystrybucja)" if v["redistributed"] else ""
        print(f"| {c} {CATEGORY_NAMES[c][0]} | {parts}{red} | {('+' + format(adj, 'g')) if adj else '–'} "
              f"| {v['final']:g}/{v['budget']} |")
    print(f"\n**Wynik: {score}/1000 – {band}**" + (" (na granicy przedziałów)" if out["near_boundary"] else ""))
    top = sorted([s for s in signals if s["points"] > 0], key=lambda s: -s["points"])[:3]
    print("Najwięcej punktów: " + ", ".join(f"{s['id']} ({s['points']:g})" for s in top))
    unc = [s for s in signals if s.get("unconfirmed")]
    if unc:
        print("Niepotwierdzone odczyty (jedno źródło, ważne 14 dni): " + ", ".join(
            f"{s['id']} +{s['unconfirmed']['added_points']:g} (wygasa "
            f"{parse_date(s['unconfirmed']['as_of']) + timedelta(days=UNCONFIRMED_MAX_DAYS)})"
            for s in unc))
    for m in correlated_moves:
        print(f"Skorelowany ruch – {CORRELATION_GROUP_NAMES[m['group']][0]} "
              f"({', '.join(m['signals'])}) od {m['since']}: {m['reason']} "
              f"Rabat −{m['discount_points']:g} pkt.")
    if review["needed"]:
        msg = []
        if high_days >= REVIEW_DAYS:
            msg.append(f"wynik ≥ {REVIEW_SCORE} od {review['high_score_since']} ({high_days} dni)")
        if long_held:
            msg.append("długo na najwyższym statusie: " + ", ".join(
                f"{x['id']} {STATUS_EMOJI[x['status']]} od {x['since']} ({x['days']} dni)"
                for x in long_held))
        print("PRZEGLĄD KALIBRACJI: " + "; ".join(msg))
    for w in warnings:
        print(f"WARNING: {w}")


if __name__ == "__main__":
    main()
