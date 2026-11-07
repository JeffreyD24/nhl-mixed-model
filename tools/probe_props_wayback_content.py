"""Nov 6, 2026 (NHL props model, RULE 12, laptop run): do archived pre-April-2022 snapshots of the pages that
probe_props_wayback.py found really contain NHL player names with prop lines and prices? For each URL pattern, lists the
distinct archived URLs before 2022-04, opens up to 3 of them (raw id_ capture) and counts prop signals: prop words
(shots on goal / points / saves / anytime goal), American odds like +150/-120, half-point lines like 2.5, and whether
the page is a JS shell. Counts only. Writes research/probes/nhl_props_wayback_content.txt."""
import re, sys, time, urllib.request, urllib.parse, json
PATTERNS = ["www.sportsbookreview.com/betting-odds/nhl-hockey/*", "www.scoresandodds.com/nhl/props*",
            "rotowire.com/betting/nhl/player-props.php", "www.numberfire.com/nhl/*", "www.bovada.lv/sports/hockey/nhl*",
            "sportsbook.fanduel.com/navigation/nhl*", "app.prizepicks.com/*", "api.prizepicks.com/projections*"]
UA = {"User-Agent": "Mozilla/5.0 (research probe)"}
def fetch(u, t=90):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
out = []
for p in PATTERNS:
    q = "http://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(dict(url=p, output="json", fl="timestamp,original",
        filter="statuscode:200", to="20220401", collapse="urlkey", limit=5000))
    try:
        rows = json.loads(fetch(q, 120) or b"[]")[1:]
    except Exception as e:
        out.append(f"{p}: cdx failed ({str(e)[:60]})"); print(out[-1], flush=True); continue
    prop = [r for r in rows if re.search(r"prop|player|shot|goal|point|save|projection", r[1], re.I)]
    pick = (prop or rows)[:: max(1, len(prop or rows) // 3)][:3]
    out.append(f"{p}: {len(rows)} distinct urls before 2022-04 ({len(prop)} with prop-ish words in url)")
    for ts, orig in pick:
        try:
            h = fetch(f"http://web.archive.org/web/{ts}id_/{orig}").decode("utf-8", "replace")
            txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S | re.I)
            txt = re.sub(r"<[^>]+>", " ", txt)
            words = len(re.findall(r"shots on goal|anytime goal|total saves|player points|goalscorer|power play points", txt, re.I))
            odds = len(re.findall(r"(?<![\w.])[+-][1-9]\d{2}(?!\d)", txt)); halves = len(re.findall(r"\b\d\.5\b", txt))
            out.append(f"   {ts} {orig[:90]} bytes={len(h)} text_chars={len(txt.split())} prop_words={words} odds={odds} x.5_lines={halves}")
        except Exception as e:
            out.append(f"   {ts} {orig[:90]} fetch failed ({str(e)[:50]})")
        print(out[-1], flush=True); time.sleep(2)
open(sys.argv[1] if len(sys.argv) > 1 else "research/probes/nhl_props_wayback_content.txt", "w").write("\n".join(out) + "\n")
