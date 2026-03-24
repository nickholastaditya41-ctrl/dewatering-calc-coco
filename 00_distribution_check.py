"""
00_distribution_check.py
========================
Uji kesesuaian distribusi frekuensi curah hujan.
Dijalankan SEBELUM modul 01 — hasilnya menentukan distribusi yang dipakai.

Distribusi yang diuji:
  1. Normal
  2. Log Normal
  3. Gumbel (EV1)
  4. Log Pearson III

Uji statistik:
  - Syarat Cs & Ck (tabel SNI 2415:2016)
  - Chi-Square goodness of fit
  - Kolmogorov-Smirnov (Smirnov-Kolmogorov)

Output:
  output/00_distribution_results.json
    → dibaca oleh modul 01 untuk menentukan metode kalkulasi Xt

Referensi:
  SNI 2415:2016 — Tata cara perhitungan debit banjir rencana
  Soewarno (1995) — Hidrologi: Aplikasi Metode Statistik
"""

import numpy as np
import pandas as pd
import scipy.stats as stats
import yaml, json, os, math

# ── Load config ───────────────────────────────────────────────────────────────
with open("config.yaml") as f:
    cfg = yaml.safe_load(f)

os.makedirs(cfg["output"]["figures_dir"], exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv(cfg["data"]["rainfall_file"])
X  = df["max_tahunan"].values.astype(float)
n  = len(X)

print("=" * 60)
print("00 — DISTRIBUTION CHECK")
print("Uji kesesuaian distribusi frekuensi curah hujan")
print("=" * 60)
print(f"\n  n = {n} data ({df['tahun'].min()}–{df['tahun'].max()})")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Statistik dasar
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 1 — STATISTIK DASAR")
print("=" * 60)

mean_X  = np.mean(X)
std_X   = np.std(X, ddof=1)
Cv      = std_X / mean_X

# Cs (koefisien skewness)
Cs = (n * np.sum((X - mean_X)**3)) / ((n-1) * (n-2) * std_X**3)

# Ck (koefisien kurtosis)
Ck = (n**2 * (n+1) * np.sum((X - mean_X)**4)) / (
     (n-1) * (n-2) * (n-3) * std_X**4)

# Log statistik (untuk Log Normal & LP3)
log_X   = np.log10(X)
mean_lX = np.mean(log_X)
std_lX  = np.std(log_X, ddof=1)
Cv_log  = std_lX / mean_lX

Cs_log  = (n * np.sum((log_X - mean_lX)**3)) / (
           (n-1) * (n-2) * std_lX**3)
Ck_log  = (n**2 * (n+1) * np.sum((log_X - mean_lX)**4)) / (
           (n-1) * (n-2) * (n-3) * std_lX**4)

print(f"""
  Data asli (X):
    Mean (X̄)   = {mean_X:.4f} mm
    Std dev (S) = {std_X:.4f} mm
    Cv          = {Cv:.4f}
    Cs          = {Cs:.4f}
    Ck          = {Ck:.4f}

  Log data (log X):
    Mean        = {mean_lX:.4f}
    Std dev     = {std_lX:.4f}
    Cs log      = {Cs_log:.4f}
    Ck log      = {Ck_log:.4f}
""")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Cek syarat distribusi (SNI 2415:2016)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 2 — CEK SYARAT DISTRIBUSI (SNI 2415:2016)")
print("=" * 60)

# Syarat Log Normal: Cs ≈ 3Cv + Cv³, Ck ≈ Cv⁸ + 6Cv⁶ + 15Cv⁴ + 16Cv² + 3
Cs_ln_teoritis = 3 * Cv + Cv**3
Ck_ln_teoritis = Cv**8 + 6*Cv**6 + 15*Cv**4 + 16*Cv**2 + 3

syarat = {
    "Normal": {
        "lolos": abs(Cs) < 0.5 and abs(Ck - 3.0) < 0.5,
        "keterangan": f"Cs ≈ 0 (aktual: {Cs:.3f}), Ck ≈ 3 (aktual: {Ck:.3f})",
        "Cs_syarat": "≈ 0",
        "Ck_syarat": "≈ 3",
    },
    "Log Normal": {
        "lolos": (abs(Cs - Cs_ln_teoritis) < 0.5 and
                  abs(Ck - Ck_ln_teoritis) < 1.0),
        "keterangan": (f"Cs ≈ {Cs_ln_teoritis:.3f} (aktual: {Cs:.3f}), "
                       f"Ck ≈ {Ck_ln_teoritis:.3f} (aktual: {Ck:.3f})"),
        "Cs_syarat": f"≈ {Cs_ln_teoritis:.3f}",
        "Ck_syarat": f"≈ {Ck_ln_teoritis:.3f}",
    },
    "Gumbel": {
        "lolos": Cs <= 1.1396 and Ck <= 5.4002,
        "keterangan": f"Cs ≤ 1.14 (aktual: {Cs:.3f}), Ck ≤ 5.40 (aktual: {Ck:.3f})",
        "Cs_syarat": "≤ 1.1396",
        "Ck_syarat": "≤ 5.4002",
    },
    "Log Pearson III": {
        "lolos": True,  # Universal — tidak ada batasan Cs/Ck
        "keterangan": "Tidak ada syarat Cs/Ck (universal)",
        "Cs_syarat": "bebas",
        "Ck_syarat": "bebas",
    },
}

print(f"\n  {'Distribusi':<20} {'Lolos?':<10} Keterangan")
print(f"  {'-'*70}")
for nama, val in syarat.items():
    status = "✓ LOLOS" if val["lolos"] else "✗ TIDAK"
    print(f"  {nama:<20} {status:<10} {val['keterangan']}")

distribusi_lolos = [k for k, v in syarat.items() if v["lolos"]]
print(f"\n  Distribusi yang lolos syarat: {', '.join(distribusi_lolos)}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Goodness of Fit: Chi-Square
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 3 — UJI CHI-SQUARE (α = 5%)")
print("=" * 60)

def chi_square_test(data, dist_name, alpha=0.05):
    """
    Uji Chi-Square untuk distribusi yang ditentukan.
    Jumlah kelas k = 1 + 3.322 * log10(n) (Sturges rule).
    """
    n_data = len(data)
    k      = max(5, int(1 + 3.322 * math.log10(n_data)))

    # Fit distribusi
    if dist_name == "Normal":
        params = stats.norm.fit(data)
        dist   = stats.norm(*params)
    elif dist_name == "Log Normal":
        params = stats.lognorm.fit(data, floc=0)
        dist   = stats.lognorm(*params)
    elif dist_name == "Gumbel":
        params = stats.gumbel_r.fit(data)
        dist   = stats.gumbel_r(*params)
    elif dist_name == "Log Pearson III":
        log_d  = np.log10(data)
        params = stats.pearson3.fit(log_d)
        # Konversi kembali ke skala asli untuk binning
        dist   = None  # Tangani manual di bawah

    # Buat bins dari persentil distribusi agar frekuensi teoritis seragam
    persentil = np.linspace(0, 100, k + 1)
    bins      = np.percentile(data, persentil)
    bins[0]   = -np.inf
    bins[-1]  =  np.inf

    # Frekuensi observasi
    f_obs = np.histogram(data, bins=bins)[0]

    # Frekuensi ekspektasi
    if dist_name == "Log Pearson III":
        log_d    = np.log10(data)
        params   = stats.pearson3.fit(log_d)
        lp3_dist = stats.pearson3(*params)
        f_exp    = np.array([
            n_data * (lp3_dist.cdf(np.log10(bins[i+1])) -
                      lp3_dist.cdf(np.log10(max(bins[i], 1e-10))))
            for i in range(k)
        ])
    else:
        f_exp = np.array([
            n_data * (dist.cdf(bins[i+1]) - dist.cdf(bins[i]))
            for i in range(k)
        ])

    # Hindari pembagi nol
    f_exp = np.where(f_exp < 0.5, 0.5, f_exp)

    # Chi-square statistic
    chi2_stat = np.sum((f_obs - f_exp)**2 / f_exp)
    df_stat   = k - 1 - 2  # k - 1 - jumlah parameter yang diestimasi
    df_stat   = max(1, df_stat)
    chi2_krit = stats.chi2.ppf(1 - alpha, df_stat)
    p_value   = 1 - stats.chi2.cdf(chi2_stat, df_stat)

    return {
        "chi2_stat": round(chi2_stat, 4),
        "chi2_krit": round(chi2_krit, 4),
        "df":        df_stat,
        "p_value":   round(p_value, 4),
        "lolos":     chi2_stat <= chi2_krit,
    }


gof_chi2 = {}
print(f"\n  {'Distribusi':<20} {'χ² hitung':<12} {'χ² kritis':<12} {'p-value':<10} {'Status'}")
print(f"  {'-'*65}")
for nama in distribusi_lolos:
    hasil = chi_square_test(X, nama)
    gof_chi2[nama] = hasil
    status = "✓ LOLOS" if hasil["lolos"] else "✗ TIDAK"
    print(f"  {nama:<20} {hasil['chi2_stat']:<12.4f} {hasil['chi2_krit']:<12.4f} "
          f"{hasil['p_value']:<10.4f} {status}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Goodness of Fit: Kolmogorov-Smirnov
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 4 — UJI KOLMOGOROV-SMIRNOV (α = 5%)")
print("=" * 60)

# Nilai kritis KS untuk α=5%: D_kritis = 1.36 / sqrt(n)
D_kritis = 1.36 / math.sqrt(n)

def ks_test(data, dist_name):
    """Uji Kolmogorov-Smirnov manual sesuai SNI."""
    data_sorted = np.sort(data)
    n_data      = len(data_sorted)

    # CDF empiris (Weibull plotting position)
    F_emp = np.arange(1, n_data + 1) / (n_data + 1)

    # CDF teoritis
    if dist_name == "Normal":
        params  = stats.norm.fit(data)
        F_teor  = stats.norm.cdf(data_sorted, *params)
    elif dist_name == "Log Normal":
        params  = stats.lognorm.fit(data, floc=0)
        F_teor  = stats.lognorm.cdf(data_sorted, *params)
    elif dist_name == "Gumbel":
        params  = stats.gumbel_r.fit(data)
        F_teor  = stats.gumbel_r.cdf(data_sorted, *params)
    elif dist_name == "Log Pearson III":
        log_d   = np.log10(data_sorted)
        params  = stats.pearson3.fit(np.log10(data))
        F_teor  = stats.pearson3.cdf(log_d, *params)

    D_max = np.max(np.abs(F_emp - F_teor))
    return {
        "D_max":    round(D_max, 4),
        "D_kritis": round(D_kritis, 4),
        "p_value":  round(float(stats.kstest(data, "norm").pvalue), 4),
        "lolos":    D_max <= D_kritis,
    }


gof_ks = {}
print(f"\n  D kritis (α=5%, n={n}): {D_kritis:.4f}")
print(f"\n  {'Distribusi':<20} {'D maks':<12} {'D kritis':<12} {'Status'}")
print(f"  {'-'*55}")
for nama in distribusi_lolos:
    hasil = ks_test(X, nama)
    gof_ks[nama] = hasil
    status = "✓ LOLOS" if hasil["lolos"] else "✗ TIDAK"
    print(f"  {nama:<20} {hasil['D_max']:<12.4f} {hasil['D_kritis']:<12.4f} {status}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Rekomendasi distribusi
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 5 — REKOMENDASI DISTRIBUSI")
print("=" * 60)

# Skor: lolos Chi2 = +2, lolos KS = +2, LP3 universal bonus = +1
# Tiebreaker: p-value Chi2 tertinggi menang
skor = {}
for nama in distribusi_lolos:
    s  = 0
    s += 2 if gof_chi2.get(nama, {}).get("lolos", False) else 0
    s += 2 if gof_ks.get(nama, {}).get("lolos", False) else 0
    s += 1 if nama == "Log Pearson III" else 0
    p  = gof_chi2.get(nama, {}).get("p_value", 0)
    skor[nama] = (s, p)

# Sort: skor tertinggi, lalu p-value tertinggi
ranking = sorted(skor.items(), key=lambda x: (x[1][0], x[1][1]), reverse=True)

print(f"\n  {'Rank':<6} {'Distribusi':<20} {'Skor':<8} {'p-value Chi2'}")
print(f"  {'-'*50}")
for i, (nama, (s, p)) in enumerate(ranking):
    marker = "  ← TERPILIH" if i == 0 else ""
    print(f"  {i+1:<6} {nama:<20} {s:<8} {p:.4f}{marker}")

distribusi_terpilih = ranking[0][0]
alasan_parts = []
if syarat[distribusi_terpilih]["lolos"]:
    alasan_parts.append(f"lolos syarat Cs/Ck")
if gof_chi2.get(distribusi_terpilih, {}).get("lolos"):
    alasan_parts.append(f"lolos Chi-Square (χ²={gof_chi2[distribusi_terpilih]['chi2_stat']})")
if gof_ks.get(distribusi_terpilih, {}).get("lolos"):
    alasan_parts.append(f"lolos KS (D={gof_ks[distribusi_terpilih]['D_max']})")

alasan = " | ".join(alasan_parts) if alasan_parts else "satu-satunya kandidat"

print(f"""
  ✓ Distribusi terpilih : {distribusi_terpilih}
  ✓ Alasan              : {alasan}
  ✓ Cs data             : {Cs:.4f}
  ✓ Ck data             : {Ck:.4f}
""")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Simpan JSON
# ══════════════════════════════════════════════════════════════════════════════
output = {
    "distribusi_terpilih": distribusi_terpilih,
    "alasan": alasan,
    "statistik": {
        "n":        n,
        "mean":     round(mean_X, 4),
        "std":      round(std_X, 4),
        "Cv":       round(Cv, 4),
        "Cs":       round(Cs, 4),
        "Ck":       round(Ck, 4),
        "mean_log": round(mean_lX, 4),
        "std_log":  round(std_lX, 4),
        "Cs_log":   round(Cs_log, 4),
        "Ck_log":   round(Ck_log, 4),
    },
    "syarat_distribusi": {
        nama: {
            "lolos_syarat": val["lolos"],
            "Cs_syarat":    val["Cs_syarat"],
            "Ck_syarat":    val["Ck_syarat"],
        }
        for nama, val in syarat.items()
    },
    "goodness_of_fit": {
        nama: {
            "chi_square": gof_chi2.get(nama, {}),
            "kolmogorov_smirnov": gof_ks.get(nama, {}),
        }
        for nama in distribusi_lolos
    },
    "ranking": [
        {"rank": i+1, "distribusi": nama, "skor": s, "p_value_chi2": p}
        for i, (nama, (s, p)) in enumerate(ranking)
    ],
}

os.makedirs("output", exist_ok=True)
with open("output/00_distribution_results.json", "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("=" * 60)
print("00_distribution_check.py — SELESAI")
print(f"  Output → output/00_distribution_results.json")
print(f"  Distribusi untuk modul 01: {distribusi_terpilih}")
print("=" * 60)
