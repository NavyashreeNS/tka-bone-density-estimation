"""
Stage 5: Quantitative Density Calibration & Partial Volume Correction
Converts CT attenuation numbers (HU) to absolute volumetric Bone Mineral Density
(mg HA/cm3) via synchronous phantom regression or internal tissue calibration,
incorporating sub-voxel partial volume correction at metal interfaces.
"""

import numpy as np
from typing import Dict, Any, Tuple, List

class DensityCalibrationEngine:
    """
    Calibrates CT image intensities into true physical bone mineral density
    (vBMD in mg HA/cm3) and applies interface partial volume corrections.
    """

    def __init__(self):
        self.slope = 1.0
        self.intercept = 0.0
        self.r_squared = 1.0
        self.is_calibrated = False

    def calibrate_from_phantom(
        self, measured_hus: List[float], known_densities: List[float]
    ) -> Dict[str, Any]:
        """
        Fit linear calibration: vBMD = slope * HU + intercept
        """
        x = np.array(measured_hus, dtype=np.float64)
        y = np.array(known_densities, dtype=np.float64)

        poly_coeffs = np.polyfit(x, y, deg=1)
        self.slope = float(poly_coeffs[0])
        self.intercept = float(poly_coeffs[1])

        y_pred = self.slope * x + self.intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        self.r_squared = float(1.0 - (ss_res / (ss_tot + 1e-8)))
        self.is_calibrated = True

        return {
            "method": "synchronous_phantom",
            "slope": round(self.slope, 6),
            "intercept": round(self.intercept, 4),
            "r_squared": round(self.r_squared, 5),
            "measured_hus": x.tolist(),
            "known_densities": y.tolist()
        }

    def calibrate_from_internal_tissues(
        self,
        fat_hu: float = -95.0,
        muscle_hu: float = 50.0,
        cortex_hu: float = 1350.0,
        cortex_ref_density: float = 1200.0
    ) -> Dict[str, Any]:
        """
        Internal calibration fallback using adipose, muscle, and cortical reference points.
        """
        x = np.array([fat_hu, muscle_hu, cortex_hu], dtype=np.float64)
        y = np.array([0.0, 5.0, cortex_ref_density], dtype=np.float64)
        return self.calibrate_from_phantom(x.tolist(), y.tolist())

    def convert_hu_to_vbmd(self, hu_array: np.ndarray) -> np.ndarray:
        """Convert arbitrary HU array to vBMD in mg HA/cm3."""
        vbmd = self.slope * hu_array + self.intercept
        return np.maximum(0.0, vbmd)

    def apply_partial_volume_correction(
        self,
        vbmd_volume: np.ndarray,
        distance_to_metal_mm: np.ndarray,
        voxel_size_mm: float = 0.5
    ) -> np.ndarray:
        """
        Correct partial volume averaging for voxels within 1.0 mm of metal.
        Estimated bone fraction alpha varies linearly from 0.3 at surface to 1.0 at 1.0 mm.
        """
        corrected = vbmd_volume.copy()
        boundary_mask = (distance_to_metal_mm > 0.0) & (distance_to_metal_mm < 1.0)

        if np.any(boundary_mask):
            # alpha linearly increases with distance
            alpha = np.clip(distance_to_metal_mm[boundary_mask] / 1.0, 0.25, 1.0)
            # Unmix partial volume
            corrected[boundary_mask] = np.maximum(0.0, vbmd_volume[boundary_mask] / alpha)

        return corrected
