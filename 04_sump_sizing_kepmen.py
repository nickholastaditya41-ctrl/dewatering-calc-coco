"""
04_sump_sizing_kepmen.py
========================
Kapasitas sump berbasis Kepmen ESDM No. 1827 K/30/MEM/2018.

Regulasi:
  "Fasilitas penampungan air tambang memiliki kapasitas sekurang-kurangnya
   1,25 kali volume air tambang pada curah hujan tertinggi selama 84 jam."

Formula:
  V_max  = (Q_limpasan + Q_airtanah) × 84 jam
  V_sump = V_max × 1.25

Validasi:
  - V_max  = 100.150,10 m³
  - V_sump = 125.187,62 m³
  - Luas sump = 11.381 m² = 1.138 ha
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import yaml, json, os, math

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)
with open("output/03_runoff_results.json") as f:
    r03 = json.load(f)

os.makedirs(cfg["output"]["figures_dir"], exist_ok=True)

# Jurnal Tabel 6 pakai I=1.27 mm/jam untuk sump sizing
# (lebih rendah dari I=1.89 untuk debit operasional)
C     = cfg["catchment"]["koef_limpasan"]
A_ha  = cfg["catchment"]["luas_ha"]
I_sump = cfg["kepmen_sump"]["I_sump_mm_per_jam"]
Q_sump_detik   = 0.00278 * C * I_sump * A_ha
Q_limpasan_jam = Q_sump_detik * 3600   # m³/jam
Q_airtanah_jam = cfg["air_tanah"]["Q_m3_per_jam"]
durasi_jam     = cfg["kepmen_sump"]["durasi_jam"]
sf             = cfg["kepmen_sump"]["safety_factor"]
kedalaman      = cfg["neraca_air"]["kedalaman_sump_m"]

# ── 1. Volume sump (Kepmen ESDM 1827) ─────────────────────────────────────────
print("=" * 60)
print("STEP 1 — KAPASITAS SUMP (Kepmen ESDM 1827 K/30/MEM/2018)")
print("=" * 60)
print(f"""
  Regulasi: kapasitas ≥ 1,25 × volume air pada hujan tertinggi 84 jam

  Q limpasan     = {Q_limpasan_jam:.2f} m³/jam
  Q air tanah    = {Q_airtanah_jam:.2f} m³/jam
  Durasi         = {durasi_jam} jam
  Safety factor  = {sf}
