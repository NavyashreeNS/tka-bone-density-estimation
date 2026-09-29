# DICOM I/O Engine

## Objective
Enable native integration with hospital Picture Archiving and Communication Systems (PACS), automated HIPAA Safe Harbor de-identification, and export of calibrated volumetric bone mineral density ($v\text{BMD}$) parametric maps.

## Features
- **PACS Ingestion**: Loads multi-slice axial CT series, sorts by `ImagePositionPatient`, scales pixel arrays by `RescaleSlope` and `RescaleIntercept` into true Hounsfield Units.
- **De-Identification**: Anonymizes patient identifiers, physician names, institutional names, and accession numbers in compliance with HIPAA Safe Harbor and GDPR Annex II.
- **Parametric Map Export**: Encapsulates 32-bit floating point calibrated densities ($\text{mg HA/cm}^3$) into 16-bit DICOM secondary capture / parametric map slices with valid Real World Value Mapping (`RWVM`), enabling loading and interactive HU/density probing in OsiriX, Horos, 3D Slicer, and clinical PACS viewers.
