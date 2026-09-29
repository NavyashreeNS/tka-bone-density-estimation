# Stage 4 Milestone: Multi-Class Segmentation Engine

## Objective
Accurately segment high-density metallic components, PMMA bone cement, cortical bone, and trabecular bone into distinct non-overlapping label volumes while suppressing partial volume blooming at implant boundaries.

## Classes Delineated
- **Class 0**: Background / Soft Tissue
- **Class 1**: Metallic Prosthesis (CoCrMo, Ti6Al4V)
- **Class 2**: PMMA Bone Cement (spatially constrained to within $0\text{--}4\text{ mm}$ of metal)
- **Class 3**: Trabecular Bone Bed ($50\text{--}650\text{ HU}$)
- **Class 4**: Cortical Bone Shell ($\ge 650\text{ HU}$)

## Distance-Isochrone Shell Generation
Using 3D Euclidean Distance Transforms, concentric shells around the implant surface are extracted:
- **Shell A**: $0.0\text{--}0.5\text{ mm}$ (Interface zone)
- **Shell B**: $0.5\text{--}1.0\text{ mm}$
- **Shell C**: $1.0\text{--}2.0\text{ mm}$
- **Shell D**: $2.0\text{--}3.0\text{ mm}$
- **Shell E**: $3.0\text{--}5.0\text{ mm}$ (Baseline host bone)
