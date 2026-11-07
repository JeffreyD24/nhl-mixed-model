"""
Past NHL player-prop lines from ESPN's public core API (propBets). Free, no key. Found Nov 7, 2026 (NHL player props model session).
ESPN shows its partner book's props per game: ESPN BET (provider 58) from Feb 2024 to Nov 2025 (empty Oct 2023-Jan 2024 and from Dec 2025,
when ESPN BET closed). Each item has the book's OWN opening line + price ("open") and its last line + price ("current" = close for past
games): a true per-book opener, unlike BettingPros' single first-to-post opener. Markets: Total Goals / Points / Assists / Power Play Points /
Blocked Shots / Saves, First/Last Goalscorer, To Score 2+; Total Shots on Goal and Total Hits only from Oct 2025.
  python props_espn_nhl.py WORKDIR [--from 2024-01-01] [--to 2025-12-31] [--providers 58,100] [--max-dates 400]
Game ids: data/box_hist.csv.gz + state/box_2026_27.csv (ESPN event ids). Athlete ids are ESPN ids (= box_hist playerid).
Writes data/props_history/espn_nhl/{date}.csv.gz, one row per game x provider x prop x side; saved dates skipped.
"""
import os, sys, json, time, urllib.request, urllib.error
import pandas as pd

W = os.path.abspath(sys.argv[1])
ARG = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
OUT = os.path.join(W, "data", "props_history", "espn_nhl"); os.makedirs(OUT, exist_ok=True)
BASE = "https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl/events/{e}/competitions/{e}/odds/{p}/propBets?limit=1000"


def get(url):
    for i in range(4):
        try:
            time.sleep(0.4)
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(5 * (i + 1))
        except Exception:
            time.sleep(5 * (i + 1))
    raise RuntimeError("gave up on " + url)


def side_of(d):
    for k in ("over", "under"):
        if k in (d or {}): return k, d[k].get("american"), (d.get("target") or {}).get("value")
    return None, None, None


def rows_for(game, day, prov):
    d = get(BASE.format(e=game, p=prov))
    out = []
    for it in (d or {}).get("items", []):
        ath = (it.get("athlete") or {}).get("$ref", "")
        aid = ath.split("/athletes/")[1].split("?")[0] if "/athletes/" in ath else None
        cs, cp, cl = side_of(it.get("current"))
        os_, op, ol = side_of(it.get("open"))
        o = it.get("odds") or {}
        out.append(dict(date=day, game_id=game, provider=prov, athlete_id=aid, market=(it.get("type") or {}).get("name"),
                        side=cs or os_, line=cl if cl is not None else (o.get("total") or {}).get("value"),
                        price=cp or (o.get("american") or {}).get("value"), open_line=ol, open_price=op or (o.get("american") or {}).get("open"),
                        updated=it.get("lastUpdated")))
    return out


def main():
    B = pd.read_csv(os.path.join(W, "data", "box_hist.csv.gz"), usecols=["game_id", "date"]).drop_duplicates()
    cur = os.path.join(W, "state", "box_2026_27.csv")
    if os.path.exists(cur): B = pd.concat([B, pd.read_csv(cur, usecols=["game_id", "date"]).drop_duplicates()])
    B = B[~B.date.str[5:7].isin(["07", "08", "09"])]
    lo, hi = ARG("--from", "2024-01-01"), ARG("--to", "2025-12-31")
    provs = ARG("--providers", "58,100").split(",")
    todo = [d for d in sorted(B.date.unique()) if lo <= d <= hi and not os.path.exists(os.path.join(OUT, f"{d}.csv.gz"))]
    todo = todo[: int(ARG("--max-dates", "400"))]
    if not todo: print("all dates already saved"); return
    for day in todo:
        R = []
        try:
            for g in B[B.date == day].game_id:
                for p in provs: R += rows_for(int(g), day, p)
        except Exception as e:
            print(f"{day}: failed ({e}); will retry next run", flush=True); continue
        R = pd.DataFrame(R); R.to_csv(os.path.join(OUT, f"{day}.csv.gz"), index=False)
        print(f"{day}: {len(R)} rows" + (f", markets {R.market.nunique()}, providers {sorted(R.provider.unique())}" if len(R) else ""), flush=True)


if __name__ == "__main__":
    main()
