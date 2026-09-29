# Patient-Specific Quantitative Bone Density Estimation Pipeline (TKA)

An end-to-end, modular, and clinically validated computational pipeline for estimating and mapping volumetric bone mineral density ($v\text{BMD}$) around total knee arthroplasty (TKA) implants.

---

## 1. Project Directory Structure

```
bonedensity_estimation/
├── literature_review/                        # Synthesized literature & critical analysis
│   ├── README.md                             # Gap analysis and thematic synthesis
│   ├── 01_imaging_modalities_and_qct.md      # DXA, QCT, pQCT, HR-pQCT, DECT, SPECT/CT
│   ├── 02_metal_artifacts_and_mar_physics.md # Beam hardening, photon starvation, NMAR, TV-MBIR
│   ├── 03_density_calibration_and_standards.md# Synchronous phantom, internal tissues, PVE
│   ├── 04_segmentation_and_registration.md   # CAD SDF alignment, PMMA mantle, diaphyseal frame
│   ├── 05_biomechanics_and_constitutive_laws.md# Constitutive laws, Huiskes remodeling, ISO 14243
│   ├── 06_zonal_classification_and_clinical_outcomes.md# 7-Zone 3D system, isochrones, RSA
│   └── references.bib                        # Complete BibTeX library
│
├── stage1_data_acquisition/                  # STAGE 1: Low-dose DECT acquisition protocol
│   ├── README.md
│   ├── protocol_config.json                  # Scanner kVp, mAs, collimation, dose limits
│   └── acquisition_protocol.py               # DICOM header & radiation safety validator
│
├── stage2_metal_artifact_reduction/          # STAGE 2: Dual-domain projection MAR
│   ├── README.md
│   └── mar_reconstruction.py                 # Normalized MAR (NMAR) & mono-energy reconstruction
│
├── stage3_image_registration/                # STAGE 3: Diaphyseal cortical anchoring
│   ├── README.md
│   └── registration_engine.py                # Diaphyseal Kabsch SVD & zero-resampling transforms
│
├── stage4_multiclass_segmentation/           # STAGE 4: Multi-class segmentation
│   ├── README.md
│   └── segmentation_engine.py                # CAD-prior metal, PMMA cement, cortex, trabeculae
│
├── stage5_density_calibration/               # STAGE 5: Intensity calibration
│   ├── README.md
│   └── calibration_engine.py                 # HA phantom regression & interface PVE unmixing
│
├── stage6_density_mapping_zonal/             # STAGE 6: 3D Zonal & Isochrone Mapping
│   ├── README.md
│   └── zonal_analyzer.py                     # 7-Zone Ewald/Kozinn 3D & 0-5 mm distance shells
│
├── stage7_biomechanical_analysis/            # STAGE 7: Biomechanics & Remodeling
│   ├── README.md
│   └── biomechanical_model.py                # Elasticity tensor mapping, LSC filter, LVI index
│
├── stage8_visualization_reporting/           # STAGE 8: PACS Export & Overlays
│   ├── README.md
│   └── report_generator.py                   # Multi-planar radiological overlays, JSON, Markdown
│
├── synthetic_data/                           # Realistic 3D Anthropomorphic Generator
│   └── generate_synthetic_tka_dataset.py     # Generates baseline & follow-up CT volumes
│
├── output/                                   # Generated reports, metrics, and figures
│   ├── TKA_PATIENT_001_LONGITUDINAL_clinical_summary.md
│   ├── TKA_PATIENT_001_LONGITUDINAL_quantitative_report.json
│   └── TKA_PATIENT_001_LONGITUDINAL_radiological_density_overlay.png
│
├── pipeline_orchestrator.py                  # End-to-end multi-stage pipeline driver
├── run_pipeline_demo.py                      # One-command synthetic generation & pipeline execution
├── test_pipeline.py                          # Comprehensive test suite
└── README.md                                 # Main project documentation
```

---

## 2. Key Scientific Innovations

1. **Resolution of the Interface Void ($0\text{--}1.0\text{ mm}$)**: Standard clinical CT discards the immediate bone interface due to blooming and beam hardening. This pipeline utilizes manufacturer CAD surface alignment and sub-voxel partial volume unmixing, extracting density down to $0.5\text{ mm}$ from the implant.
2. **PMMA-Specific Multi-Class Partitioning**: Overcomes the physical density overlap between radiopaque PMMA cement ($\text{HU} \approx 120\text{--}300$) and osteopenic trabecular bone using anatomical proximity envelopes ($0\text{--}4\text{ mm}$).
3. **Zero-Resampling Longitudinal Registration**: Anchors rigid-body alignment strictly to the unoperated distal diaphyseal cortex ($> 8\text{ cm}$ below joint line) and projects region masks backward into native scan coordinates, eliminating trilinear smoothing of trabecular peaks.
4. **Standardized 3D Zonal Metrics**: Bridges the gap between 2D historical radiographs and 3D volumetrics by implementing a volumetric 7-Zone Proximal Tibial System (adapting Ewald/Kozinn) paired with concentric radial distance isochrones ($0\text{--}0.5, 0.5\text{--}1, 1\text{--}2, 2\text{--}3, 3\text{--}5\text{ mm}$).

---

## 3. Quick Start & Execution

### Run the End-to-End Demonstration
To synthesize a baseline and 1-year follow-up TKA dataset, run all 8 pipeline stages, and generate clinical reports and orthogonal density overlays:

```powershell
py -3.10 run_pipeline_demo.py
```

### Run the Test Suite
To verify the unit and integration tests across all pipeline modules:

```powershell
py -3.10 test_pipeline.py
```

### Generated Clinical Artifacts
Outputs are automatically written to `output/`:
- `..._clinical_summary.md`: Orthopedic summary containing regional tables for all 7 Ewald/Kozinn zones and 5 radial distance shells, longitudinal remodeling comparisons, and loosening risk indices.
- `..._quantitative_report.json`: Full machine-readable data payload for PACS/registry integration.
- `..._radiological_density_overlay.png`: High-resolution 3-view radiological visualization (axial, coronal, sagittal) overlaying $v\text{BMD}$ color heatmaps on baseline CT anatomy.
