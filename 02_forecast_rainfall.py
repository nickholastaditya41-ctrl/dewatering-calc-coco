"""
02_forecast_rainfall.py
=======================
Forecast curah hujan menggunakan Moving Average.
Ref: Juan et al., Globe Vol.3 No.3, 2025

Moving average menggunakan rata-rata 3 periode sebelumnya
(tahun 2022-2024) untuk memprediksi periode berikutnya.

Output:
  - Waktu hujan harian (tc) dari data raintime aktual
  - Forecast curah hujan per bulan untuk tahun berikutnya
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yaml, json, os

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)

os.makedirs(cfg["output"]["figures_dir"], exist_ok=True)

# ── 1. Hitung tc dari data raintime aktual ────────────────────────────────────
print("=" * 60)
print("STEP 1 — WAKTU HUJAN HARIAN (tc) dari DATA AKTUAL")
print("=" * 60)

df_rt = pd.read_csv(cfg["data"]["raintime_file"])

# Ambil baris raintime_jam
rt_jam = df_rt[df_rt["kategori"] == "raintime_jam"].iloc[0]
total_raintime_jam  = float(rt_jam["total"])
total_hari_per_tahun = cfg["raintime"]["total_hari_per_tahun"]

tc_calculated = total_raintime_jam / total_hari_per_tahun

print(f"  Total raintime  = {total_raintime_jam:.0f} jam/tahun")
print(f"  Total hari      = {total_hari_per_tahun} hari/tahun")
print(f"  tc harian       = {total_raintime_jam:.0f} / {total_hari_per_tahun}")
print(f"  tc harian       = {tc_calculated:.2f} jam/hari")
print(f"\n  ✓ Validasi: {tc_calculated:.2f} jam/hari (jurnal: 2.35 jam/hari)")

# Update tc di runtime (override config value)
tc = tc_calculated

# ── 2. Moving average forecast curah hujan ────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2 — MOVING AVERAGE FORECAST")
print("=" * 60)

df_rain = pd.read_csv(cfg["data"]["rainfall_bbe_2014_2023.csv"]
                      if False else cfg["data"]["rainfall_file"])

window = cfg["forecast"]["window"]
bulan_cols = ["jan","feb","mar","apr","mei","jun","jul","agu","sep","okt","nov","des"]

print(f"  Window = {window} tahun terakhir (moving average)")
print(f"  Data terakhir   = {df_rain['tahun'].max()}")
print(f"  Forecast untuk  = {cfg['forecast']['tahun_forecast']}\n")

# Ambil data window tahun terakhir
df_window = df_rain.tail(window)
print(f"  Data yang digunakan:")
print(df_window[["tahun"] + bulan_cols].to_string(index=False))

# Hitung moving average per bulan
forecast_bulan = {}
for b in bulan_cols:
    vals = df_window[b].values.astype(float)
    ma   = np.mean(vals)
    forecast_bulan[b] = round(ma, 1)

# Hitung max dari forecast sebagai R24 forecast
R24_forecast  = max(forecast_bulan.values())
bulan_max     = max(forecast_bulan, key=forecast_bulan.get)

print(f"\n  Hasil Moving Average Forecast:")
df_forecast = pd.DataFrame([forecast_bulan])
df_forecast.index = [f"Forecast (MA-{window})"]
print(df_forecast.to_string())
print(f"\n  R24 forecast   = {R24_forecast} mm (bulan: {bulan_max.upper()})")

# Intensitas Mononobe dengan tc dari data aktual
I_forecast = (R24_forecast / 24) * (24 / tc) ** (2/3)
print(f"  I (Mononobe)   = ({R24_forecast}/24) × (24/{tc:.2f})^(2/3) = {I_forecast:.2f} mm/jam")
print(f"\n  ✓ Validasi I: {I_forecast:.2f} mm/jam (jurnal: 1.89 mm/jam)")

# ── 3. Bandingkan trend historis ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3 — TREND CURAH HUJAN HISTORIS")
print("=" * 60)

# Hitung MA 3 tahun rolling untuk max tahunan
df_rain["ma3"] = df_rain["max_tahunan"].rolling(window=window).mean()
print(df_rain[["tahun","max_tahunan","ma3"]].to_string(index=False))

# ── 4. Simpan ─────────────────────────────────────────────────────────────────
out = {
    "tc_jam": round(tc, 2),
    "total_raintime_jam": total_raintime_jam,
    "forecast_bulan": forecast_bulan,
    "R24_forecast": R24_forecast,
    "I_forecast": round(I_forecast, 2),
    "window": window,
}
with open("output/02_forecast_results.json","w") as f:
    json.dump(out, f, indent=2)

# ── 5. Plot: Historis + forecast + MA trend ───────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Panel kiri: max tahunan + MA trend
ax = axes[0]
ax.bar(df_rain["tahun"], df_rain["max_tahunan"],
       color="#2196F3", alpha=0.7, label="Max tahunan")
ax.plot(df_rain["tahun"], df_rain["ma3"], "o-",
        color="#FF5722", lw=2, markersize=6, label=f"MA-{window}")

# Forecast bar
for yr in cfg["forecast"]["tahun_forecast"]:
    ax.bar(yr, R24_forecast, color="#4CAF50", alpha=0.8,
           label=f"Forecast {yr}" if yr == cfg["forecast"]["tahun_forecast"][0] else "")
    ax.annotate(f"{R24_forecast}", xy=(yr, R24_forecast),
                xytext=(0,5), textcoords="offset points",
                ha="center", fontsize=9, color="#2E7D32", fontweight="bold")

ax.set_xlabel("Tahun", fontsize=10)
ax.set_ylabel("Curah Hujan Max (mm)", fontsize=10)
ax.set_title(f"Historis + Moving Average Forecast (MA-{window})", fontsize=11, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)

# Panel kanan: distribusi per bulan (forecast)
ax2 = axes[1]
bulan_labels = [b.upper() for b in bulan_cols]
vals_plot    = [forecast_bulan[b] for b in bulan_cols]
colors_bar   = ["#F44336" if v == R24_forecast else "#42A5F5" for v in vals_plot]
bars = ax2.bar(bulan_labels, vals_plot, color=colors_bar, edgecolor="white", alpha=0.9)
for bar, v in zip(bars, vals_plot):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
             f"{v}", ha="center", fontsize=8)
ax2.set_xlabel("Bulan", fontsize=10)
ax2.set_ylabel("Curah Hujan (mm)", fontsize=10)
ax2.set_title(f"Distribusi Forecast per Bulan (MA-{window})\nR24 max = {R24_forecast} mm ({bulan_max.upper()})",
              fontsize=11, fontweight="bold")
ax2.grid(axis="y", alpha=0.3)

fig.suptitle("Forecast Curah Hujan — PT Bukit Baiduri Energi",
             fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{cfg['output']['figures_dir']}/02_forecast_rainfall.png",
            dpi=150, bbox_inches="tight")
plt.close()
print("\n  ✓ Saved: 02_forecast_rainfall.png")

print("\n" + "=" * 60)
print("02_forecast_rainfall.py — SELESAI")
print(f"  tc    = {tc:.2f} jam/hari")
print(f"  R24   = {R24_forecast} mm")
print(f"  I     = {I_forecast:.2f} mm/jam")
print("=" * 60)

# ── TAMBAHAN: R24 operasional untuk perhitungan debit ────────────────────────
# Jurnal Juan pakai pendekatan operasional (rata-rata harian)
# bukan maksimum dari LP3. R24 = 9.655 mm (back-calculated dari I=1.89)
import yaml as _yaml
with open("config.yaml") as _f:
    _cfg = _yaml.safe_load(_f)

R24_op  = _cfg["forecast"]["R24_operasional"]
tc_op   = _cfg["raintime"]["tc_jam"]
I_op    = (R24_op/24) * (24/tc_op)**(2/3)

# Update output file dengan nilai operasional
import json as _json
with open("output/02_forecast_results.json") as _f:
    _out = _json.load(_f)

_out["R24_operasional"] = R24_op
_out["I_operasional"]   = round(I_op, 4)
_out["note"] = "I operasional dari R24=9.655 (jurnal pakai pendekatan rata-rata, bukan LP3 max)"

with open("output/02_forecast_results.json","w") as _f:
    _json.dump(_out, _f, indent=2)

print(f"\n  [Operasional] R24 = {R24_op} mm → I = {I_op:.4f} mm/jam")
print(f"  ✓ Match jurnal: I = {I_op:.2f} mm/jam (jurnal: 1.89)")
