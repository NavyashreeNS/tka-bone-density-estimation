# Interactive 3D Visualization & 3D Slicer Integration

## Objective
Provide intuitive, web-based 3D visual exploration and clinical workstation integration for orthopedic surgeons, biomechanical engineers, and radiologists.

## Components
1. **Interactive 3D HTML Dashboard (`interactive_viewer.py`)**:
   - Generates standalone, self-contained 3D HTML files powered by Plotly and WebGL.
   - Interactive 3D orbital rotation, pan, zoom, and distance inspection.
   - Dual-layer visualization:
     - Metallic prosthesis (CoCrMo baseplate and central keel fins).
     - Full 3D scalar density point cloud / isosurface color-coded by $v\text{BMD}$ ($\text{mg HA/cm}^3$).
   - Can be opened instantly in any browser without installing software.
2. **3D Slicer Extension (`slicer_tka_density_module.py`)**:
   - Native Python scripted module for the open-source 3D Slicer medical platform (`slicer.org`).
   - Automatically loads DICOM Parametric Maps, applies calibrated Rainbow/Jet color lookup tables, and links orthogonal axial, coronal, and sagittal cross-sections.
