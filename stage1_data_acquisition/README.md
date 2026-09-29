# Stage 1 Milestone: Data Acquisition Protocol & Quality Control

## Objective
Establish and enforce a standardized, low-dose, high-penetration computed tomography acquisition protocol tailored for periprosthetic bone density quantification in TKA patients.

## Protocol Highlights
- **Scanner Type**: Multi-Detector CT ($\ge 64$ slices) or Dual-Energy CT (DECT).
- **Tube Voltage**: $140\text{ kVp}$ (Single Energy) or $80 / \text{Sn } 150\text{ kVp}$ (Dual Energy).
- **Collimation & Pitch**: Low pitch ($0.5\text{--}0.7$), thin detector collimation ($0.6\text{ mm}$).
- **Reconstruction Increment**: $0.4\text{ mm}$ overlapping slices to minimize partial volume staircase artifacts.
- **Dose Constrained**: Effective dose $\le 0.25\text{ mSv}$ ($k = 0.0008\text{ mSv}/(\text{mGy}\cdot\text{cm})$), allowing safe longitudinal scanning.
- **Physical Standards**: In-scan solid Calcium Hydroxyapatite phantom ($0, 50, 100, 200, 400\text{ mg HA/cm}^3$).

## Module Files
- `protocol_config.json`: Protocol definition parameters.
- `acquisition_protocol.py`: Automated validator for DICOM headers and radiation dose parameters.
