"""
End-to-End Quantitative TKA Bone Mineral Density Estimation Pipeline
Orchestrates Stages 1 through 8, delivering patient-specific volumetric BMD mapping,
longitudinal remodeling classification, DICOM PACS export, FEA biomechanical decks,
and interactive 3D web dashboards.
"""

import sys
import os
import json
import numpy as np

# Ensure sub-stage packages are in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from stage1_data_acquisition.acquisition_protocol import AcquisitionProtocolValidator
from stage2_metal_artifact_reduction.mar_reconstruction import MetalArtifactReducer
from stage3_image_registration.registration_engine import AnatomicalRegistrationEngine
from stage4_multiclass_segmentation.segmentation_engine import MultiClassSegmenter
from stage5_density_calibration.calibration_engine import DensityCalibrationEngine
from stage6_density_mapping_zonal.zonal_analyzer import ZonalDensityAnalyzer
from stage7_biomechanical_analysis.biomechanical_model import BiomechanicalAnalyzer
from stage8_visualization_reporting.report_generator import QuantitativeReportGenerator
from dicom_engine.dicom_io import DicomIOEngine
from fea_engine.fea_exporter import FEAMeshExporter
from dashboard.interactive_viewer import Interactive3DDashboard

class TKABoneDensityPipeline:
    """
    Main orchestrator for patient-specific quantitative bone density estimation in TKA.
    """

    def __init__(self, output_dir: str = None):
        if output_dir is None:
            output_dir = os.path.join(BASE_DIR, "output")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.validator = AcquisitionProtocolValidator()
        self.mar = MetalArtifactReducer(metal_threshold_hu=2800.0)
        self.registrar = AnatomicalRegistrationEngine(diaphyseal_cutoff_slice=18)
        self.segmenter = MultiClassSegmenter()
        self.calibrator = DensityCalibrationEngine()
        self.analyzer = ZonalDensityAnalyzer(voxel_spacing_mm=[0.6, 0.4, 0.4])
        self.biomech = BiomechanicalAnalyzer(precision_error_cv=1.5)
        self.reporter = QuantitativeReportGenerator(output_dir=self.output_dir)
        self.dicom_io = DicomIOEngine()
        self.fea_exporter = FEAMeshExporter(voxel_size_mm=[0.6, 0.4, 0.4])
        self.dashboard = Interactive3DDashboard(output_dir=self.output_dir)

    def run_single_time_point(
        self,
        volume_hu: np.ndarray,
        metadata: dict,
        apply_mar: bool = False,
        export_dicom: bool = True,
        export_fea: bool = True,
        export_3d_html: bool = True
    ) -> dict:
        """
        Processes a single CT acquisition (e.g. baseline post-op or follow-up).
        """
        patient_id = metadata.get("PatientID", "UNKNOWN_PATIENT")
        study_date = metadata.get("StudyDate", "2026-09-29")

        print(f"\n========================================================")
        print(f" Processing Scan: {patient_id} ({study_date})")
        print(f"========================================================")

        # STAGE 1: Protocol Validation
        print("[Stage 1] Validating DICOM metadata & acquisition parameters...")
        valid, val_report = self.validator.validate_metadata(metadata)
        if not valid:
            print(f"  [WARN] Protocol validation failed: {val_report['errors']}")
        else:
            print(f"  [OK] Valid protocol. Effective dose: {val_report['effective_dose_msv']} mSv")

        # STAGE 2: Metal Artifact Reduction
        recon_hu = volume_hu.copy()
        mar_report = {"applied": apply_mar}
        if apply_mar:
            print("[Stage 2] Running Normalized Metal Artifact Reduction (NMAR)...")
            recon_hu, mar_metrics = self.mar.process_volume(volume_hu)
            mar_report["metrics"] = mar_metrics
            print(f"  [OK] MAR complete across {volume_hu.shape[0]} slices.")
        else:
            print("[Stage 2] Skipping full projection MAR (using reconstructed volume).")

        # STAGE 4: Multi-Class Segmentation
        print("[Stage 4] Performing multi-class segmentation (Metal, PMMA, Cortex, Trabeculae)...")
        label_map, voxel_counts = self.segmenter.segment_volume(recon_hu, is_cemented=True)
        metal_mask = label_map == 1
        cement_mask = label_map == 2
        trabecular_mask = label_map == 3
        cortical_mask = label_map == 4
        bone_mask = trabecular_mask | cortical_mask
        print(f"  [OK] Segmentation finished. Bone voxels: {np.sum(bone_mask)}, Metal: {np.sum(metal_mask)}")

        # STAGE 3: Anatomical Coordinate Definition
        print("[Stage 3] Establishing diaphyseal anatomical coordinate frame...")
        anat_frame = self.registrar.define_anatomical_frame(bone_mask)
        print(f"  [OK] Origin: {[round(c, 1) for c in anat_frame['origin']]}")

        # STAGE 5: Density Calibration & Partial Volume Correction
        print("[Stage 5] Calibrating CT attenuation (HU) to vBMD (mg HA/cm3)...")
        rods = metadata.get("PhantomRods", [])
        if rods and len(rods) >= 3:
            hus = [r["expected_hu"] for r in rods]
            dens = [r["concentration_mg_ha_cm3"] for r in rods]
            cal_info = self.calibrator.calibrate_from_phantom(hus, dens)
            print(f"  [OK] Phantom calibration: slope={cal_info['slope']:.5f}, R2={cal_info['r_squared']:.4f}")
        else:
            cal_info = self.calibrator.calibrate_from_internal_tissues()
            print(f"  [OK] Internal tissue calibration fallback used.")

        # Convert entire volume to vBMD
        raw_vbmd = self.calibrator.convert_hu_to_vbmd(recon_hu)
        # Apply boundary partial volume correction
        from scipy.ndimage import distance_transform_edt
        dist_mm = distance_transform_edt(~metal_mask) * 0.4
        corr_vbmd = self.calibrator.apply_partial_volume_correction(raw_vbmd, dist_mm)
        # Zero out non-bone regions
        corr_vbmd[~bone_mask] = 0.0

        # STAGE 6: 3D Zonal Mapping & Radial Distance Shells
        print("[Stage 6] Executing 3D zonal partitioning (7-Zone) & radial isochrones...")
        cy, cx = volume_hu.shape[1] // 2, volume_hu.shape[2] // 2
        zones_dict = self.analyzer.partition_tibial_zones(bone_mask, metal_mask, center_x=cx, center_y=cy)
        shells_dict = self.analyzer.partition_distance_shells(bone_mask, metal_mask)
        zonal_stats = self.analyzer.analyze_all_regions(corr_vbmd, zones_dict, shells_dict)
        print(f"  [OK] Zone 1 (Medial SubPlate) Mean vBMD: {zonal_stats['anatomical_zones']['Zone_1_Medial_SubPlate']['mean_vbmd']} mg/cm3")
        print(f"  [OK] Shell A (0-0.5 mm) Mean vBMD: {zonal_stats['distance_shells']['Shell_A_0.0_to_0.5mm']['mean_vbmd']} mg/cm3")

        # STAGE 7: Biomechanics
        print("[Stage 7] Mapping Young's Modulus & evaluating loosening risk...")
        e_modulus = self.biomech.density_to_modulus(corr_vbmd)
        lvi_metrics = self.biomech.compute_loosening_vulnerability_index(
            zonal_stats["distance_shells"]["Shell_A_0.0_to_0.5mm"]
        )
        print(f"  [OK] Clinical Risk: {lvi_metrics['clinical_risk_category']} (LVI = {lvi_metrics['loosening_vulnerability_index']})")

        # Package Result Payload
        payload = {
            "metadata": metadata,
            "validation": val_report,
            "segmentation": voxel_counts,
            "anatomical_frame": anat_frame,
            "calibration": cal_info,
            "zonal_analysis": zonal_stats,
            "biomechanics": {
                "max_modulus_mpa": float(np.max(e_modulus)),
                "mean_trabecular_modulus_mpa": float(np.mean(e_modulus[trabecular_mask])) if np.any(trabecular_mask) else 0.0,
                "loosening_vulnerability": lvi_metrics
            }
        }

        # STAGE 8: Visualization & Reports
        print("[Stage 8] Generating radiological density overlays and clinical reports...")
        slice_z = min(10, volume_hu.shape[0] - 1)
        slice_y = cy
        slice_x = cx
        img_path = self.reporter.render_density_overlays(
            recon_hu, corr_vbmd, metal_mask, cement_mask, slice_z, slice_y, slice_x, patient_id
        )
        json_path = self.reporter.generate_json_report(patient_id, study_date, payload)
        md_path = self.reporter.generate_markdown_report(patient_id, study_date, payload)

        artifacts = {
            "image_overlay": img_path,
            "json_report": json_path,
            "markdown_summary": md_path
        }

        # ADVANCED MODULE 1: Real DICOM Parametric Series Export
        if export_dicom:
            print("[DICOM Export] Exporting calibrated vBMD volume as DICOM series...")
            dicom_subfolder = os.path.join(self.output_dir, f"{patient_id}_DICOM_vBMD")
            dcm_files = self.dicom_io.export_vbmd_as_dicom_series(
                corr_vbmd, metadata, dicom_subfolder
            )
            artifacts["dicom_series_dir"] = dicom_subfolder
            print(f"  [OK] Exported {len(dcm_files)} DICOM slices to {dicom_subfolder}")

        # ADVANCED MODULE 2: Biomechanical FEA Meshing & Solver Input Decks
        if export_fea:
            print("[FEA Exporter] Generating 3D tetrahedral mesh and Abaqus/FEBio decks...")
            mesh_data = self.fea_exporter.generate_voxel_tetrahedral_mesh(
                label_map, corr_vbmd, subsample_stride=3
            )
            inp_path = os.path.join(self.output_dir, f"{patient_id}_biomechanical_model.inp")
            feb_path = os.path.join(self.output_dir, f"{patient_id}_biomechanical_model.feb")
            self.fea_exporter.export_abaqus_inp(mesh_data, inp_path)
            self.fea_exporter.export_febio_xml(mesh_data, feb_path)
            artifacts["fea_abaqus_inp"] = inp_path
            artifacts["fea_febio_xml"] = feb_path
            print(f"  [OK] FEA Mesh: {mesh_data['num_nodes']} nodes, {mesh_data['num_elements']} tets.")
            print(f"       Abaqus Deck: {inp_path}")
            print(f"       FEBio Deck:  {feb_path}")

        # ADVANCED MODULE 3: Interactive 3D Web Dashboard
        if export_3d_html:
            print("[3D Dashboard] Rendering interactive 3D WebGL dashboard...")
            html_path = self.dashboard.generate_interactive_3d_html(
                corr_vbmd, metal_mask, bone_mask, patient_id=patient_id
            )
            artifacts["interactive_3d_html"] = html_path
            print(f"  [OK] 3D Dashboard: {html_path}")

        payload["artifacts"] = artifacts
        payload["arrays"] = {
            "recon_hu": recon_hu,
            "corr_vbmd": corr_vbmd,
            "bone_mask": bone_mask,
            "metal_mask": metal_mask,
            "cement_mask": cement_mask,
            "e_modulus": e_modulus
        }
        return payload

    def run_longitudinal_study(
        self,
        baseline_scan: tuple,
        followup_scan: tuple
    ) -> dict:
        """
        Executes end-to-end longitudinal bone density tracking across two time points.
        """
        v_base, _, meta_base = baseline_scan
        v_foll, _, meta_foll = followup_scan

        # Process Baseline
        res_base = self.run_single_time_point(v_base, meta_base)

        # Process Follow-up
        res_foll = self.run_single_time_point(v_foll, meta_foll)

        # Coordinate Registration (Follow-up to Baseline)
        print("\n[Longitudinal Registration] Rigid alignment on diaphyseal cortical envelope...")
        T_matrix, T_inv, reg_metrics = self.registrar.register_rigid(
            res_base["arrays"]["bone_mask"],
            res_foll["arrays"]["bone_mask"]
        )
        print(f"  [OK] Diaphyseal registration complete. Determinant: {reg_metrics['determinant']:.4f}")

        # Compute Longitudinal Biological Remodeling
        print("[Longitudinal Analysis] Evaluating % delta vBMD against LSC threshold...")
        long_comp = self.biomech.analyze_longitudinal_change(
            res_base["zonal_analysis"],
            res_foll["zonal_analysis"]
        )

        res_foll["longitudinal_comparison"] = long_comp
        # Regenerate updated clinical reports with longitudinal tables
        self.reporter.generate_markdown_report(
            meta_foll["PatientID"], meta_foll["StudyDate"], res_foll
        )
        self.reporter.generate_json_report(
            meta_foll["PatientID"], meta_foll["StudyDate"], res_foll
        )

        print("\n========================================================")
        print(" LONGITUDINAL REMODELING SUMMARY (1-YEAR POST-OP)")
        print("========================================================")
        for z_name, d in long_comp["anatomical_zones"].items():
            print(f" {z_name:<30}: {d['baseline_vbmd']:>6.1f} -> {d['followup_vbmd']:>6.1f} mg/cm3 "
                  f"({d['pct_change']:>+6.2f}%) [{d['classification']}]")

        return {
            "baseline": res_base,
            "followup": res_foll,
            "registration": reg_metrics,
            "longitudinal_remodeling": long_comp
        }
