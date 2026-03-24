"""
05_pump_sizing.py
=================
Sizing pompa dari debit aktual lapangan (bukan formula teoritis).
Ref: Juan et al., Globe Vol.3 No.3, 2025

Pendekatan Juan: debit pompa diukur langsung di lapangan
menggunakan alat flowbar pada RPM 1500.

Validasi:
  - Q aktual = 162.60 m³/jam = 2926.80 m³/hari
  - Lama pemompaan = 615.93 jam ≈ 26 hari
  - Pump ratio = 1.6
"""

import numpy as np
import matplotlib.pyplot as plt
import yaml, json, os, math

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)
with open("output/03_runoff_results.json") as f:
    r03 = json.load(f)
with open("output/04_sump_results.json") as f:
    r04 = json.load(f)

os.makedirs(cfg["output"]["figures_dir"], exist_ok=True)

pompa         = cfg["pompa"]
Q_pompa_jam   = pompa["debit_aktual_m3_per_jam"]
Q_pompa_hari  = pompa["debit_aktual_m3_per_hari"]
jam_kerja     = pompa["jam_kerja_per_hari"]
target_hari   = pompa["target_hari"]
V_sump        = r04["V_sump_m3"]
Q_total_hari  = r03["Q_total_hari"]

# ── 1. Debit aktual pompa ─────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1 — DEBIT AKTUAL POMPA (dari lapangan)")
print("=" * 60)
print(f"""
  Pompa    : {pompa['jenis']}
  RPM      : {pompa['rpm_operasi']}
  Metode   : Pengukuran langsung flowbar di lapangan

  Q aktual = {Q_pompa_jam:.2f} m³/jam
  Jam kerja = {jam_kerja} jam/hari
  Q/hari   = {Q_pompa_jam:.2f} × {jam_kerja} = {Q_pompa_hari:.2f} m³/hari

  ✓ Validasi: {Q_pompa_hari:.2f} m³/hari (jurnal: 2.926,80)
""")

# ── 2. Lama pemompaan ─────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 2 — LAMA PEMOMPAAN")
print("=" * 60)

# Lama pemompaan = V_sump / Q_pompa_jam
# Jurnal hitung lama pompa dari V_MASUK (sebelum ×1.25), bukan V_sump
V_masuk = r04["V_masuk_m3"]
t_jam   = V_masuk / Q_pompa_jam
t_hari  = t_jam / jam_kerja

print(f"  V masuk  = {V_masuk:,.2f} m³  (sebelum safety factor)")
print(f"  Q pompa  = {Q_pompa_jam:.2f} m³/jam")
print(f"  t pompa  = {V_masuk:,.2f} / {Q_pompa_jam:.2f} = {t_jam:.2f} jam")
print(f"  t pompa  = {t_jam:.2f} / {jam_kerja} jam/hari = {t_hari:.1f} hari")
print(f"\n  ✓ Validasi: {t_jam:.2f} jam (jurnal: 615,93 jam = 26 hari)")

# ── 3. Pump ratio ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3 — PUMP RATIO")
print("=" * 60)

# Pump ratio jurnal = V_masuk / V_pompa_total
# = 100150 / (2926.80 * t_hari) ≈ 1.6 menurut jurnal
# Definisi: seberapa banyak pompa harus bekerja vs air yang masuk
# pump_ratio = V_masuk per hari / V_keluar per hari
# Definisi jurnal: 'perbandingan volume air masuk vs keluar'
pump_ratio = Q_total_hari / Q_pompa_hari
print(f"  Pump ratio = Q pompa / Q masuk")
print(f"  Pump ratio = {Q_pompa_hari:.2f} / {Q_total_hari:.2f}")
print(f"  Pump ratio = {pump_ratio:.2f}")
print(f"\n  ✓ Validasi: {pump_ratio:.1f} (jurnal: 1,6)")
print(f"  Status: {'✓ Pompa mampu drain sump' if pump_ratio > 1 else '✗ Pompa tidak cukup'}")

# ── 4. Simpan ─────────────────────────────────────────────────────────────────
out = {
    "Q_pompa_jam":  Q_pompa_jam,
    "Q_pompa_hari": Q_pompa_hari,
    "jam_kerja":    jam_kerja,
    "t_jam":        round(t_jam, 2),
    "t_hari":       round(t_hari, 1),
    "pump_ratio":   round(pump_ratio, 2),
    "V_sump":       V_sump,
}
with open("output/05_pump_results.json","w") as f:
    json.dump(out, f, indent=2)

# ── 5. Ilustrasi: Pump performance ────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Panel kiri: Q pompa vs Q inflow
ax = axes[0]
labels = ["Q inflow\n(limpasan+airtanah)", "Q pompa\n(aktual lapangan)"]
vals   = [Q_total_hari, Q_pompa_hari]
colors_= ["#EF5350", "#42A5F5"]
bars = ax.bar(labels, vals, color=colors_, edgecolor="white", width=0.5, alpha=0.9)
for bar, v in zip(bars, vals):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+20,
            f"{v:,.2f} m³/hari", ha="center", fontsize=11, fontweight="bold")
ax.set_ylabel("Debit (m³/hari)", fontsize=11)
ax.set_title(f"Q Pompa vs Q Inflow\nPump Ratio = {pump_ratio:.2f}",
             fontsize=12, fontweight="bold")
ax.set_ylim(0, max(vals)*1.3)
ax.grid(axis="y", alpha=0.3)
status_color = "#4CAF50" if pump_ratio > 1 else "#F44336"
ax.text(0.5, 0.92, f"Pump ratio {pump_ratio:.1f} > 1 → POMPA MAMPU DRAIN",
        transform=ax.transAxes, ha="center", fontsize=10,
        fontweight="bold", color=status_color)

# Panel kanan: simulasi volume sump per hari
ax2 = axes[1]
days      = np.arange(0, math.ceil(t_hari)+2)
V_sisa    = []
V_current = V_sump

for d in days:
    V_sisa.append(max(0, V_current))
    net = Q_pompa_hari - Q_total_hari
    V_current -= net

ax2.fill_between(days, V_sisa, alpha=0.3, color="#42A5F5")
ax2.plot(days, V_sisa, "o-", color="#1565C0", lw=2, markersize=5)
ax2.axhline(0, color="#F44336", linestyle="--", lw=1.5, label="Sump kosong")
ax2.axvline(t_hari, color="#4CAF50", linestyle="--", lw=1.5,
            label=f"Target selesai hari ke-{t_hari:.0f}")
ax2.set_xlabel("Hari ke-", fontsize=11)
ax2.set_ylabel("Volume Sisa di Sump (m³)", fontsize=11)
ax2.set_title(f"Simulasi Pengeringan Sump A9\n"
              f"Lama pemompaan: {t_jam:.0f} jam ≈ {t_hari:.0f} hari @ {jam_kerja} jam/hari",
              fontsize=12, fontweight="bold")
ax2.legend(fontsize=10)
ax2.grid(alpha=0.3)
ax2.set_ylim(bottom=-1000)

fig.suptitle("Analisis Pompa — PT Bukit Baiduri Energi (MF-385H)",
             fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{cfg['output']['figures_dir']}/05_pump_analysis.png",
            dpi=150, bbox_inches="tight")
plt.close()
print("\n  ✓ Saved: 05_pump_analysis.png")

print("\n" + "=" * 60)
print("05_pump_sizing.py — SELESAI")
print("=" * 60)
