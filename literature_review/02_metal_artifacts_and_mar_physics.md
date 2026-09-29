# 02: Physics of Metal Artifacts and Artifact Reduction in CT

## 1. Physical Mechanisms of Artifact Generation
In diagnostic CT ($80\text{--}140\text{ kVp}$), the total linear attenuation coefficient $\mu(E)$ is governed by photoelectric absorption ($\propto Z^3 / E^3$) and Compton scattering ($\propto \rho_e$).

### 1.1 Beam Hardening
Polychromatic X-rays traversing high-atomic-number implant metals encounter extreme attenuation:
$$\mu_{\text{effective}} = -\frac{1}{L} \ln \left( \frac{\int I_0(E) e^{-\int \mu(x,y,z; E) ds} dE}{\int I_0(E) dE} \right)$$
Because lower-energy photons are preferentially absorbed, the remaining beam becomes "harder" (higher effective mean energy). Standard filtered back-projection (FBP) assumes a monochromatic beam, causing underestimation of attenuation coefficients along rays passing through metal. This manifests as:
- Dark streaks connecting dense metal components (e.g., between femoral condylar lugs or tibial keel fins).
- Artificial "cupping" across adjacent trabecular bone, mimicking localized osteolysis.

### 1.2 Photon Starvation
Along thick metal axes (e.g., mediolateral trajectory through a cobalt-chromium femoral component), the transmitted X-ray flux drops below the electronic noise threshold of the detector ($I \approx 0$). In the logarithmic transformation $p = -\ln(I/I_0)$, extreme noise propagation produces sharp, alternating dark and bright streaks across the entire field of view.

### 1.3 Partial Volume Blooming
Because detector elements have finite spatial apertures ($0.5\text{--}0.7\text{ mm}$), voxels intersecting the boundary between metal ($\mu \sim 2.8\text{ cm}^{-1}$) and trabecular bone ($\mu \sim 0.25\text{ cm}^{-1}$) receive an averaged intermediate attenuation. The thresholded metal boundary artificially expands outwards ("blooming"), cannibalizing up to $1.0\text{ mm}$ of genuine peri-implant bone.

---

## 2. Metal Artifact Reduction (MAR) Algorithms

```
                          MAR ALGORITHM CLASSIFICATION
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
Sinogram Inpainting            Iterative Reconstruction       Deep Learning Dual-Domain
(e.g., NMAR)                  (e.g., TV-MBIR, ASiR-V)        (e.g., DuDoNet, ADN)
• Meyer et al. (2010)         • Penalized likelihood         • Lin et al. (2019)
• Forward-project metal mask  • Model exact physical system  • End-to-end sinogram &
• Normalize by prior image    • De-weight starved rays         image domain learning
• Interpolate missing shadow  • High edge preservation       • Physics consistency loss
```

### 2.1 Normalized Metal Artifact Reduction (NMAR)
Proposed by Meyer et al. (*Med Phys*, 2010), NMAR prevents the interpolation errors typical of standard linear sinogram inpainting:
1. Segment metallic structures in initial reconstruction $I_{\text{initial}}$ at threshold $\tau \ge 3000\text{ HU}$.
2. Forward-project metal mask to delineate the corrupted sinogram shadow $S_{\text{metal}}(\theta, s)$.
3. Construct a simplified prior image $I_{\text{prior}}$ containing only segmented air, soft tissue, and bone with assigned theoretical attenuation values.
4. Forward-project $I_{\text{prior}}$ to obtain prior sinogram $P_{\text{prior}}$.
5. Compute normalized sinogram:
   $$P_{\text{norm}}(\theta, s) = \frac{P_{\text{meas}}(\theta, s)}{P_{\text{prior}}(\theta, s)}$$
6. Perform 1D or 2D spline interpolation exclusively over $S_{\text{metal}}(\theta, s)$ on $P_{\text{norm}}$.
7. Re-multiply by $P_{\text{prior}}(\theta, s)$ and reconstruct using FBP or iterative algorithms.
* **Quantitative Accuracy**: Reduces streak-induced density error from $\pm 350\text{ HU}$ to within $\pm 45\text{ HU}$ in peri-implant regions ($> 1\text{ mm}$ from metal).

### 2.2 Model-Based Iterative Reconstruction (MBIR) with Total Variation (TV)
Rather than discarding metal projections, TV-MBIR solves:
$$\hat{\mu} = \arg\min_\mu \left\{ \frac{1}{2} \| W (y - A \mu) \|_2^2 + \lambda \|\nabla \mu\|_1 \right\}$$
where $W_{ii} = \exp(-y_i)$ heavily down-weights photon-starved rays without setting them to zero. TV regularization preserves sharp cortical edges while eliminating noise streaks in homogeneous trabecular bone.

### 2.3 Virtual Monochromatic Imaging (VMI) via Dual-Energy CT
Bamberg et al. (2011) showed that VMI synthesized at high photon energies ($110\text{--}150\text{ keV}$) effectively extinguishes beam hardening artifacts because the monochromatic energy reconstruction mathematically decouples photoelectric and Compton interactions. However, contrast-to-noise ratio (CNR) for cancellous bone decreases at high keV, requiring recalibration of HU-to-density conversion equations.
