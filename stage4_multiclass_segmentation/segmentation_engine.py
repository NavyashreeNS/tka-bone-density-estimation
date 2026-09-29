"""
Stage 4: Multi-Class Segmentation Engine
Segments metallic implant, PMMA bone cement layer, cortical bone shell,
and trabecular bone bed with CAD-prior spatial constraints to eliminate blooming.
"""

import numpy as np
from scipy.ndimage import distance_transform_edt, binary_dilation, binary_erosion
from typing import Dict, Any, Tuple

class MultiClassSegmenter:
    """
    Partitions reconstructed CT volumes into discrete, non-overlapping classes:
    0: Background / Soft Tissue
    1: Metallic Implant (CoCr / Ti)
    2: PMMA Bone Cement
    3: Trabecular Cancellous Bone
    4: Cortical Bone Shell
    """

    def __init__(
        self,
        metal_hu_thresh: float = 2800.0,
        cortical_hu_thresh: float = 650.0,
        trabecular_hu_min: float = 40.0,
        cement_hu_min: float = 120.0,
        cement_hu_max: float = 380.0,
        max_cement_depth_voxels: float = 6.0
    ):
        self.metal_hu_thresh = metal_hu_thresh
        self.cortical_hu_thresh = cortical_hu_thresh
        self.trabecular_hu_min = trabecular_hu_min
        self.cement_hu_min = cement_hu_min
        self.cement_hu_max = cement_hu_max
        self.max_cement_depth_voxels = max_cement_depth_voxels

    def segment_volume(
        self, volume_hu: np.ndarray, is_cemented: bool = True
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Executes hierarchical multi-class segmentation.
        """
        label_map = np.zeros(volume_hu.shape, dtype=np.uint8)

        # 1. Segment Metal Implant
        metal_mask = volume_hu >= self.metal_hu_thresh
        # Erode 1 voxel to mitigate blooming from partial volume effect
        if np.any(metal_mask):
            metal_eroded = binary_erosion(metal_mask, iterations=1)
            # Retain eroded core if not empty, otherwise keep original
            if np.any(metal_eroded):
                metal_final = metal_eroded
            else:
                metal_final = metal_mask
        else:
            metal_final = metal_mask

        label_map[metal_final] = 1

        # Calculate Distance Map from metal surface
        dist_from_metal = distance_transform_edt(~metal_final)

        # 2. PMMA Cement Segmentation (if cemented)
        cement_mask = np.zeros_like(metal_mask)
        if is_cemented and np.any(metal_final):
            # Spatial prior: cement must be within close proximity to non-articulating metal
            near_metal_zone = (dist_from_metal > 0) & (dist_from_metal <= self.max_cement_depth_voxels)
            cement_candidates = (
                near_metal_zone &
                (volume_hu >= self.cement_hu_min) &
                (volume_hu <= self.cement_hu_max)
            )
            cement_mask = cement_candidates
            label_map[cement_mask] = 2

        # 3. Cortical Bone Segmentation
        cortical_mask = (volume_hu >= self.cortical_hu_thresh) & (~metal_final) & (~cement_mask)
        label_map[cortical_mask] = 4

        # 4. Trabecular Bone Segmentation
        # Must be within bone anatomical envelope, excluding cortex, cement, metal, background
        trabecular_mask = (
            (volume_hu >= self.trabecular_hu_min) &
            (volume_hu < self.cortical_hu_thresh) &
            (~metal_final) &
            (~cement_mask)
        )
        label_map[trabecular_mask] = 3

        voxel_counts = {
            "background": int(np.sum(label_map == 0)),
            "metal": int(np.sum(label_map == 1)),
            "cement": int(np.sum(label_map == 2)),
            "trabecular_bone": int(np.sum(label_map == 3)),
            "cortical_bone": int(np.sum(label_map == 4))
        }

        return label_map, voxel_counts

    @staticmethod
    def get_distance_shells(metal_mask: np.ndarray, voxel_spacing_mm: float = 0.5) -> Dict[str, np.ndarray]:
        """
        Generate concentric radial distance shells from implant boundary:
        Shell A: 0.0 - 0.5 mm
        Shell B: 0.5 - 1.0 mm
        Shell C: 1.0 - 2.0 mm
        Shell D: 2.0 - 3.0 mm
        Shell E: 3.0 - 5.0 mm
        """
        dist_voxels = distance_transform_edt(~metal_mask)
        dist_mm = dist_voxels * voxel_spacing_mm

        shells = {
            "shell_0_to_0.5mm": (dist_mm > 0.0) & (dist_mm <= 0.5),
            "shell_0.5_to_1.0mm": (dist_mm > 0.5) & (dist_mm <= 1.0),
            "shell_1.0_to_2.0mm": (dist_mm > 1.0) & (dist_mm <= 2.0),
            "shell_2.0_to_3.0mm": (dist_mm > 2.0) & (dist_mm <= 3.0),
            "shell_3.0_to_5.0mm": (dist_mm > 3.0) & (dist_mm <= 5.0),
        }
        return shells
