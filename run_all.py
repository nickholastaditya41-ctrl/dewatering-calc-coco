"""
run_all.py — Mine Dewatering Calculator (Project 2)
Ref: Juan et al., Globe Vol.3 No.3, Agustus 2025
PT Bukit Baiduri Energi, Kutai Kartanegara, Kaltim

Usage: python run_all.py
"""

import subprocess, sys, os, time

os.makedirs("output/figures", exist_ok=True)

scripts = [
    ("01 — Rainfall Analysis (LP3)",        "src/01_rainfall_analysis.py"),
    ("02 — Forecast Moving Average",         "src/02_forecast_rainfall.py"),
    ("03 — Runoff Calculation",              "src/03_runoff_calculation.py"),
    ("04 — Sump Sizing (Kepmen ESDM 1827)",  "src/04_sump_sizing_kepmen.py"),
    ("05 — Pump Sizing (aktual lapangan)",   "src/05_pump_sizing.py"),
    ("06 — Water Balance (neraca air)",      "src/06_water_balance.py"),
]

print("=" * 60)
print("MINE DEWATERING CALCULATOR — PROJECT 2")
print("Ref: Juan et al., Globe Vol.3 No.3, 2025")
print("PT Bukit Baiduri Energi, Kutai Kartanegara")
print("=" * 60)

start  = time.time()
errors = []

for label, script in scripts:
    print(f"\n▶ {label}...")
    t0     = time.time()
    result = subprocess.run([sys.executable, script], capture_output=False)
    elapsed = time.time() - t0
    if result.returncode == 0:
        print(f"  ✓ Selesai ({elapsed:.1f}s)")
    else:
        print(f"  ✗ ERROR")
        errors.append(label)

total = time.time() - start
print("\n" + "=" * 60)
if not errors:
    print(f"✓ SEMUA SELESAI ({total:.1f}s)")
    print(f"  Output → output/")
    print(f"  Figures → output/figures/ (7 PNG)")
else:
    print(f"✗ {len(errors)} error:")
    for e in errors:
        print(f"  - {e}")
print("=" * 60)
