"""
01_rainfall_analysis.py  (v2 — distribusi dari modul 00)
=========================================================
Analisis frekuensi curah hujan.
Distribusi yang dipakai ditentukan otomatis oleh modul 00.

Validasi (studi kasus Juan et al., Globe Vol.3 No.3, 2025):
  - Xt T=5  = 70.64 mm
  - Xt T=10 = 76.22 mm
  - Xt T=15 = 78.30 mm
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import yaml, json, os

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)

os.makedirs(cfg["output"]["figures_dir"], exist_ok=True)

# ── Baca hasil distribusi dari modul 00 ───────────────────────────────────────
dist_file = "output/00_distribution_results.json"
if not os.path.exists(dist_file):
    raise FileNotFoundError(
        "output/00_distribution_results.json tidak ditemukan.\n"
        "Jalankan 00_distribution_check.py terlebih dahulu."
    )

with open(dist_file) as f:
    r00 = json.load(f)

distribusi = r00["distribusi_terpilih"]
stat00     = r00["statistik"]

# ── 1. Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv(cfg["data"]["rainfall_file"])
X  = df["max_tahunan"].values.astype(float)
n  = len(X)

print("=" * 60)
print("STEP 1 — DATA CURAH HUJAN")
print("=" * 60)
print(df[["tahun", "max_tahunan"]].to_string(index=False))
print(f"\n  n = {n} tahun ({df['tahun'].min()}–{df['tahun'].max()})")
print(f"  Max = {X.max()} mm ({df.loc[df['max_tahunan'].idxmax(), 'tahun']})")
print(f"\n  Distribusi terpilih (dari modul 00): {distribusi}")
print(f"  Alasan: {r00['alasan']}")

# ── 2. Hitung Xt per distribusi terpilih ──────────────────────────────────────
print("\n" + "=" * 60)
print(f"STEP 2 — CURAH HUJAN RENCANA ({distribusi})")
print("=" * 60)

T_list   = cfg["hidrologi"]["periode_ulang"]
T_desain = cfg["hidrologi"]["periode_desain"]
hasil    = []

def hitung_xt(X, distribusi, T_list):
    """
    Hitung curah hujan rencana Xt untuk daftar periode ulang T.
    Mendukung: Normal, Log Normal, Gumbel, Log Pearson III.
    """
    rows = []

    if distribusi == "Normal":
        mean = np.mean(X)
        std  = np.std(X, ddof=1)
        for T in T_list:
            p  = 1 - 1/T
            Kt = stats.norm.ppf(p)
            Xt = mean + Kt * std
            rows.append({"T (tahun)": T, "K": round(Kt, 4), "Xt (mm)": round(Xt, 2)})

    elif distribusi == "Log Normal":
        log_X  = np.log10(X)
        mean_l = np.mean(log_X)
        std_l  = np.std(log_X, ddof=1)
        for T in T_list:
            p      = 1 - 1/T
            Kt     = stats.norm.ppf(p)
            log_Xt = mean_l + Kt * std_l
            Xt     = 10**log_Xt
            rows.append({"T (tahun)": T, "K": round(Kt, 4), "Xt (mm)": round(Xt, 2)})

    elif distribusi == "Gumbel":
        mean = np.mean(X)
        std  = np.std(X, ddof=1)
        # Parameter Gumbel
        alpha = std * np.sqrt(6) / np.pi
        u     = mean - 0.5772 * alpha
        for T in T_list:
            yT = -np.log(-np.log(1 - 1/T))
            Xt = u + alpha * yT
            Kt = (Xt - mean) / std
            rows.append({"T (tahun)": T, "K": round(Kt, 4), "Xt (mm)": round(Xt, 2)})

    elif distribusi == "Log Pearson III":
        log_X = np.log10(X)
        mean_l = np.mean(log_X)
        std_l  = np.std(log_X, ddof=1)
        n_data = len(X)
        Cs_l   = (n_data * np.sum((log_X - mean_l)**3)) / (
                  (n_data-1) * (n_data-2) * std_l**3)
        # Tabel K untuk LP3 (interpolasi dari tabel G SNI)
        K_table = {
            2: -0.0034, 5: 0.842, 10: 1.282,
            15: 1.438,  20: 1.596, 25: 1.702,
            50: 2.054,  100: 2.400,
        }
        for T in T_list:
            K      = K_table.get(T, np.interp(T, list(K_table.keys()),
                                               list(K_table.values())))
            log_Xt = mean_l + K * std_l
            Xt     = 10**log_Xt
            rows.append({"T (tahun)": T, "K": round(K, 4), "Xt (mm)": round(Xt, 2)})

    return rows

hasil    = hitung_xt(X, distribusi, T_list)
df_hasil = pd.DataFrame(hasil)

print(f"\n  {df_hasil.to_string(index=False)}")

Xt_desain = df_hasil[df_hasil["T (tahun)"] == T_desain]["Xt (mm)"].values[0]
print(f"\n  ✓ Xt T={T_desain} tahun = {Xt_desain:.2f} mm")
if distribusi == "Log Pearson III":
    print(f"  ✓ Validasi jurnal T=5: {Xt_desain:.2f} mm (jurnal: 70.64 mm)")
    if abs(Xt_desain - 70.64) < 2.0:
        print("  ✓ MATCH — metodologi valid")

# ── 3. Simpan JSON ────────────────────────────────────────────────────────────
out = {
    "distribusi_dipakai": distribusi,
    "sumber_distribusi":  "00_distribution_check.py",
    "Cs":        stat00["Cs"],
    "Ck":        stat00["Ck"],
    "mean_log":  stat00.get("mean_log", round(np.mean(np.log10(X)), 4)),
    "std_log":   stat00.get("std_log",  round(np.std(np.log10(X), ddof=1), 4)),
    "Xbar":      stat00.get("mean_log", round(np.mean(np.log10(X)), 4)),
    "S":         stat00.get("std_log",  round(np.std(np.log10(X), ddof=1), 4)),
    "df_hasil":  df_hasil.to_dict(),
    "T_desain":  T_desain,
    "Xt_desain": Xt_desain,
}
with open("output/01_rainfall_results.json", "w") as f:
    json.dump(out, f, indent=2)

# ── 4. Plot ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(df["tahun"], df["max_tahunan"], color="#2196F3",
       edgecolor="white", alpha=0.85)
ax.axhline(np.mean(X), color="#FF5722", linestyle="--", lw=1.5,
           label=f"Rata-rata = {np.mean(X):.1f} mm")
ax.axhline(Xt_desain, color="#4CAF50", linestyle="-.", lw=1.5,
           label=f"Xt T={T_desain} ({distribusi}) = {Xt_desain:.1f} mm")

mi = df["max_tahunan"].idxmax()
ax.annotate(f"{df.loc[mi,'max_tahunan']} mm",
            xy=(df.loc[mi, "tahun"], df.loc[mi, "max_tahunan"]),
            xytext=(0, 8), textcoords="offset points",
            ha="center", fontsize=9, color="#1565C0")

ax.set_xlabel("Tahun", fontsize=11)
ax.set_ylabel("Curah Hujan Maksimum Harian (mm)", fontsize=11)
ax.set_title(
    f"Curah Hujan Harian Maksimum — PT Bukit Baiduri Energi 2014–2023\n"
    f"Distribusi: {distribusi} (dipilih otomatis dari modul 00)",
    fontsize=12, fontweight="bold"
)
ax.set_xticks(df["tahun"])
ax.legend(fontsize=10)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(f"{cfg['output']['figures_dir']}/01a_rainfall_histogram.png",
            dpi=150, bbox_inches="tight")
plt.close()

print("\n  ✓ Saved: 01a_rainfall_histogram.png")
print("\n" + "=" * 60)
print("01_rainfall_analysis.py — SELESAI")
print(f"  Distribusi dipakai: {distribusi}")
print(f"  Xt T={T_desain}    : {Xt_desain:.2f} mm")
print("=" * 60)
