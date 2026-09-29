# Stage 2 Milestone: Metal Artifact Reduction (MAR) & Reconstruction

## Objective
Restore missing or degraded projection data caused by high-atomic-number TKA metallic components (CoCrMo, Ti6Al4V), eliminating severe beam hardening and photon starvation streaks while preserving peri-implant trabecular architecture.

## Algorithm: Normalized Metal Artifact Reduction (NMAR)
1. **Metal Mask Binarization**: Segment metallic pixels at $\text{HU} \ge 2800$.
2. **Prior Image Synthesis**: Classify the initial volume into air ($-1000\text{ HU}$), soft tissue ($+40\text{ HU}$), and bone ($+800\text{ HU}$), followed by Gaussian smoothing.
3. **Sinogram Normalization**: Forward-project the uncorrected data and divide by the forward-projected prior sinogram.
4. **Normalized Inpainting**: Interpolate over the metal shadow within the normalized sinogram using cubic/linear splines.
5. **De-Normalization & Reconstruction**: Multiply by the prior sinogram and reconstruct via Filtered Back-Projection (FBP).

## Key Metric
- **Artifact Variance Reduction ($\%$)**: Measures variance reduction in the immediate peri-implant zone ($0\text{--}5\text{ mm}$ around metal), targeting $> 60\text{--}80\%$ variance reduction.
