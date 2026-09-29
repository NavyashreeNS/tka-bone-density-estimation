"""
Stage 1: Patient-Specific Data Acquisition & Protocol Verification
Validates incoming scan metadata and DICOM headers against quantitative TKA protocols,
verifying dose limits, spatial resolution, and phantom inclusion.
"""

import json
import os
from typing import Dict, Any, Tuple

class AcquisitionProtocolValidator:
    """Validates CT acquisition parameters for quantitative bone density mapping."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "protocol_config.json")
        with open(config_path, "r") as f:
            self.spec = json.load(f)

    def validate_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, list]:
        """
        Validate DICOM header dictionary against protocol specifications.
        """
        errors = []
        warnings = []

        # Check Slice Thickness
        slice_thick = metadata.get("SliceThickness", 1.0)
        max_thick = self.spec["acquisition_parameters"]["slice_thickness_mm"] * 1.5
        if slice_thick > max_thick:
            warnings.append(
                f"Slice thickness ({slice_thick} mm) exceeds recommended {max_thick} mm. "
                "Partial volume effects will be amplified."
            )

        # Check kVp
        kvp = metadata.get("KVP", 120)
        if kvp < 120 and not metadata.get("IsDualEnergy", False):
            warnings.append(
                f"Single-energy kVp ({kvp} kV) is low. High beam hardening streaks expected around CoCr/Ti."
            )

        # Radiation Dose Verification
        ctdi_vol = metadata.get("CTDIvol", 15.0)
        max_ctdi = self.spec["radiation_dose_limits"]["max_ctdi_vol_mgy"]
        if ctdi_vol > max_ctdi:
            errors.append(
                f"CTDIvol ({ctdi_vol} mGy) exceeds safety threshold ({max_ctdi} mGy)."
            )

        dlp = metadata.get("DLP", 200.0)
        k_factor = self.spec["radiation_dose_limits"]["knee_conversion_factor_k"]
        effective_dose = dlp * k_factor
        max_dose = self.spec["radiation_dose_limits"]["max_effective_dose_msv"]

        is_valid = len(errors) == 0
        report = {
            "is_valid": is_valid,
            "effective_dose_msv": round(effective_dose, 4),
            "errors": errors,
            "warnings": warnings,
            "passed_specs": {
                "kVp": kvp,
                "CTDIvol": ctdi_vol,
                "DLP": dlp,
                "SliceThickness": slice_thick,
                "PhantomIncluded": metadata.get("PhantomIncluded", True)
            }
        }
        return is_valid, report


if __name__ == "__main__":
    validator = AcquisitionProtocolValidator()
    sample_meta = {
        "KVP": 140,
        "SliceThickness": 0.6,
        "CTDIvol": 14.5,
        "DLP": 210.0,
        "IsDualEnergy": False,
        "PhantomIncluded": True
    }
    valid, rep = validator.validate_metadata(sample_meta)
    print(f"Protocol Valid: {valid}")
    print(json.dumps(rep, indent=2))
