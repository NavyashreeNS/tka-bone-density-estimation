"""
Stage 8: Quantitative Reporting, Visualization & PACS Export
Compiles patient-specific structured clinical reports (JSON and Markdown),
and generates multi-planar radiological density overlay visualizations.
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import Dict, Any

def sanitize_for_json(obj):
    """Recursively converts NumPy types to native Python types and filters out volumetric arrays."""
    if isinstance(obj, dict):
        clean_dict = {}
        for k, v in obj.items():
            if k == "arrays":
                continue
            clean_dict[k] = sanitize_for_json(v)
        return clean_dict
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        if obj.size <= 20:
            return obj.tolist()
        return f"<ndarray shape={obj.shape} dtype={obj.dtype}>"
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    return obj

class QuantitativeReportGenerator:
    """
    Generates standardized orthopedic reports and radiological density overlays.
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_json_report(
        self, patient_id: str, study_date: str, results_payload: Dict[str, Any]
    ) -> str:
        """Export comprehensive machine-readable JSON report."""
        report = {
            "patient_id": patient_id,
            "study_date": study_date,
            "pipeline_version": "2.4.0-TKA-QCT",
            "results": sanitize_for_json(results_payload)
        }
        json_path = os.path.join(self.output_dir, f"{patient_id}_quantitative_report.json")
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)
        return json_path

    def generate_markdown_report(
        self, patient_id: str, study_date: str, results_payload: Dict[str, Any]
    ) -> str:
        """Export structured clinical markdown report with summary tables."""
        md_path = os.path.join(self.output_dir, f"{patient_id}_clinical_summary.md")
        z_stats = results_payload.get("zonal_analysis", {}).get("anatomical_zones", {})
        s_stats = results_payload.get("zonal_analysis", {}).get("distance_shells", {})
        lvi = results_payload.get("biomechanics", {}).get("loosening_vulnerability", {})
        longitudinal = results_payload.get("longitudinal_comparison", {})

        with open(md_path, "w") as f:
            f.write(f"# Patient-Specific TKA Peri-Implant Bone Density Report\n\n")
            f.write(f"- **Patient ID**: `{patient_id}`\n")
            f.write(f"- **Study Date**: `{study_date}`\n")
            f.write(f"- **Clinical Risk Category**: **{lvi.get('clinical_risk_category', 'UNKNOWN')}**\n")
            f.write(f"- **Loosening Vulnerability Index (LVI)**: `{lvi.get('loosening_vulnerability_index', 'N/A')}`\n\n")

            f.write("## 1. Proximal Tibial Anatomic Zones (Modified Ewald/Kozinn)\n\n")
            f.write("| Zone | Mean vBMD (mg HA/cm³) | Std Dev | Volume (cm³) | Low-Density Bone (%) |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for z_name, d in z_stats.items():
                f.write(f"| {z_name} | {d['mean_vbmd']} | ±{d['std_vbmd']} | {d['volume_cm3']} | {d['pct_resorbed_low_density']}% |\n")

            f.write("\n## 2. Radial Distance-Isochrone Shells (Interface Fixation)\n\n")
            f.write("| Shell | Mean vBMD (mg HA/cm³) | Std Dev | Volume (cm³) | Low-Density Bone (%) |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for s_name, d in s_stats.items():
                f.write(f"| {s_name} | {d['mean_vbmd']} | ±{d['std_vbmd']} | {d['volume_cm3']} | {d['pct_resorbed_low_density']}% |\n")

            if longitudinal:
                f.write("\n## 3. Longitudinal Remodeling Comparison (Follow-up vs. Baseline)\n\n")
                f.write("| Region | Baseline (mg/cm³) | Follow-up (mg/cm³) | Change (%) | Status |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- |\n")
                long_zones = longitudinal.get("anatomical_zones", {})
                for reg_name, l_data in long_zones.items():
                    f.write(
                        f"| {reg_name} | {l_data['baseline_vbmd']} | {l_data['followup_vbmd']} | "
                        f"{l_data['pct_change']}% | `{l_data['classification']}` |\n"
                    )

            f.write("\n---\n*Report generated automatically by Antigravity Quantitative TKA Bone Density Pipeline.*\n")

        return md_path

    def render_density_overlays(
        self,
        volume_hu: np.ndarray,
        vbmd_volume: np.ndarray,
        metal_mask: np.ndarray,
        cement_mask: np.ndarray,
        slice_z: int,
        slice_y: int,
        slice_x: int,
        patient_id: str
    ) -> str:
        """
        Generates a 3-panel orthogonal view (axial, coronal, sagittal) with vBMD heatmaps.
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        views = [
            ("Axial (Z)", volume_hu[slice_z, :, :], vbmd_volume[slice_z, :, :], metal_mask[slice_z, :, :], cement_mask[slice_z, :, :]),
            ("Coronal (Y)", volume_hu[:, slice_y, :], vbmd_volume[:, slice_y, :], metal_mask[:, slice_y, :], cement_mask[:, slice_y, :]),
            ("Sagittal (X)", volume_hu[:, :, slice_x], vbmd_volume[:, :, slice_x], metal_mask[:, :, slice_x], cement_mask[:, slice_x])
        ]

        for ax, (title, hu_slice, v_slice, m_slice, c_slice) in zip(axes, views):
            # Base CT in grayscale
            ax.imshow(hu_slice, cmap="gray", vmin=-200, vmax=1400)
            
            # Bone Density Overlay
            v_masked = np.ma.masked_where(v_slice <= 10.0, v_slice)
            im = ax.imshow(v_masked, cmap="jet", alpha=0.55, vmin=50, vmax=800)
            
            # Metal Contour (White)
            ax.contour(m_slice, levels=[0.5], colors=["white"], linewidths=1.2)
            
            # Cement Contour (Cyan)
            if np.any(c_slice):
                ax.contour(c_slice, levels=[0.5], colors=["cyan"], linewidths=1.0)

            ax.set_title(title, fontsize=12, fontweight="bold")
            ax.axis("off")

        fig.subplots_adjust(right=0.88)
        cbar_ax = fig.add_axes([0.90, 0.20, 0.02, 0.60])
        cbar = fig.colorbar(im, cax=cbar_ax)
        cbar.set_label("vBMD (mg HA/cm³)", fontsize=11)

        img_path = os.path.join(self.output_dir, f"{patient_id}_radiological_density_overlay.png")
        plt.savefig(img_path, dpi=200, bbox_inches="tight")
        plt.close()
        return img_path
