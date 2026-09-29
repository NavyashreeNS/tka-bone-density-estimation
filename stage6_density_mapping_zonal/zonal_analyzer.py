"""
Stage 6: 3D Zonal Density Mapping & Radial Isochrone Regional Analysis
Implements the 7-zone volumetric adaptation of the Ewald/Kozinn roentgenographic
system and extracts distance-isochrone shells (0-5 mm) from implant geometry.
"""

import numpy as np
from scipy.ndimage import distance_transform_edt
from typing import Dict, Any, List

class ZonalDensityAnalyzer:
    """
    Partitions proximal tibial bone into 7 anatomical volumetric zones
    and 5 concentric radial distance shells, extracting statistical density metrics.
    """

    def __init__(self, voxel_spacing_mm: List[float] = [0.6, 0.4, 0.4]):
        self.voxel_spacing = np.array(voxel_spacing_mm, dtype=np.float64)
        self.voxel_volume_cm3 = float(np.prod(self.voxel_spacing) / 1000.0)

    def partition_tibial_zones(
        self,
        bone_mask: np.ndarray,
        metal_mask: np.ndarray,
        center_x: int,
        center_y: int,
        tray_depth_voxels: int = 8,
        keel_depth_voxels: int = 20
    ) -> Dict[str, np.ndarray]:
        """
        Geometrically divides the proximal tibia into 7 volumetric zones.
        """
        zones = {}
        z_dim, y_dim, x_dim = bone_mask.shape

        # Zone 1: Medial Sub-Plate (depth 0-5 mm under medial tray, x < center_x)
        z1 = np.zeros_like(bone_mask, dtype=bool)
        z1[:tray_depth_voxels, :, :center_x] = True
        zones["Zone_1_Medial_SubPlate"] = z1 & bone_mask & (~metal_mask)

        # Zone 2: Lateral Sub-Plate (depth 0-5 mm under lateral tray, x >= center_x)
        z2 = np.zeros_like(bone_mask, dtype=bool)
        z2[:tray_depth_voxels, :, center_x:] = True
        zones["Zone_2_Lateral_SubPlate"] = z2 & bone_mask & (~metal_mask)

        # Zone 3: Anterior Margin (y < center_y)
        z3 = np.zeros_like(bone_mask, dtype=bool)
        z3[tray_depth_voxels:keel_depth_voxels, :center_y, :] = True
        zones["Zone_3_Anterior_Margin"] = z3 & bone_mask & (~metal_mask)

        # Zone 4: Posterior Margin (y >= center_y)
        z4 = np.zeros_like(bone_mask, dtype=bool)
        z4[tray_depth_voxels:keel_depth_voxels, center_y:, :] = True
        zones["Zone_4_Posterior_Margin"] = z4 & bone_mask & (~metal_mask)

        # Zone 5: Peri-Keel Central Cancellous Bed
        dist_from_metal = distance_transform_edt(~metal_mask)
        z5 = (dist_from_metal > 0) & (dist_from_metal <= 8)
        z5_cand = np.zeros_like(bone_mask, dtype=bool)
        z5_cand[tray_depth_voxels:keel_depth_voxels, :, :] = True
        zones["Zone_5_PeriKeel_Central"] = z5 & z5_cand & bone_mask & (~metal_mask)

        # Zone 6: Distal Stem Tip Apex Zone
        z6 = np.zeros_like(bone_mask, dtype=bool)
        z6[keel_depth_voxels:keel_depth_voxels + 10, :, :] = True
        zones["Zone_6_Distal_Stem_Apex"] = z6 & bone_mask & (~metal_mask)

        # Zone 7: Deep Diaphyseal Reference Baseline
        z7 = np.zeros_like(bone_mask, dtype=bool)
        z7[keel_depth_voxels + 10:, :, :] = True
        zones["Zone_7_Diaphyseal_Baseline"] = z7 & bone_mask & (~metal_mask)

        return zones

    def partition_distance_shells(
        self, bone_mask: np.ndarray, metal_mask: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """
        Radial concentric shells based on Euclidean distance to metal surface.
        """
        # Distance transform accounting for isotropic/anisotropic voxel spacing
        dist_voxels = distance_transform_edt(~metal_mask, sampling=self.voxel_spacing)
        shells = {}

        shell_ranges = [
            ("Shell_A_0.0_to_0.5mm", 0.0, 0.5),
            ("Shell_B_0.5_to_1.0mm", 0.5, 1.0),
            ("Shell_C_1.0_to_2.0mm", 1.0, 2.0),
            ("Shell_D_2.0_to_3.0mm", 2.0, 3.0),
            ("Shell_E_3.0_to_5.0mm", 3.0, 5.0),
        ]

        for name, d_min, d_max in shell_ranges:
            in_shell = (dist_voxels > d_min) & (dist_voxels <= d_max)
            shells[name] = in_shell & bone_mask & (~metal_mask)

        return shells

    def compute_region_statistics(
        self, vbmd_volume: np.ndarray, region_mask: np.ndarray
    ) -> Dict[str, Any]:
        """Calculate comprehensive descriptive statistics for an ROI."""
        vals = vbmd_volume[region_mask]
        if len(vals) == 0:
            return {
                "voxel_count": 0,
                "volume_cm3": 0.0,
                "mean_vbmd": 0.0,
                "std_vbmd": 0.0,
                "median_vbmd": 0.0,
                "pct_resorbed_low_density": 0.0
            }

        mean_v = float(np.mean(vals))
        std_v = float(np.std(vals))
        med_v = float(np.median(vals))
        vol_cm3 = float(len(vals) * self.voxel_volume_cm3)
        # Low density threshold (< 100 mg HA/cm3) indicates resorption/osteopenia
        low_density_ratio = float(np.sum(vals < 100.0) / len(vals) * 100.0)

        return {
            "voxel_count": int(len(vals)),
            "volume_cm3": round(vol_cm3, 3),
            "mean_vbmd": round(mean_v, 2),
            "std_vbmd": round(std_v, 2),
            "median_vbmd": round(med_v, 2),
            "pct_resorbed_low_density": round(low_density_ratio, 2)
        }

    def analyze_all_regions(
        self,
        vbmd_volume: np.ndarray,
        zones_dict: Dict[str, np.ndarray],
        shells_dict: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """Runs batch statistical analysis across all zones and shells."""
        zone_results = {}
        for z_name, mask in zones_dict.items():
            zone_results[z_name] = self.compute_region_statistics(vbmd_volume, mask)

        shell_results = {}
        for s_name, mask in shells_dict.items():
            shell_results[s_name] = self.compute_region_statistics(vbmd_volume, mask)

        return {
            "anatomical_zones": zone_results,
            "distance_shells": shell_results
        }
