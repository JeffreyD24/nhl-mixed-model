import sys, pandas as pd
sys.argv = ["x", "."]; sys.path.insert(0, ".")
import shifts
r = pd.DataFrame(shifts.toi_report(2026020180, "phi", "fla"))
print("ROWS", len(r)); print(r.head(4).to_string()); print(r.groupby("team").player.nunique().to_dict())
print((r.groupby(["team", "player"]).duration_sec.sum() / 60).describe().round(1).to_dict())
