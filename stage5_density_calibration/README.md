# Stage 5 Milestone: Quantitative Density Calibration & Partial Volume Correction

## Objective
Convert raw CT attenuation numbers (Hounsfield Units, HU) to absolute physical volumetric Bone Mineral Density ($v\text{BMD}, \text{mg HA/cm}^3$) and correct boundary partial volume averaging.

## Calibration Modes
1. **Synchronous In-Scan Phantom (Primary)**:
   - High-precision linear regression: $v\text{BMD} = m \cdot \text{HU} + c$ using solid HA reference rods ($0, 50, 100, 200, 400\text{ mg/cm}^3$).
   - Fit criterion: $R^2 \ge 0.99$.
2. **Phantom-less Internal Tissue Fallback (Secondary)**:
   - Three-point regression anchored to subcutaneous fat ($0\text{ mg/cm}^3$), muscle ($5\text{ mg/cm}^3$), and intact diaphyseal cortex ($1200\text{ mg/cm}^3$).

## Interface Partial Volume Correction
Voxels within $0.0\text{--}1.0\text{ mm}$ of metal surfaces are corrected by estimating the sub-voxel bone fraction $\alpha \in [0.25, 1.0]$:
$$v\text{BMD}_{\text{corr}} = \frac{v\text{BMD}_{\text{meas}}}{\alpha}$$
preventing artificial bone loss or metal contamination at the direct contact interface.