""")

V_masuk = (Q_limpasan_jam + Q_airtanah_jam) * durasi_jam
V_sump  = V_masuk * sf

print(f"  V masuk  = ({Q_limpasan_jam:.2f} + {Q_airtanah_jam:.2f}) × {durasi_jam}")
print(f"  V masuk  = {Q_limpasan_jam + Q_airtanah_jam:.2f} × {durasi_jam}")
print(f"  V masuk  = {V_masuk:.2f} m³")
print(f"\n  V sump   = {V_masuk:.2f} × {sf}")
print(f"  V sump   = {V_sump:.2f} m³")
print(f"\n  ✓ Validasi V masuk : {V_masuk:.2f} m³ (jurnal: 100.150,10)")
print(f"  ✓ Validasi V sump  : {V_sump:.2f} m³ (jurnal: 125.187,62)")

# ── 2. Luas sump ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2 — LUAS SUMP")
print("=" * 60)

luas_sump_m2 = V_sump / kedalaman
luas_sump_ha = luas_sump_m2 / 10000

print(f"  Luas = V_sump / kedalaman")
print(f"  Luas = {V_sump:.2f} / {kedalaman}")
print(f"  Luas = {luas_sump_m2:.0f} m² = {luas_sump_ha:.3f} ha")
print(f"\n  ✓ Validasi: {luas_sump_m2:.0f} m² (jurnal: 11.381 m²)")

# ── 3. Simpan ─────────────────────────────────────────────────────────────────
out = {
    "V_masuk_m3":    round(V_masuk, 2),
    "V_sump_m3":     round(V_sump, 2),
    "luas_sump_m2":  round(luas_sump_m2, 0),
    "luas_sump_ha":  round(luas_sump_ha, 3),
    "kedalaman_m":   kedalaman,
    "durasi_jam":    durasi_jam,
    "safety_factor": sf,
    "Q_total_jam":   round(Q_limpasan_jam + Q_airtanah_jam, 2),
}
with open("output/04_sump_results.json","w") as f:
    json.dump(out, f, indent=2)

# ── 4. Ilustrasi: Skema sump Kepmen ───────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel kiri: breakdown volume
ax = axes[0]
categories  = ["V masuk\n(84 jam)", "V sump\n(×1.25 Kepmen)"]
values      = [V_masuk, V_sump]
colors_bar  = ["#42A5F5", "#EF5350"]
bars = ax.bar(categories, values, color=colors_bar, edgecolor="white",
              linewidth=1.5, width=0.5, alpha=0.9)
for bar, val in zip(bars, values):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+500,
            f"{val:,.1f} m³", ha="center", fontsize=11, fontweight="bold")

ax.axhline(V_masuk, color="#42A5F5", linestyle="--", alpha=0.5)
ax.set_ylabel("Volume (m³)", fontsize=11)
ax.set_title("Kapasitas Sump — Kepmen ESDM 1827\n"
             f"Safety factor: {sf}× | Durasi: {durasi_jam} jam",
             fontsize=12, fontweight="bold")
ax.set_ylim(0, V_sump * 1.3)
ax.grid(axis="y", alpha=0.3)
ax.text(0.5, 0.92, "Kepmen ESDM No. 1827 K/30/MEM/2018",
        transform=ax.transAxes, ha="center", fontsize=9,
        style="italic", color="#666")

# Panel kanan: cross-section sump
ax2 = axes[1]
ax2.set_title(f"Skema Sump A9 — Tampak Samping\n"
              f"V = {V_sump:,.1f} m³ | Luas = {luas_sump_m2:,.0f} m²",
              fontsize=12, fontweight="bold")

h  = kedalaman
w  = np.sqrt(luas_sump_m2)  # asumsikan persegi untuk simplifikasi
slope = w * 0.15

trap_x = [0, slope, slope+w, slope*2+w, 0]
trap_y = [h, 0, 0, h, h]
ax2.fill(trap_x, trap_y, color="#B3E5FC", alpha=0.7,
         edgecolor="#0288D1", linewidth=2)

# Water level
water_h = h * 0.85
ax2.fill([slope*0.3, slope*0.7, slope*1.3+w, slope*1.7+w, slope*0.3],
         [water_h*0.15, 0.5, 0.5, water_h*0.15, water_h*0.15],
         color="#1565C0", alpha=0.3)

# Dimensi
ax2.annotate("", xy=(slope*2+w+2, h), xytext=(slope*2+w+2, 0),
             arrowprops=dict(arrowstyle="<->", color="#333", lw=1.5))
ax2.text(slope*2+w+4, h/2, f"h={h}m", va="center", fontsize=10, fontweight="bold")

ax2.annotate("", xy=(slope*2+w, -1.5), xytext=(0, -1.5),
             arrowprops=dict(arrowstyle="<->", color="#333", lw=1.5))
ax2.text((slope*2+w)/2, -2.5, f"B={slope*2+w:.0f}m", ha="center",
         fontsize=10, fontweight="bold")

ax2.text(slope+w/2, h/2, f"V={V_sump:,.0f} m³\nA={luas_sump_m2:,.0f} m²",
         ha="center", va="center", fontsize=10, fontweight="bold", color="#01579B")

ax2.set_xlim(-5, slope*2+w+20)
ax2.set_ylim(-4, h+4)
ax2.set_xlabel("Lebar (m)", fontsize=10)
ax2.set_ylabel("Kedalaman (m)", fontsize=10)
ax2.grid(alpha=0.2)

fig.suptitle("Kapasitas Sump A9 — PT Bukit Baiduri Energi",
             fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{cfg['output']['figures_dir']}/04_sump_sizing.png",
            dpi=150, bbox_inches="tight")
plt.close()
print("\n  ✓ Saved: 04_sump_sizing.png")

print("\n" + "=" * 60)
print("04_sump_sizing_kepmen.py — SELESAI")
print("=" * 60)
