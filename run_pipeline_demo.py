"""
Executable Demonstration: End-to-End Patient-Specific TKA Bone Density Pipeline
Synthesizes a realistic anthropomorphic TKA knee volume, executes all 8 stages,
and produces full clinical outputs and longitudinal remodeling analyses.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from synthetic_data.generate_synthetic_tka_dataset import generate_synthetic_tka_scan
from pipeline_orchestrator import TKABoneDensityPipeline

def main():
    print("======================================================================")
    print(" PATIENT-SPECIFIC QUANTITATIVE BONE DENSITY ESTIMATION PIPELINE (TKA) ")
    print("======================================================================\n")

    # 1. Synthesize Baseline (T0) and 12-Month Follow-Up (T1) CT volumes
    print("Generating synthetic anthropomorphic TKA scans...")
    print(" - Baseline (Immediate Post-Op)")
    base_scan = generate_synthetic_tka_scan(dim=(36, 72, 72), is_followup=False)

    print(" - Follow-up (12-Month Post-Op with Medial Sub-Plate Stress Shielding)")
    foll_scan = generate_synthetic_tka_scan(dim=(36, 72, 72), is_followup=True, resorption_severity=0.28)

    # 2. Instantiate and Execute Pipeline
    output_directory = os.path.join(BASE_DIR, "output")
    pipeline = TKABoneDensityPipeline(output_dir=output_directory)

    results = pipeline.run_longitudinal_study(base_scan, foll_scan)

    print("\n======================================================================")
    print(" EXECUTION COMPLETED SUCCESSFULLY")
    print("======================================================================")
    print(f"Output Directory: {output_directory}")
    print(f"Generated Files:")
    for f in os.listdir(output_directory):
        print(f" - {f}")

if __name__ == "__main__":
    main()
