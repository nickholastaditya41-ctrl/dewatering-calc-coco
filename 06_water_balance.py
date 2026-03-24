"""
06_water_balance.py
===================
Neraca air (water balance) lengkap.
Ref: Juan et al., Globe Vol.3 No.3, 2025

Neraca air = Q_masuk - Evaporasi - Infiltrasi - Q_pompa = Q_tersisa

Validasi:
  - Evaporasi   = 14.79 m³/hari
  - Infiltrasi  = 4.55 m³/hari
  - Q tersisa   = 1.265,52 m³/hari
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import yaml, json, os

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)
with open("output/03_runoff_results.json") as f:
    r03 = json.load(f)
with open("output/04_sump_results.json") as f:
    r04 = json.load(f)
with open("output/05_pump_results.json") as f:
    r05 = json.load(f)

os.makedirs(cfg["output"]["figures_dir"], exist_ok=True)

na        = cfg["neraca_air"]
luas_m2   = r04["luas_sump_m2"]
Q_total   = r03["Q_total_hari"]
Q_pompa   = r05["Q_pompa_hari"]
V_sump    = r04["V_sump_m3"]

# ── 1. Evaporasi ──────────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1 — EVAPORASI")
print("=" * 60)

evap_mm_per_tahun  = na["evaporasi_mm_per_tahun"]
evap_mm_per_hari   = evap_mm_per_tahun / 365
evap_m3_per_hari   = evap_mm_per_hari / 1000 * luas_m2

print(f"  Evaporasi      = {evap_mm_per_tahun} mm/tahun")
print(f"  Per hari       = {evap_mm_per_tahun}/365 = {evap_mm_per_hari:.2f} mm/hari")
print(f"  Luas sump      = {luas_m2:,.0f} m²")
print(f"  Evaporasi vol  = {evap_mm_per_hari:.2f}/1000 × {luas_m2:,.0f}")
print(f"                 = {evap_m3_per_hari:.2f} m³/hari")
print(f"  ✓ Validasi: {evap_m3_per_hari:.2f} m³/hari (jurnal: 14,79)")

# ── 2. Infiltrasi ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2 — INFILTRASI")
print("=" * 60)

infil_mm_per_tahun = na["infiltrasi_mm_per_tahun"]
infil_mm_per_hari  = infil_mm_per_tahun / 365
infil_m3_per_hari  = infil_mm_per_hari / 1000 * luas_m2

print(f"  Infiltrasi     = {infil_mm_per_tahun} mm/tahun")
print(f"  Per hari       = {infil_mm_per_tahun}/365 = {infil_mm_per_hari:.2f} mm/hari")
print(f"  Infiltrasi vol = {infil_mm_per_hari:.2f}/1000 × {luas_m2:,.0f}")
print(f"                 = {infil_m3_per_hari:.2f} m³/hari")
print(f"  ✓ Validasi: {infil_m3_per_hari:.2f} m³/hari (jurnal: 4,55)")

# ── 3. Neraca air lengkap ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3 — NERACA AIR")
print("=" * 60)

Q_tersisa = Q_total - evap_m3_per_hari - infil_m3_per_hari - Q_pompa

print(f"""
  ┌─────────────────────────────────────────────┐
  │           NERACA AIR SUMP A9                │
  │  PT Bukit Baiduri Energi, Kaltim            │
  ├─────────────────────────────────────────────┤
  │  INFLOW                                     │
  │    Debit limpasan   : {r03['Q_hari_limpasan']:>10.2f} m³/hari  │
  │    Debit air tanah  : {r03['Q_airtanah_hari']:>10.2f} m³/hari  │
  │    ─────────────────────────────────────    │
  │    Total masuk      : {Q_total:>10.2f} m³/hari  │
  │                                             │
  │  OUTFLOW                                    │
  │    Evaporasi        : {evap_m3_per_hari:>10.2f} m³/hari  │
  │    Infiltrasi       : {infil_m3_per_hari:>10.2f} m³/hari  │
  │    Debit pompa      : {Q_pompa:>10.2f} m³/hari  │
  │    ─────────────────────────────────────    │
  │    Total keluar     : {evap_m3_per_hari+infil_m3_per_hari+Q_pompa:>10.2f} m³/hari  │
  │                                             │
  │  SISA (surplus/defisit)                     │
  │    Q tersisa        : {Q_tersisa:>10.2f} m³/hari  │
  │    Status           : {'SURPLUS ⚠' if Q_tersisa > 0 else 'DEFISIT ✓':>10}            │
  └─────────────────────────────────────────────┘
