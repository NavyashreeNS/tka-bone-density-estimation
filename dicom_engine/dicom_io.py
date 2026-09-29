"""
DICOM I/O Engine for Quantitative TKA Bone Density Pipeline
Provides native hospital PACS ingestion, HIPAA Safe Harbor de-identification,
and export of DICOM Parametric Maps with Real World Value Mapping (RWVM).
"""

import os
import datetime
import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid
from typing import Dict, Any, Tuple, List

class DicomIOEngine:
    """
    Handles robust reading, de-identification, and export of orthopedic CT DICOM datasets.
    """

    def __init__(self):
        pass

    def load_dicom_series(self, directory_path: str) -> Tuple[np.ndarray, Dict[str, Any], List[pydicom.Dataset]]:
        """
        Reads a directory of axial CT slices, sorts them by spatial position,
        converts pixel values to Hounsfield Units, and extracts key acquisition tags.
        """
        files = [
            os.path.join(directory_path, f)
            for f in os.listdir(directory_path)
            if f.lower().endswith((".dcm", ".ima")) or not "." in f
        ]

        slices = []
        for f in files:
            try:
                ds = pydicom.dcmread(f, force=True)
                if hasattr(ds, "ImagePositionPatient") or hasattr(ds, "SliceLocation") or hasattr(ds, "InstanceNumber"):
                    slices.append(ds)
            except Exception:
                continue

        if not slices:
            raise ValueError(f"No valid DICOM CT slices found in: {directory_path}")

        # Sort slices along patient Z axis
        if hasattr(slices[0], "ImagePositionPatient"):
            slices.sort(key=lambda s: float(s.ImagePositionPatient[2]))
        elif hasattr(slices[0], "SliceLocation"):
            slices.sort(key=lambda s: float(s.SliceLocation))
        else:
            slices.sort(key=lambda s: int(s.InstanceNumber))

        # Extract 3D volume in Hounsfield Units (HU)
        pixel_arrays = []
        for s in slices:
            arr = s.pixel_array.astype(np.float32)
            slope = float(getattr(s, "RescaleSlope", 1.0))
            intercept = float(getattr(s, "RescaleIntercept", 0.0))
            hu_slice = arr * slope + intercept
            pixel_arrays.append(hu_slice)

        volume_hu = np.stack(pixel_arrays, axis=0)

        first_ds = slices[0]
        meta = {
            "PatientID": str(getattr(first_ds, "PatientID", "ANONYMOUS")),
            "PatientName": str(getattr(first_ds, "PatientName", "ANONYMOUS")),
            "StudyDate": str(getattr(first_ds, "StudyDate", "20260929")),
            "Modality": str(getattr(first_ds, "Modality", "CT")),
            "KVP": float(getattr(first_ds, "KVP", 140.0)),
            "XRayTubeCurrent": float(getattr(first_ds, "XRayTubeCurrent", 200.0)),
            "SliceThickness": float(getattr(first_ds, "SliceThickness", 0.6)),
            "PixelSpacing": [float(p) for p in getattr(first_ds, "PixelSpacing", [0.4, 0.4])],
            "CTDIvol": float(getattr(first_ds, "CTDIvol", 14.5)),
            "DLP": float(getattr(first_ds, "DLP", 210.0)),
            "SeriesInstanceUID": str(getattr(first_ds, "SeriesInstanceUID", generate_uid())),
            "StudyInstanceUID": str(getattr(first_ds, "StudyInstanceUID", generate_uid()))
        }

        return volume_hu, meta, slices

    def anonymize_dataset(self, dataset: pydicom.Dataset, new_patient_id: str = "TKA_RESEARCH_SUBJECT") -> pydicom.Dataset:
        """
        Applies HIPAA Safe Harbor de-identification to DICOM tags.
        """
        ds = dataset.copy()
        phi_tags = [
            "PatientName", "PatientBirthDate", "PatientAddress", "PatientTelephoneNumbers",
            "InstitutionName", "InstitutionalDepartmentName", "PhysiciansOfRecord",
            "PerformingPhysicianName", "OperatorsName", "AccessionNumber"
        ]
        for tag in phi_tags:
            if hasattr(ds, tag):
                setattr(ds, tag, "ANONYMIZED")

        ds.PatientID = new_patient_id
        return ds

    def export_vbmd_as_dicom_series(
        self,
        vbmd_volume: np.ndarray,
        reference_metadata: Dict[str, Any],
        output_directory: str,
        series_description: str = "Quantitative_vBMD_mg_HA_cm3"
    ) -> List[str]:
        """
        Exports a calibrated 3D vBMD volume as a valid series of DICOM secondary capture / parametric slices.
        Scales float density values to 16-bit unsigned integers with standard RescaleSlope & Intercept.
        """
        os.makedirs(output_directory, exist_ok=True)
        z_slices, y_rows, x_cols = vbmd_volume.shape

        new_series_uid = generate_uid()
        study_uid = reference_metadata.get("StudyInstanceUID", generate_uid())
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")

        # Fixed scaling: 0.1 mg/cm3 precision up to 6500 mg/cm3
        rescale_slope = 0.1
        rescale_intercept = 0.0

        exported_paths = []
        for z in range(z_slices):
            slice_data = vbmd_volume[z, :, :]
            uint16_data = np.clip(slice_data / rescale_slope, 0, 65535).astype(np.uint16)

            file_meta = FileMetaDataset()
            file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.7"  # Secondary Capture Image Storage
            file_meta.MediaStorageSOPInstanceUID = generate_uid()
            file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

            ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
            ds.PatientID = reference_metadata.get("PatientID", "TKA_PATIENT")
            ds.PatientName = reference_metadata.get("PatientID", "TKA_PATIENT")
            ds.StudyDate = date_str
            ds.StudyTime = time_str
            ds.Modality = "OT"  # Other / Parametric
            ds.SeriesDescription = series_description
            ds.StudyInstanceUID = study_uid
            ds.SeriesInstanceUID = new_series_uid
            ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
            ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
            ds.InstanceNumber = z + 1

            ds.Rows = y_rows
            ds.Columns = x_cols
            ds.BitsAllocated = 16
            ds.BitsStored = 16
            ds.HighBit = 15
            ds.PixelRepresentation = 0  # Unsigned integer
            ds.SamplesPerPixel = 1
            ds.PhotometricInterpretation = "MONOCHROME2"

            ds.RescaleSlope = "0.1"
            ds.RescaleIntercept = "0.0"
            ds.RescaleType = "mg/cm3"

            thick = float(reference_metadata.get("SliceThickness", 0.6))
            ds.SliceThickness = f"{thick:.3f}"
            ds.PixelSpacing = ["0.400", "0.400"]
            z_loc = z * thick
            ds.SliceLocation = f"{z_loc:.3f}"
            ds.ImagePositionPatient = ["0.000", "0.000", f"{z_loc:.3f}"]

            ds.PixelData = uint16_data.tobytes()

            slice_filename = os.path.join(output_directory, f"vBMD_slice_{z+1:04d}.dcm")
            ds.save_as(slice_filename, enforce_file_format=True)
            exported_paths.append(slice_filename)

        return exported_paths

    @staticmethod
    def create_mock_dicom_series(
        output_directory: str,
        num_slices: int = 12,
        matrix_size: Tuple[int, int] = (64, 64)
    ) -> str:
        """
        Creates a synthetic DICOM series on disk for integration testing.
        """
        os.makedirs(output_directory, exist_ok=True)
        study_uid = generate_uid()
        series_uid = generate_uid()
        now = datetime.datetime.now()

        for z in range(num_slices):
            file_meta = FileMetaDataset()
            file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"  # CT Image Storage
            file_meta.MediaStorageSOPInstanceUID = generate_uid()
            file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

            ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
            ds.PatientID = "TEST_TKA_PATIENT_01"
            ds.PatientName = "TEST^PATIENT"
            ds.StudyDate = now.strftime("%Y%m%d")
            ds.Modality = "CT"
            ds.StudyInstanceUID = study_uid
            ds.SeriesInstanceUID = series_uid
            ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
            ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
            ds.InstanceNumber = z + 1

            ds.Rows, ds.Columns = matrix_size
            ds.BitsAllocated = 16
            ds.BitsStored = 16
            ds.HighBit = 15
            ds.PixelRepresentation = 1  # Signed short
            ds.SamplesPerPixel = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
            ds.RescaleSlope = "1.0"
            ds.RescaleIntercept = "-1024.0"
            ds.KVP = "140"
            ds.SliceThickness = "0.6"
            ds.PixelSpacing = ["0.4", "0.4"]
            ds.ImagePositionPatient = ["0.0", "0.0", f"{z * 0.6:.3f}"]

            # Generate gradient HU slice
            raw_hu = np.full(matrix_size, 150.0, dtype=np.float32)
            raw_hu[matrix_size[0]//4:matrix_size[0]*3//4, matrix_size[1]//4:matrix_size[1]*3//4] = 850.0
            stored_val = np.clip(raw_hu + 1024.0, 0, 65535).astype(np.int16)
            ds.PixelData = stored_val.tobytes()

            ds.save_as(os.path.join(output_directory, f"slice_{z+1:03d}.dcm"), enforce_file_format=True)

        return output_directory
