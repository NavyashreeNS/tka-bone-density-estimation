# Biomechanical Finite Element (FEA) Engine

## Objective
Automatically translate patient-specific calibrated volumetric bone mineral density ($v\text{BMD}$) fields into heterogeneous 3D tetrahedral finite element meshes, assign empirical constitutive material properties, and export ready-to-run input decks for open-source and commercial solvers.

## Core Capabilities
- **Mesh Generation**: Discretizes bone, cement, and implant volumes into 4-node tetrahedral elements (`C3D4` / `tet4`).
- **Material Assignment**:
  - Bone: Density-dependent Young's modulus using Morgan & Keaveny (2001):
    $$E_i = 3790 \cdot (\rho_{\text{ash}, i})^{2.18} \quad [\text{MPa}]$$
  - Implant: CoCrMo ($E = 210\text{ GPa}$, $\nu = 0.3$) or Ti6Al4V ($E = 110\text{ GPa}$, $\nu = 0.3$).
  - Cement: PMMA ($E = 2.5\text{ GPa}$, $\nu = 0.35$).
- **Boundary & Loading Conditions**:
  - Distal diaphysis cut surface: Encastre fixed constraint ($U_x = U_y = U_z = 0$).
  - Proximal plateau: ISO 14243 peak axial compressive load ($2600\text{ N}$).
- **Supported Solvers**:
  - `FEBio` XML (`.feb`) for biomechanical research simulation.
  - `Abaqus` / `CalculiX` (`.inp`) for structural mechanics and micromotion analysis.
