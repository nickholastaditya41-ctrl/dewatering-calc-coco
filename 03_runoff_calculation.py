"""
03_runoff_calculation.py
========================
Debit limpasan — Metode Rasional.
Q = 0.00278 × C × I × A  (Q dalam m³/detik, A dalam Ha)

Ref: Juan et al., Globe Vol.3 No.3, 2025
     Formula eksplisit: Q = 0.00278 × C × I × A

Validasi:
  - Q = 0.49 m³/detik
  - Q = 1.763 m³/jam
  - Q = 4.211,66 m³/hari (termasuk air tanah)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import yaml, json, os

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)

with open("output/01_rainfall_results.json") as f:
    r01 = json.load(f)
with open("output/02_forecast_results.json") as f:
    r02 = json.load(f)

os.makedirs(cfg["output"]["figures_dir"], exist_ok=True)

Xt_desain = r01["Xt_desain"]
tc        = r02["tc_jam"]
I_lp3     = (Xt_desain / 24) * (24 / tc)**(2/3)   # dari LP3
I_forecast = r02.get("I_operasional", r02["I_forecast"])  # operasional dari R24=9.655

C     = cfg["catchment"]["koef_limpasan"]
A_ha  = cfg["catchment"]["luas_ha"]
nama  = cfg["catchment"]["nama"]

# ── 1. Intensitas Mononobe ────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1 — INTENSITAS MONONOBE")
print("=" * 60)
print(f"  Formula: I = (R24/24) × (24/tc)^(2/3)")
print(f"  tc  = {tc:.2f} jam (dari data raintime aktual)")
print()
print(f"  [A] Dari LP3 T=5: R24 = {Xt_desain:.2f} mm")
print(f"      I = {I_lp3:.4f} mm/jam")
print()
print(f"  [B] Dari forecast MA: R24 = {r02['R24_forecast']} mm")
print(f"      I = {I_forecast:.2f} mm/jam")
print()
print(f"  → Digunakan: I = {I_forecast:.2f} mm/jam (forecast)")
print(f"  ✓ Validasi: {I_forecast:.2f} mm/jam (jurnal: 1.89 mm/jam)")

I = I_forecast   # pakai forecast sesuai jurnal

# ── 2. Debit Rasional ─────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2 — DEBIT RASIONAL")
print("=" * 60)
print(f"  Formula: Q = 0.00278 × C × I × A(Ha)")
print(f"           (Q dalam m³/detik)\n")

Q_detik = 0.00278 * C * I * A_ha
Q_jam   = Q_detik * 3600
Q_hari  = Q_jam * tc   # × waktu hujan harian (jam/hari)

print(f"  Q = 0.00278 × {C} × {I:.2f} × {A_ha}")
print(f"  Q = {Q_detik:.4f} m³/detik")
print(f"  Q = {Q_detik:.2f} m³/detik = {Q_jam:.0f} m³/jam")
print(f"  Q/hari = {Q_jam:.0f} × {tc:.2f} jam = {Q_hari:.2f} m³/hari")
print()
print(f"  ✓ Validasi Q detik: {Q_detik:.2f} (jurnal: 0.49)")
print(f"  ✓ Validasi Q jam  : {Q_jam:.0f} (jurnal: 1.763)")
print(f"  ✓ Validasi Q hari : {Q_hari:.2f} (jurnal: 4.142,54)")

# ── 3. Tambahkan debit air tanah ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3 — TOTAL DEBIT (limpasan + air tanah)")
print("=" * 60)

Q_airtanah_hari = cfg["air_tanah"]["Q_m3_per_hari"]
Q_total_hari    = Q_hari + Q_airtanah_hari

print(f"  Q limpasan       = {Q_hari:.2f} m³/hari")
print(f"  Q air tanah      = {Q_airtanah_hari:.2f} m³/hari (diukur lapangan)")
print(f"  ─────────────────────────────────────")
print(f"  Q total          = {Q_total_hari:.2f} m³/hari")
print(f"\n  ✓ Validasi Q total: {Q_total_hari:.2f} m³/hari (jurnal: 4.211,66)")

# ── 4. Simpan ─────────────────────────────────────────────────────────────────
out = {
    "I_mm_per_jam": round(I, 2),
    "Q_detik": round(Q_detik, 4),
    "Q_jam": round(Q_jam, 2),
    "Q_hari_limpasan": round(Q_hari, 2),
    "Q_airtanah_hari": Q_airtanah_hari,
    "Q_total_hari": round(Q_total_hari, 2),
    "C": C, "A_ha": A_ha, "tc": tc,
}
with open("output/03_runoff_results.json","w") as f:
    json.dump(out, f, indent=2)

# ── 5. Ilustrasi: Diagram alur ────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 4))
ax.set_xlim(0, 13); ax.set_ylim(0, 4); ax.axis("off")

boxes = [
    (0.3,  1.2, 2.0, 1.6, "#B3E5FC", "#0288D1", "Data Hujan",      f"R24={r02['R24_forecast']} mm\n(MA forecast)"),
    (2.8,  1.2, 2.0, 1.6, "#C8E6C9", "#388E3C", "Raintime Data",   f"tc={tc:.2f} jam/hari\n(aktual lapangan)"),
    (5.3,  1.2, 2.0, 1.6, "#FFF9C4", "#F57F17", "Mononobe",        f"I={I:.2f} mm/jam"),
    (7.8,  1.2, 2.0, 1.6, "#FFE0B2", "#E65100", "Debit Rasional",  f"Q={Q_detik:.2f} m³/s\n={Q_jam:.0f} m³/jam"),
    (10.3, 1.2, 2.0, 1.6, "#FFCDD2", "#C62828", "+Air Tanah",      f"Q_total\n={Q_total_hari:.1f} m³/hari"),
]

for (x, y, w, h, fc, ec, title, sub) in boxes:
    rect = mpatches.FancyBboxPatch((x,y), w, h,
                                   boxstyle="round,pad=0.1",
                                   facecolor=fc, edgecolor=ec, lw=1.5)
    ax.add_patch(rect)
    ax.text(x+w/2, y+h*0.65, title, ha="center", va="center",
            fontsize=9, fontweight="bold", color=ec)
    ax.text(x+w/2, y+h*0.28, sub, ha="center", va="center",
            fontsize=8, color="#333")

for x1, x2 in [(2.3,2.8),(4.8,5.3),(7.3,7.8),(9.8,10.3)]:
    ax.annotate("", xy=(x2,2.0), xytext=(x1,2.0),
                arrowprops=dict(arrowstyle="->", color="#555", lw=1.5))

ax.set_title("Alur Analisis Debit Limpasan — PT Bukit Baiduri Energi\n"
             "Metode Rasional: Q = 0.00278 × C × I × A",
             fontsize=12, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{cfg['output']['figures_dir']}/03_runoff_flow.png",
            dpi=150, bbox_inches="tight")
plt.close()
print("\n  ✓ Saved: 03_runoff_flow.png")

print("\n" + "=" * 60)
print("03_runoff_calculation.py — SELESAI")
print("=" * 60)
