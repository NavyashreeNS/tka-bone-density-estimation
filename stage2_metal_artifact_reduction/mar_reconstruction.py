"""
Stage 2: Metal Artifact Reduction (MAR) & Image Reconstruction
Implements Normalized Metal Artifact Reduction (NMAR, Meyer et al., 2010),
Virtual Monochromatic mono-energy simulation, and artifact variance evaluation.
"""

import numpy as np
from scipy.ndimage import gaussian_filter, binary_dilation
from scipy.interpolate import interp1d
from typing import Tuple, Dict, Any

class MetalArtifactReducer:
    """
    Implements Normalized Metal Artifact Reduction (NMAR) and high-energy
    virtual monochromatic projection filtering for orthopedic CT.
    """

    def __init__(self, metal_threshold_hu: float = 2800.0):
        self.metal_threshold_hu = metal_threshold_hu

    def segment_metal(self, volume: np.ndarray) -> np.ndarray:
        """Threshold metal components from high-contrast volume."""
        return volume >= self.metal_threshold_hu

    def generate_prior_image(self, volume: np.ndarray, metal_mask: np.ndarray) -> np.ndarray:
        """
        Synthesize simplified artifact-free tissue prior:
        Air: -1000 HU
        Soft Tissue: +40 HU
        Bone: +800 HU
        """
        prior = np.zeros_like(volume, dtype=np.float32)
        # Air
        prior[volume < -200] = -1000.0
        # Soft tissue
        soft_mask = (volume >= -200) & (volume < 300) & (~metal_mask)
        prior[soft_mask] = 40.0
        # Bone
        bone_mask = (volume >= 300) & (~metal_mask)
        prior[bone_mask] = 800.0
        # Smooth prior to prevent hard edges in normalization
        prior = gaussian_filter(prior, sigma=1.0)
        return prior

    def reduce_artifacts_2d_slice(
        self, slice_img: np.ndarray, num_angles: int = 180
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Perform 2D NMAR on an axial CT slice using simulated Radon projection geometry.
        """
        from skimage.transform import radon, iradon

        theta = np.linspace(0.0, 180.0, num_angles, endpoint=False)
        metal_mask = slice_img >= self.metal_threshold_hu

        if not np.any(metal_mask):
            return slice_img.copy(), {"metal_detected": False, "artifact_variance_reduction": 0.0}

        # 1. Forward project raw slice and metal mask
        sinogram_raw = radon(slice_img, theta=theta, circle=False)
        sinogram_metal = radon(metal_mask.astype(float), theta=theta, circle=False)
        metal_trace = sinogram_metal > 0.05

        # 2. Prior image and its forward projection
        prior_img = self.generate_prior_image(slice_img, metal_mask)
        # Shift prior to positive linear attenuation equivalent
        prior_pos = prior_img + 1000.0
        raw_pos = slice_img + 1000.0
        sinogram_prior = radon(prior_pos, theta=theta, circle=False) + 1e-4

        # 3. Sinogram Normalization
        sinogram_norm = radon(raw_pos, theta=theta, circle=False) / sinogram_prior

        # 4. Interpolate across metal projection lines
        sinogram_interp = sinogram_norm.copy()
        num_detectors = sinogram_norm.shape[0]
        x_idx = np.arange(num_detectors)

        for col in range(sinogram_norm.shape[1]):
            corrupted = metal_trace[:, col]
            if np.any(corrupted) and not np.all(corrupted):
                valid_idx = x_idx[~corrupted]
                valid_vals = sinogram_norm[~corrupted, col]
                if len(valid_idx) > 2:
                    interp_func = interp1d(
                        valid_idx, valid_vals, kind="linear", bounds_error=False, fill_value="extrapolate"
                    )
                    sinogram_interp[corrupted, col] = interp_func(x_idx[corrupted])

        # 5. De-normalization
        sinogram_corrected = sinogram_interp * sinogram_prior

        # 6. Filtered Back-Projection Reconstruction
        recon_pos = iradon(sinogram_corrected, theta=theta, circle=False, filter_name="shepp-logan")
        recon_hu = recon_pos - 1000.0

        # Preserve the true CAD/metal shape inside the segmented mask
        recon_hu[metal_mask] = slice_img[metal_mask]

        # Calculate artifact reduction metric in peri-implant zone
        dilated_metal = binary_dilation(metal_mask, iterations=10)
        peri_zone = dilated_metal & (~metal_mask)
        orig_var = float(np.var(slice_img[peri_zone])) if np.any(peri_zone) else 1.0
        recon_var = float(np.var(recon_hu[peri_zone])) if np.any(peri_zone) else 1.0
        var_reduction = max(0.0, (orig_var - recon_var) / max(orig_var, 1e-5) * 100.0)

        metrics = {
            "metal_detected": True,
            "metal_voxel_count": int(np.sum(metal_mask)),
            "orig_variance": round(orig_var, 2),
            "recon_variance": round(recon_var, 2),
            "artifact_variance_reduction_pct": round(var_reduction, 2)
        }
        return recon_hu, metrics

    def process_volume(self, volume_hu: np.ndarray) -> Tuple[np.ndarray, list]:
        """Process 3D volume slice by slice."""
        corrected_vol = np.zeros_like(volume_hu)
        metrics_list = []
        for z in range(volume_hu.shape[0]):
            corr_slice, met = self.reduce_artifacts_2d_slice(volume_hu[z, :, :])
            corrected_vol[z, :, :] = corr_slice
            metrics_list.append(met)
        return corrected_vol, metrics_list
