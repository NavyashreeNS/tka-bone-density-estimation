"""
Comprehensive Unit & Integration Test Suite for TKA Bone Density Pipeline
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
from synthetic_data.generate_synthetic_tka_dataset import generate_synthetic_tka_scan

class TestTKABoneDensityPipeline(unittest.TestCase):

    def setUp(self):
        self.validator = AcquisitionProtocolValidator()
        self.calibrator = DensityCalibrationEngine()
        self.segmenter = MultiClassSegmenter()
        self.analyzer = ZonalDensityAnalyzer()
        self.biomech = BiomechanicalAnalyzer()

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
        # Perfectly linear points: vBMD = 0.5 * HU + 25
        hus = [-50.0, 50.0, 150.0, 350.0, 750.0]
        densities = [0.0, 50.0, 100.0, 200.0, 400.0]
        res = self.calibrator.calibrate_from_phantom(hus, densities)
        self.assertGreater(res["r_squared"], 0.99)
        # Test conversion: 150 HU -> 100 mg/cm3
        converted = self.calibrator.convert_hu_to_vbmd(np.array([150.0]))
        self.assertAlmostEqual(converted[0], 100.0, delta=1.0)

    def test_stage4_multiclass_segmentation(self):
        mock_vol = np.full((10, 20, 20), -900.0, dtype=np.float32)
        # Add bone
        mock_vol[:, 5:15, 5:15] = 200.0
        # Add cortex
        mock_vol[:, 4:6, :] = 900.0
        # Add metal
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
        # Morgan & Keaveny: E = 3790 * (rho_ash)^2.18
        # for 200 mg/cm3 (0.2 g/cm3 ash): 3790 * 0.2^2.18 approx 113 MPa
        self.assertGreater(e_mod[0], 50.0)
        self.assertLess(e_mod[0], 250.0)
        # Cortical: 1000 mg/cm3 (1.0 g/cm3): approx 3790 MPa
        self.assertGreater(e_mod[1], 3000.0)

    def test_end_to_end_synthetic_pipeline(self):
        vol, gt, meta = generate_synthetic_tka_scan(dim=(16, 32, 32))
        self.assertEqual(vol.shape, (16, 32, 32))
        self.assertIn("PatientID", meta)

if __name__ == "__main__":
    unittest.main()
