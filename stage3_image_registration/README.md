# Stage 3 Milestone: Anatomical Frame Definition & Longitudinal Registration

## Objective
Establish an anatomical coordinate frame for the proximal tibia/distal femur and align longitudinal multi-time-point CT acquisitions without re-sampling or dampening the raw scalar bone density values.

## Key Methods
1. **Diaphyseal Cortical Bone Anchoring**: Excludes surgically altered joint compartments and focuses exclusively on undisturbed distal cortical bone ($> 8\text{ cm}$ below joint line).
2. **Kabsch Singular Value Decomposition (SVD)**: Derives optimal 3D rigid-body rotation $\mathbf{R}$ and translation $\mathbf{t}$ matrices.
3. **Zero-Resampling Rule**: The spatial transformation $\mathbf{T}_{t_1 \to t_0}$ is inverted to $\mathbf{T}^{-1}$. Region of interest (ROI) masks are mapped into follow-up space, guaranteeing that density analysis runs directly on native, un-interpolated voxels.
