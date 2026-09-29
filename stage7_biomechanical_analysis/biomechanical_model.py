"""
Stage 7: Biomechanical Modeling & Longitudinal Remodeling Analysis
Implements density-to-elasticity constitutive mappings (Morgan & Keaveny, Keller),
Least Significant Change (LSC) longitudinal filtering, and Loosening Vulnerability Index (LVI).
"""

import numpy as np
from typing import Dict, Any, Tuple

class BiomechanicalAnalyzer:
    """
    Translates quantitative bone density maps into biomechanical elasticity tensors
    and tracks longitudinal remodeling dynamics.
    """

    def __init__(self, precision_error_cv: float = 1.5):
        # 1.5% precision error typical for calibrated clinical QCT
        self.cv = precision_error_cv
        # 95% confidence threshold for true biological change
        self.lsc_pct = 2.77 * self.cv

    def density_to_modulus(
        self,
        vbmd_volume: np.ndarray,
        model: str = "morgan_keaveny_2001"
    ) -> np.ndarray:
        """
        Converts vBMD (mg HA/cm3) to Young's Modulus E (MPa).
        vBMD in mg/cm3 -> rho_ash in g/cm3 (divide by 1000).
        """
        # ash density in g/cm3
        rho_ash = np.maximum(0.0, vbmd_volume / 1000.0)
        e_modulus = np.zeros_like(vbmd_volume, dtype=np.float32)

        if model == "morgan_keaveny_2001":
            # E = 3790 * (rho_ash)^2.18  [MPa]
            e_modulus = 3790.0 * np.power(rho_ash, 2.18)
        elif model == "keller_1994":
            # E = 2017 * (rho_ash)^1.67  [MPa]
            e_modulus = 2017.0 * np.power(rho_ash, 1.67)
        elif model == "carter_hayes_1977":
            # rho_app approx rho_ash / 0.6
            rho_app = rho_ash / 0.6
            e_modulus = 3790.0 * np.power(rho_app, 3.0)
        else:
            raise ValueError(f"Unknown constitutive model: {model}")

        # Clip unphysical values (trabecular: 5-3000 MPa, cortical: up to 20000 MPa)
        return np.clip(e_modulus, 0.0, 25000.0)

    def analyze_longitudinal_change(
        self,
        baseline_stats: Dict[str, Any],
        followup_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Computes % delta vBMD across zones and classifies biological significance.
        """
        comparison = {}
        for region_type in ["anatomical_zones", "distance_shells"]:
            comparison[region_type] = {}
            b_regions = baseline_stats.get(region_type, {})
            f_regions = followup_stats.get(region_type, {})

            for name, b_data in b_regions.items():
                f_data = f_regions.get(name, {})
                b_mean = b_data.get("mean_vbmd", 0.0)
                f_mean = f_data.get("mean_vbmd", 0.0)

                if b_mean > 1e-4:
                    pct_change = ((f_mean - b_mean) / b_mean) * 100.0
                else:
                    pct_change = 0.0

                # Statistical Significance Filter based on LSC
                is_significant = abs(pct_change) > self.lsc_pct
                if not is_significant:
                    status = "STABLE"
                elif pct_change < 0:
                    status = "RESORPTION_STRESS_SHIELDING"
                else:
                    status = "SCLEROSIS_BONE_FORMATION"

                comparison[region_type][name] = {
                    "baseline_vbmd": b_mean,
                    "followup_vbmd": f_mean,
                    "delta_vbmd": round(f_mean - b_mean, 2),
                    "pct_change": round(pct_change, 2),
                    "lsc_threshold_pct": round(self.lsc_pct, 2),
                    "is_biologically_significant": is_significant,
                    "classification": status
                }

        return comparison

    def compute_loosening_vulnerability_index(
        self, shell_a_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Computes Loosening Vulnerability Index (LVI) at the immediate interface.
        LVI = fraction of bone in Shell A (< 0.5 mm) with vBMD < 100 mg HA/cm3.
        """
        pct_resorbed = shell_a_stats.get("pct_resorbed_low_density", 0.0)
        lvi = pct_resorbed / 100.0

        if lvi < 0.15:
            risk = "LOW_RISK"
        elif lvi <= 0.35:
            risk = "MODERATE_RISK"
        else:
            risk = "HIGH_RISK_ASEPTIC_LOOSENING"

        return {
            "loosening_vulnerability_index": round(lvi, 3),
            "interface_low_density_pct": round(pct_resorbed, 2),
            "clinical_risk_category": risk
        }