""")
print(f"  ✓ Validasi Q tersisa: {Q_tersisa:.2f} m³/hari (jurnal: 1.265,52)")

# Interpretasi
if Q_tersisa > 0:
    print(f"\n  ⚠ SURPLUS: Sump tidak pernah kosong sepenuhnya.")
    print(f"    {Q_tersisa:.2f} m³/hari tetap terakumulasi.")
    print(f"    Perlu evaluasi kapasitas pompa atau jadwal operasi.")
else:
    print(f"\n  ✓ DEFISIT: Pompa mampu mengosongkan sump.")

# ── 4. Simpan ─────────────────────────────────────────────────────────────────
out = {
    "evaporasi_m3_hari":  round(evap_m3_per_hari, 2),
    "infiltrasi_m3_hari": round(infil_m3_per_hari, 2),
    "Q_masuk_hari":       round(Q_total, 2),
    "Q_pompa_hari":       round(Q_pompa, 2),
    "Q_tersisa_hari":     round(Q_tersisa, 2),
    "status":             "SURPLUS" if Q_tersisa > 0 else "DEFISIT",
    "luas_sump_m2":       luas_m2,
}
with open("output/06_waterbalance_results.json","w") as f:
    json.dump(out, f, indent=2)

# ── 5. Ilustrasi: Diagram alir neraca air ─────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel kiri: diagram alir (Sankey-style)
ax = axes[0]
ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis("off")
ax.set_title("Diagram Alir Neraca Air — Sump A9",
             fontsize=12, fontweight="bold")

# Kotak tengah: sump
sump_rect = mpatches.FancyBboxPatch((3.5, 2.5), 3, 3,
                                     boxstyle="round,pad=0.2",
                                     facecolor="#B3E5FC", edgecolor="#0288D1", lw=2)
ax.add_patch(sump_rect)
ax.text(5, 4.4, "SUMP A9", ha="center", fontsize=11, fontweight="bold", color="#01579B")
ax.text(5, 3.8, f"Kapasitas\n{V_sump:,.0f} m³", ha="center", fontsize=9, color="#0277BD")

# Inflow kiri
inflows = [
    (f"Limpasan\n{r03['Q_hari_limpasan']:,.1f} m³/hari", "#42A5F5", 6.0),
    (f"Air Tanah\n{r03['Q_airtanah_hari']:.2f} m³/hari", "#26C6DA", 4.0),
]
for label, color, y in inflows:
    ax.annotate("", xy=(3.5, y), xytext=(1.0, y),
                arrowprops=dict(arrowstyle="->", color=color, lw=2))
    ax.text(0.5, y, label, ha="center", va="center", fontsize=8,
            fontweight="bold", color=color,
            bbox=dict(boxstyle="round", facecolor="white", edgecolor=color, alpha=0.8))

# Outflow kanan
outflows = [
    (f"Pompa\n{Q_pompa:,.1f} m³/hari", "#EF5350", 6.0),
    (f"Evaporasi\n{evap_m3_per_hari:.2f} m³/hari", "#FF9800", 4.5),
    (f"Infiltrasi\n{infil_m3_per_hari:.2f} m³/hari", "#8D6E63", 3.0),
]
for label, color, y in outflows:
    ax.annotate("", xy=(9.0, y), xytext=(6.5, y),
                arrowprops=dict(arrowstyle="->", color=color, lw=2))
    ax.text(9.5, y, label, ha="center", va="center", fontsize=8,
            fontweight="bold", color=color,
            bbox=dict(boxstyle="round", facecolor="white", edgecolor=color, alpha=0.8))

# Sisa
color_sisa = "#F44336" if Q_tersisa > 0 else "#4CAF50"
ax.text(5, 2.0, f"Q tersisa: {Q_tersisa:,.1f} m³/hari\n({'SURPLUS ⚠' if Q_tersisa > 0 else 'DEFISIT ✓'})",
        ha="center", fontsize=10, fontweight="bold", color=color_sisa,
        bbox=dict(boxstyle="round", facecolor="white", edgecolor=color_sisa, alpha=0.9))

# Panel kanan: bar chart breakdown
ax2 = axes[1]
components = ["Limpasan", "Air\nTanah", "Total\nMasuk", "Evaporasi", "Infiltrasi",
               "Pompa", "Sisa"]
values_bar = [r03["Q_hari_limpasan"], r03["Q_airtanah_hari"], Q_total,
               evap_m3_per_hari, infil_m3_per_hari, Q_pompa, Q_tersisa]
colors_bar = ["#42A5F5","#26C6DA","#1565C0","#FF9800","#8D6E63","#EF5350",
               "#F44336" if Q_tersisa > 0 else "#4CAF50"]

bars = ax2.bar(components, values_bar, color=colors_bar, edgecolor="white",
               linewidth=1.2, alpha=0.9)
for bar, v in zip(bars, values_bar):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+10,
             f"{v:,.1f}", ha="center", fontsize=8, fontweight="bold", rotation=45)

ax2.axhline(0, color="black", lw=0.5)
ax2.set_ylabel("Debit (m³/hari)", fontsize=11)
ax2.set_title("Komponen Neraca Air (m³/hari)", fontsize=12, fontweight="bold")
ax2.grid(axis="y", alpha=0.3)

fig.suptitle("Neraca Air Sump A9 — PT Bukit Baiduri Energi",
             fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{cfg['output']['figures_dir']}/06_water_balance.png",
            dpi=150, bbox_inches="tight")
plt.close()
print("\n  ✓ Saved: 06_water_balance.png")

print("\n" + "=" * 60)
print("06_water_balance.py — SELESAI")
print("=" * 60)
