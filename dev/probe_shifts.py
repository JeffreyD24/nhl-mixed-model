import urllib.request, re, html
b = urllib.request.urlopen(urllib.request.Request("https://www.nhl.com/scores/htmlreports/20262027/TH020180.HTM", headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8", "ignore")
i = b.find("playerHeading")
print(b[i - 300:i + 3500])
cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", b, re.S)]
print("CELLS", len(cells)); print(cells[40:160])
