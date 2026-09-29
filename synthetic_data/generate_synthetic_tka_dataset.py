"""
Synthetic Anthropomorphic TKA CT Volume Generator
Generates realistic 3D volumetric datasets containing:
- Proximal tibia cortical envelope and cancellous trabecular bed
- Metallic tibial baseplate and central stem/keel (CoCrMo, > 3000 HU)
- PMMA bone cement mantle
- Simulated metal beam-hardening and streak artifacts
- Multi-rod solid HA calibration phantom (0, 50, 100, 200, 400 mg HA/cm3)
- Longitudinal follow-up with simulated stress shielding bone loss
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import Tuple, Dict, Any

def generate_synthetic_tka_scan(
    dim: Tuple[int, int, int] = (48, 96, 96),
    is_followup: bool = False,
    resorption_severity: float = 0.25
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Generate a 3D synthetic knee CT volume (HU) and ground-truth density.
    dim: (Z_slices, Y_rows, X_cols)
    """
    z_dim, y_dim, x_dim = dim
    vol_hu = np.full(dim, -900.0, dtype=np.float32)  # Ambient Air
    gt_vbmd = np.zeros(dim, dtype=np.float32)

    # 1. Soft Tissue Envelope (Leg contour)
    z_idx, y_idx, x_idx = np.indices(dim)
    cy, cx = y_dim // 2, x_dim // 2
    r_leg = 38.0
    leg_mask = ((y_idx - cy)**2 + (x_idx - cx)**2) <= r_leg**2
    vol_hu[leg_mask] = 40.0 + np.random.normal(0, 8, size=np.sum(leg_mask))

    # 2. Tibial Bone Envelope (Metaphysis tapering to diaphysis)
    # Radius tapers along Z (slice 0 is proximal, slice max is distal)
    r_bone_y = 26.0 - 0.2 * z_idx
    r_bone_x = 22.0 - 0.15 * z_idx
    bone_envelope = (((y_idx - cy) / r_bone_y)**2 + ((x_idx - cx) / r_bone_x)**2) <= 1.0

    # Cortical Shell (outer 3 voxels)
    inner_cortex = (((y_idx - cy) / (r_bone_y - 2.5))**2 + ((x_idx - cx) / (r_bone_x - 2.5))**2) <= 1.0
    cortex_mask = bone_envelope & (~inner_cortex)
    vol_hu[cortex_mask] = 1250.0 + np.random.normal(0, 40, size=np.sum(cortex_mask))
    gt_vbmd[cortex_mask] = 1100.0

    # Trabecular Cancellous Bed
    trabecular_mask = bone_envelope & inner_cortex
    base_trab_hu = 220.0
    base_trab_density = 200.0

    # If longitudinal follow-up, introduce stress-shielding bone resorption in medial sub-plate (x < cx, z < 12)
    if is_followup:
        medial_resorption = trabecular_mask & (x_idx < cx) & (z_idx < 12)
        vol_hu[trabecular_mask] = base_trab_hu + np.random.normal(0, 25, size=np.sum(trabecular_mask))
        gt_vbmd[trabecular_mask] = base_trab_density
        # Apply resorption
        vol_hu[medial_resorption] = (base_trab_hu * (1.0 - resorption_severity)) + np.random.normal(0, 20, size=np.sum(medial_resorption))
        gt_vbmd[medial_resorption] = base_trab_density * (1.0 - resorption_severity)
    else:
        vol_hu[trabecular_mask] = base_trab_hu + np.random.normal(0, 25, size=np.sum(trabecular_mask))
        gt_vbmd[trabecular_mask] = base_trab_density

    # 3. Metallic Tibial Component (Tray + Keel)
    # Tibial Baseplate: proximal slices, elliptical tray
    tray_mask = (z_idx <= 4) & ((((y_idx - cy) / 20.0)**2 + ((x_idx - cx) / 18.0)**2) <= 1.0)
    # Keel / Stem: central fin
    keel_mask = (z_idx > 4) & (z_idx <= min(22, z_dim - 5)) & (np.abs(y_idx - cy) <= 3) & (np.abs(x_idx - cx) <= 5)
    metal_mask = tray_mask | keel_mask

    # 4. PMMA Bone Cement Layer (around keel and tray base)
    cement_zone = (
        ((z_idx == 5) & ((((y_idx - cy) / 20.0)**2 + ((x_idx - cx) / 18.0)**2) <= 1.0)) |
        ((z_idx > 4) & (z_idx <= min(23, z_dim - 4)) & (np.abs(y_idx - cy) <= 5) & (np.abs(x_idx - cx) <= 7) & (~metal_mask))
    ) & bone_envelope
    vol_hu[cement_zone] = 230.0 + np.random.normal(0, 15, size=np.sum(cement_zone))

    # Overwrite metal (CoCr: 3200 HU)
    vol_hu[metal_mask] = 3200.0

    # 5. Simulated Beam Hardening & Streak Artifacts radiating from metal
    streaks = np.zeros(dim, dtype=np.float32)
    for z in range(z_dim):
        if np.any(metal_mask[z, :, :]):
            # Dark streaks connecting dense regions
            cupping = np.exp(-(((y_idx[z, :, :] - cy)**2 + (x_idx[z, :, :] - cx)**2) / 60.0))
            streaks[z, :, :] -= cupping * 120.0
            # Radial bright streak spikes along axes
            spikes = (np.abs(y_idx[z, :, :] - cy) < 2) | (np.abs(x_idx[z, :, :] - cx) < 2)
            streaks[z, :, :] += spikes * 160.0

    streaks = gaussian_filter(streaks, sigma=[0.5, 1.2, 1.2])
    vol_hu += streaks

    # 6. Synchronous Solid HA Calibration Phantom Rods (Posterior Splint)
    phantom_densities = [0.0, 50.0, 100.0, 200.0, 400.0]
    phantom_hus = [-50.0, 50.0, 150.0, 350.0, 750.0]
    phantom_info = []

    rod_radius = 3.0
    rod_y = y_dim - 8
    rod_spacing_x = x_dim // 6

    for i, (d_val, h_val) in enumerate(zip(phantom_densities, phantom_hus)):
        rod_x = (i + 1) * rod_spacing_x
        rod_mask = ((y_idx - rod_y)**2 + (x_idx - rod_x)**2) <= rod_radius**2
        vol_hu[rod_mask] = h_val + np.random.normal(0, 5, size=np.sum(rod_mask))
        phantom_info.append({
            "concentration_mg_ha_cm3": d_val,
            "expected_hu": h_val,
            "center": [z_dim // 2, rod_y, rod_x],
            "radius_voxels": rod_radius
        })

    metadata = {
        "KVP": 140,
        "SliceThickness": 0.6,
        "PixelSpacing": [0.4, 0.4],
        "CTDIvol": 14.2,
        "DLP": 215.0,
        "IsDualEnergy": False,
        "PhantomIncluded": True,
        "PhantomRods": phantom_info,
        "PatientID": "TKA_PATIENT_001_LONGITUDINAL",
        "StudyDate": "2026-09-29" if not is_followup else "2027-09-29"
    }

    return vol_hu, gt_vbmd, metadata

if __name__ == "__main__":
    v, gt, meta = generate_synthetic_tka_scan()
    print(f"Synthesized CT Volume: shape={v.shape}, min_hu={v.min():.1f}, max_hu={v.max():.1f}")
