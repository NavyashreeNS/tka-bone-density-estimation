"""
Stage 3: Longitudinal Image Registration & Coordinate Frame Definition
Performs rigid registration anchored strictly to the diaphyseal cortical envelope,
preventing surgical resection bias and preserving raw scalar density values.
"""

import numpy as np
from scipy.ndimage import center_of_mass
from typing import Tuple, Dict, Any

class AnatomicalRegistrationEngine:
    """
    Computes patient-specific anatomical coordinate frames and registers
    longitudinal multi-time-point scans using cortical bone anchoring.
    """

    def __init__(self, diaphyseal_cutoff_slice: int = 15):
        self.diaphyseal_cutoff_slice = diaphyseal_cutoff_slice

    def define_anatomical_frame(self, bone_mask: np.ndarray) -> Dict[str, Any]:
        """
        Derives mechanical axis from the distal/diaphyseal cortical canal.
        """
        # Diaphyseal region: distal slices
        diaphysis_mask = bone_mask.copy()
        if diaphysis_mask.shape[0] > self.diaphyseal_cutoff_slice:
            diaphysis_mask[:self.diaphyseal_cutoff_slice, :, :] = False

        coords = np.argwhere(diaphysis_mask)
        if len(coords) < 100:
            coords = np.argwhere(bone_mask)

        # Centroid (Origin)
        origin = np.mean(coords, axis=0)

        # Principal inertia axes
        cov = np.cov(coords - origin, rowvar=False)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        # Primary axis is the direction of maximum variance (longitudinal axis)
        longitudinal_axis = eigenvectors[:, -1]

        return {
            "origin": origin.tolist(),
            "longitudinal_axis": longitudinal_axis.tolist(),
            "covariance_eigenvalues": eigenvalues.tolist()
        }

    def register_rigid(
        self, baseline_bone: np.ndarray, followup_bone: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Computes 3D rigid transformation [R, t] aligning follow-up to baseline
        anchored on diaphyseal cortical bone.
        """
        # Mask out operated epiphyseal zones
        b_diaph = baseline_bone.copy()
        f_diaph = followup_bone.copy()
        b_diaph[:self.diaphyseal_cutoff_slice, :, :] = False
        f_diaph[:self.diaphyseal_cutoff_slice, :, :] = False

        b_pts = np.argwhere(b_diaph)
        f_pts = np.argwhere(f_diaph)

        if len(b_pts) == 0 or len(f_pts) == 0:
            b_pts = np.argwhere(baseline_bone)
            f_pts = np.argwhere(followup_bone)

        # Center of mass alignment
        b_com = np.mean(b_pts, axis=0)
        f_com = np.mean(f_pts, axis=0)

        # Covariance matching (Kabsch algorithm on principal moments)
        H = np.dot((f_pts[:1000] - f_com).T, (b_pts[:1000] - b_com))
        U, S, Vt = np.linalg.svd(H)
        R = np.dot(Vt.T, U.T)

        # Ensure right-handed coordinate system (det = +1)
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = np.dot(Vt.T, U.T)

        t = b_com - np.dot(R, f_com)

        # Build 4x4 Affine Matrix
        T_matrix = np.eye(4)
        T_matrix[:3, :3] = R
        T_matrix[:3, 3] = t

        T_inv = np.linalg.inv(T_matrix)

        metrics = {
            "rotation_matrix": R.tolist(),
            "translation_vector": t.tolist(),
            "target_points_count": len(b_pts),
            "source_points_count": len(f_pts),
            "determinant": float(np.linalg.det(R))
        }
        return T_matrix, T_inv, metrics

    @staticmethod
    def transform_points(points: np.ndarray, T_matrix: np.ndarray) -> np.ndarray:
        """Apply 4x4 transformation matrix to [N x 3] point array."""
        homogeneous = np.hstack([points, np.ones((points.shape[0], 1))])
        transformed = np.dot(homogeneous, T_matrix.T)
        return transformed[:, :3]
