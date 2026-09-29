# 04: Advanced Segmentation and Longitudinal Registration Methods

## 1. Multi-Class Segmentation Challenges in TKA

```
              ANATOMICAL & MATERIAL DISCRIMINATION CHALLENGE
┌─────────────────────────┬──────────────────────┬───────────────────────────────┐
│ Material / Structure    │ Typical Attenuation  │ Segmentation Challenge        │
├─────────────────────────┼──────────────────────┼───────────────────────────────┤
│ CoCrMo / Ti6Al4V Alloy  │ > 3000 HU            │ Blooming expands boundaries   │
│ PMMA Bone Cement        │ 120 – 300 HU         │ Direct overlap with bone      │
│ Trabecular Cancellous   │ 50 – 350 HU          │ Directly overlaps with cement │
│ Cortical Bone Shell     │ 800 – 1800 HU        │ Thin walls blur via PVE       │
└─────────────────────────┴──────────────────────┴───────────────────────────────┘
```

### 1.1 CAD Model-to-Image Surface Registration
To prevent threshold-induced blooming from artificially cannibalizing $0.5\text{--}1.5\text{ mm}$ of bone, the manufacturer's CAD surface mesh ($\mathcal{S}_{\text{CAD}}$) is registered to the image volume:
1. Estimate rough orientation from the principal moments of inertia of the metal cluster.
2. Formulate optimization:
   $$\hat{\mathbf{T}} = \arg\min_{\mathbf{T}} \int_{\mathcal{S}_{\text{CAD}}} \left| \nabla I(\mathbf{T}(\mathbf{p})) \cdot \mathbf{n}(\mathbf{p}) \right|^{-1} ds$$
   maximizing the image gradient magnitude along surface normal vectors.
3. Compute signed distance field $\Phi(\mathbf{x}) = \text{dist}(\mathbf{x}, \mathbf{T}(\mathcal{S}_{\text{CAD}}))$ to establish sub-millimeter boundary definitions.

### 1.2 Cortical Bone Mapping (Stradwin Edge Profiling)
Treece et al. (2010) developed cortical bone mapping to overcome partial volume overestimation of cortical thickness ($Ct.Th$). By sampling 1D perpendicular profiles across the cortical shell and fitting an idealized model (a box function convolved with a Gaussian point spread function), the exact endosteal and periosteal boundaries are resolved even when $Ct.Th$ is less than the scanner point-spread function ($\approx 1\text{ mm}$).

### 1.3 PMMA Cement Separation via Deep Spatial Priors
Because radiopaque PMMA cement overlaps with trabecular bone in intensity, semantic 3D U-Net segmentation must be constrained with anatomical spatial priors:
- The cement layer is restricted to a $0\text{--}4\text{ mm}$ shell around the non-articulating surfaces of the implant.
- Voxels outside this spatial envelope are constrained to $\mathcal{M}_{\text{cement}} = 0$.

---

## 2. Longitudinal Registration Without Density Degradation
In longitudinal studies tracking bone remodeling over 1, 2, and 5 years:
- **Resampling Artifacts**: Trilinear or spline interpolation of follow-up volumes onto baseline grids blurs high-frequency trabecular edges and lowers peak densities.
- **Diaphyseal Cortical Anchoring**: The surgical resection zone and peri-implant metaphyseal bone undergo remodeling and cannot serve as registration targets. Registration is strictly anchored to the unoperated distal/diaphyseal cortical bone ($> 8\text{ cm}$ from the joint line).
- **Inverse Coordinate Mapping**: The spatial transformation $\mathbf{T}_{t \to t_0}$ is inverted ($\mathbf{T}_{t \to t_0}^{-1}$); region-of-interest masks are transformed to native follow-up coordinate space, ensuring density measurements are always computed directly on raw, un-interpolated voxels.
