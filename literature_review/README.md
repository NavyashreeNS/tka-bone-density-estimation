# Comprehensive Literature Review: Quantitative Bone Density Estimation in TKA

## Overview
This directory contains a rigorous, multi-thematic critical literature review supporting the end-to-end patient-specific quantitative bone density estimation pipeline around Total Knee Arthroplasty (TKA) implants.

## Thematic Document Structure

1. **[01_imaging_modalities_and_qct.md](01_imaging_modalities_and_qct.md)**:
   - Comparative physics and clinical performance of DXA, QCT, pQCT, HR-pQCT, DECT, and SPECT/CT.
   - Analysis of projection overlap vs. true 3D volumetric density ($v\text{BMD}$).
   - Dose profiles and clinical trade-offs.

2. **[02_metal_artifacts_and_mar_physics.md](02_metal_artifacts_and_mar_physics.md)**:
   - Detailed mathematical physics of X-ray interactions with high-atomic-number metals ($Z_{\text{Co}}=27, Z_{\text{Cr}}=24, Z_{\text{Ti}}=22$).
   - Beam hardening, photon starvation, scatter, and partial volume blooming.
   - Evaluation of projection MAR (NMAR), iterative model-based reconstruction (MBIR), high-energy virtual monochromatic imaging (VMI), and deep learning (DuDoNet/ADN).

3. **[03_density_calibration_and_standards.md](03_density_calibration_and_standards.md)**:
   - Synchronous physical phantom standards (Cann-Genant, Mindways solid HA).
   - Asynchronous and patient-internal tissue reference calibration (fat, muscle, cortical bone).
   - Mathematical formulation of sub-voxel partial volume correction at metal interfaces.

4. **[04_segmentation_and_registration.md](04_segmentation_and_registration.md)**:
   - Manufacturer CAD registration using signed distance fields (SDF) to eliminate blooming.
   - Spatial-prior deep learning for PMMA bone cement vs. osteopenic bone separation.
   - Anatomical landmark anchoring on the tibial and femoral diaphysis for zero-interpolation longitudinal tracking.

5. **[05_biomechanics_and_constitutive_laws.md](05_biomechanics_and_constitutive_laws.md)**:
   - Power-law density-to-elasticity relationships (Carter & Hayes, Keller, Keyak, Morgan & Keaveny).
   - Strain adaptive bone remodeling theory (Huiskes) and ISO 14243 biomechanical load cases.
   - Calculation of interfacial shear, micromotion thresholds, and stress shielding risk.

6. **[06_zonal_classification_and_clinical_outcomes.md](06_zonal_classification_and_clinical_outcomes.md)**:
   - Evolution from 2D planar Gruen and Ewald/Kozinn zones to 3D volumetric partitions.
   - Concentric radial distance shells ($0\text{--}0.5\text{ mm}$, $0.5\text{--}1\text{ mm}$, $1\text{--}2\text{ mm}$, $2\text{--}3\text{ mm}$, $3\text{--}5\text{ mm}$).
   - Radiostereometric Analysis (RSA) migration correlation and aseptic loosening failure mechanisms.

7. **[references.bib](references.bib)**:
   - Complete BibTeX bibliography referencing key publications.

## Key Research Gaps Addressed by this Pipeline

| Gap ID | Identified Clinical / Technical Limitation | Literature Evidence | Proposed Pipeline Solution |
| :--- | :--- | :--- | :--- |
| **GAP-1** | **Interface Blindness ($0\text{--}1.5\text{ mm}$)**: Standard QCT discards the immediate bone interface due to blooming and beam hardening streaks. | Stilling et al. (2012), Nazarian et al. (2008) | CAD-guided signed distance field alignment combined with sub-voxel partial volume fraction correction. |
| **GAP-2** | **PMMA Cement vs. Bone Conflation**: Radiopaque bone cement ($\text{HU} \approx 120\text{--}300$) directly overlaps with osteopenic trabecular bone. | van Loon et al. (2001) | Spatial-prior constrained 3D U-Net restricting PMMA to within $3\text{ mm}$ of implant contact surfaces. |
| **GAP-3** | **Longitudinal Re-slicing Degradation**: Multi-time-point scans resampled to a common grid suffer from trilinear smoothing of trabecular peaks. | Treece et al. (2010) | Inverse coordinate mapping: project 3D ROIs backward into native scan space without re-interpolating scalar density fields. |
| **GAP-4** | **Arbitrary 2D Zonal Projections**: Planar regions are inconsistently extended into 3D, impeding multi-center data pooling. | Ewald (1989), Petersen (1995) | Standardized 7-zone volumetric partition combined with radial distance isochrone shells. |
