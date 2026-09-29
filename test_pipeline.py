"""
Comprehensive Unit & Integration Test Suite for TKA Bone Density Pipeline
Tests Stages 1 through 8, DICOM I/O Engine, FEA Mesh Exporter, and Interactive Dashboard.
"""

import unittest
import numpy as np
import os
import sys

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
from synthetic_data.generate_synthetic_tka_dataset import generate_synthetic_tka_scan

class TestTKABoneDensityPipeline(unittest.TestCase):

    def setUp(self):
        self.validator = AcquisitionProtocolValidator()
        self.calibrator = DensityCalibrationEngine()
        self.segmenter = MultiClassSegmenter()
        self.analyzer = ZonalDensityAnalyzer()
        self.biomech = BiomechanicalAnalyzer()
        self.dicom_io = DicomIOEngine()
        self.fea_exporter = FEAMeshExporter()
        self.test_out_dir = os.path.join(BASE_DIR, "output", "test_artifacts")
        os.makedirs(self.test_out_dir, exist_ok=True)
        self.dashboard = Interactive3DDashboard(output_dir=self.test_out_dir)

    def test_stage1_protocol_validation(self):
        valid_meta = {
            "KVP": 140,
            "SliceThickness": 0.6,
            "CTDIvol": 12.0,
            "DLP": 180.0,
            "PhantomIncluded": True
        }
        is_valid, report = self.validator.validate_metadata(valid_meta)
        self.assertTrue(is_valid)
        self.assertLess(report["effective_dose_msv"], 0.25)

    def test_stage5_calibration_linearity(self):
        hus = [-50.0, 50.0, 150.0, 350.0, 750.0]
        densities = [0.0, 50.0, 100.0, 200.0, 400.0]
        res = self.calibrator.calibrate_from_phantom(hus, densities)
        self.assertGreater(res["r_squared"], 0.99)
        converted = self.calibrator.convert_hu_to_vbmd(np.array([150.0]))
        self.assertAlmostEqual(converted[0], 100.0, delta=1.0)

    def test_stage4_multiclass_segmentation(self):
        mock_vol = np.full((10, 20, 20), -900.0, dtype=np.float32)
        mock_vol[:, 5:15, 5:15] = 200.0
        mock_vol[:, 4:6, :] = 900.0
        mock_vol[:, 9:11, 9:11] = 3200.0

        label_map, counts = self.segmenter.segment_volume(mock_vol, is_cemented=True)
        self.assertIn("metal", counts)
        self.assertIn("cortical_bone", counts)
        self.assertGreater(counts["metal"], 0)

    def test_stage6_zonal_partitioning(self):
        bone_mask = np.ones((20, 20, 20), dtype=bool)
        metal_mask = np.zeros((20, 20, 20), dtype=bool)
        metal_mask[:5, 8:12, 8:12] = True
        bone_mask[metal_mask] = False

        zones = self.analyzer.partition_tibial_zones(bone_mask, metal_mask, center_x=10, center_y=10)
        self.assertEqual(len(zones), 7)
        self.assertIn("Zone_1_Medial_SubPlate", zones)
        self.assertIn("Zone_2_Lateral_SubPlate", zones)

    def test_stage7_constitutive_laws(self):
        vbmd = np.array([200.0, 1000.0], dtype=np.float32)
        e_mod = self.biomech.density_to_modulus(vbmd, model="morgan_keaveny_2001")
        self.assertGreater(e_mod[0], 50.0)
        self.assertLess(e_mod[0], 250.0)
        self.assertGreater(e_mod[1], 3000.0)

    def test_dicom_round_trip(self):
        mock_dir = os.path.join(self.test_out_dir, "mock_dicom")
        self.dicom_io.create_mock_dicom_series(mock_dir, num_slices=5, matrix_size=(32, 32))
        vol_hu, meta, slices = self.dicom_io.load_dicom_series(mock_dir)
        self.assertEqual(vol_hu.shape, (5, 32, 32))
        self.assertEqual(meta["Modality"], "CT")

        export_dir = os.path.join(self.test_out_dir, "exported_vbmd_dicom")
        exported_files = self.dicom_io.export_vbmd_as_dicom_series(vol_hu, meta, export_dir)
        self.assertEqual(len(exported_files), 5)
        self.assertTrue(os.path.exists(exported_files[0]))

    def test_fea_meshing_and_export(self):
        labels = np.zeros((6, 12, 12), dtype=np.uint8)
        labels[:, 3:9, 3:9] = 3  # Trabecular
        labels[:, 2:4, :] = 4   # Cortical
        labels[0:2, 5:7, 5:7] = 1 # Metal
        vbmd = np.full((6, 12, 12), 200.0, dtype=np.float32)

        mesh = self.fea_exporter.generate_voxel_tetrahedral_mesh(labels, vbmd, subsample_stride=1)
        self.assertGreater(mesh["num_nodes"], 0)
        self.assertGreater(mesh["num_elements"], 0)

        inp_path = os.path.join(self.test_out_dir, "test_model.inp")
        feb_path = os.path.join(self.test_out_dir, "test_model.feb")
        self.fea_exporter.export_abaqus_inp(mesh, inp_path)
        self.fea_exporter.export_febio_xml(mesh, feb_path)
        self.assertTrue(os.path.exists(inp_path))
        self.assertTrue(os.path.exists(feb_path))

    def test_interactive_dashboard_html_generation(self):
        vbmd = np.random.uniform(50, 800, size=(10, 20, 20)).astype(np.float32)
        metal = np.zeros((10, 20, 20), dtype=bool)
        metal[0:2, 8:12, 8:12] = True
        bone = np.ones((10, 20, 20), dtype=bool)
        bone[metal] = False

        html_path = self.dashboard.generate_interactive_3d_html(vbmd, metal, bone, patient_id="TEST_HTML_001")
        self.assertTrue(os.path.exists(html_path))
        self.assertGreater(os.path.getsize(html_path), 1000)

if __name__ == "__main__":
    unittest.main()
