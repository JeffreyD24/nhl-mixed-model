"""Nov 7, 2026 (NHL props model, RULE 12): how many Wayback Machine snapshots exist of NHL player-prop pages, by year?
Runs on an Actions runner (web.archive.org is blocked by the Claude workspace egress policy). Counts only; writes
research/probes/nhl_props_wayback.txt. A page with many dated snapshots = a possible free archive of past prop lines."""
import json, sys, time, urllib.request, urllib.parse, collections
PAGES = ["rotowire.com/betting/nhl/player-props.php", "www.bettingpros.com/nhl/props/*", "www.scoresandodds.com/nhl/props*",
         "www.covers.com/sport/hockey/nhl/player-props*", "www.oddstrader.com/nhl/player-props*", "www.actionnetwork.com/nhl/props*",
         "sportsbook.draftkings.com/leagues/hockey/nhl*", "sportsbook.fanduel.com/navigation/nhl*", "www.oddsshark.com/nhl/player-props*",
         "www.vegasinsider.com/nhl/odds/player-props*", "www.pickswise.com/nhl/props*", "www.dimers.com/nhl/props*",
         "www.numberfire.com/nhl/*", "www.rotogrinders.com/*nhl*prop*", "www.sportsbookreview.com/betting-odds/nhl-hockey/*",
         "app.prizepicks.com/*", "api.prizepicks.com/projections*", "www.bovada.lv/sports/hockey/nhl*",
         "sports.core.api.espn.com/v2/sports/hockey/leagues/nhl/events/*/propBets*"]
out = []
for p in PAGES:
    q = "http://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(dict(url=p, output="json", fl="timestamp,statuscode", limit=50000))
    try:
        rows = json.loads(urllib.request.urlopen(q, timeout=120).read() or b"[]")[1:]
        by = collections.Counter(r[0][:4] for r in rows if r[1] == "200")
        days = len({r[0][:8] for r in rows if r[1] == "200"})
        out.append(f"{p}: {sum(by.values())} ok snapshots on {days} days; by year {dict(sorted(by.items()))}")
    except Exception as e:
        out.append(f"{p}: failed ({str(e)[:80]})")
    print(out[-1], flush=True); time.sleep(3)
open(sys.argv[1] if len(sys.argv) > 1 else "research/probes/nhl_props_wayback.txt", "w").write("\n".join(out) + "\n")
