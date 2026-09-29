# 03: Density Calibration Standards and Partial Volume Modeling

## 1. Quantitative CT Calibration Fundamentals
CT numbers in Hounsfield Units (HU) are scanner- and protocol-dependent:
$$\text{HU} = 1000 \times \left( \frac{\mu - \mu_{\text{water}}}{\mu_{\text{water}} - \mu_{\text{air}}} \right)$$
Because $\mu$ varies with X-ray tube potential, filtration, and patient size, HUs cannot be directly treated as absolute physical densities without calibration.

### 1.1 Synchronous In-Scan Phantom Calibration
First formalized by Cann & Genant (1980), synchronous calibration places solid reference standards directly beneath or adjacent to the patient during scanning:
- Standards: Calcium Hydroxyapatite ($\text{HA}$) or Dipotassium Hydrogen Phosphate ($\text{K}_2\text{HPO}_4$) at concentrations typically spanning $0, 50, 100, 200, 400\text{ mg/cm}^3$.
- Linear model:
  $$v\text{BMD}(\mathbf{x}) = m \cdot \text{HU}(\mathbf{x}) + c$$
  $$m = \frac{\text{Cov}(\text{HU}, \rho)}{\text{Var}(\text{HU})}, \quad c = \bar{\rho} - m \cdot \overline{\text{HU}}$$
- Precision: Yields long-term root-mean-square coefficient of variation ($\text{RMS-CV}$) $< 1.5\%$.

### 1.2 Phantom-less / Internal Tissue Reference Calibration
In retrospective or non-standardized clinical scans where a physical phantom is omitted, internal patient tissues serve as calibration anchors:
- Subcutaneous/Intramuscular Adipose Tissue: Assigned $\rho \approx 0\text{ mg HA/cm}^3$ ($\text{HU} \approx -100\text{ to } -80$).
- Deep Muscle / Vascular Blood Pool: Assigned $\rho \approx 5\text{ mg HA/cm}^3$ ($\text{HU} \approx +45\text{ to } +55$).
- Intact Cortical Baseline (Diaphyseal Cortex): Assigned population-adjusted cortical density ($\rho \approx 1150\text{--}1250\text{ mg HA/cm}^3$, $\text{HU} \approx 1200\text{--}1500$).
- Two-point or three-point linear fitting restores absolute density within an error margin of $\pm 5\text{--}8\%$.

---

## 2. Partial Volume Modeling at Metallic and Cement Boundaries
At the direct boundary between metallic implant and bone, partial volume averaging corrupts voxel intensities.

### 2.1 Sub-Voxel Volume Fraction Formulation
Let voxel $V_i$ contain fractions of metal ($\alpha_{\text{m}}$), bone ($\alpha_{\text{b}}$), and cement/soft tissue ($\alpha_{\text{s}}$), where $\alpha_{\text{m}} + \alpha_{\text{b}} + \alpha_{\text{s}} = 1$. The observed attenuation is:
$$\mu_{\text{obs}}(V_i) = \alpha_{\text{m}} \mu_{\text{metal}} + \alpha_{\text{b}} \mu_{\text{bone}} + \alpha_{\text{s}} \mu_{\text{soft}}$$
Because $\mu_{\text{metal}} \gg \mu_{\text{bone}}$, even a small metal fraction ($\alpha_{\text{m}} = 0.05$) inflates $\mu_{\text{obs}}$ drastically.

### 2.2 Sub-Voxel Marching-Cubes Over-Sampling
1. Fit nominal implant CAD geometry to the image volume using sub-voxel signed distance transforms.
2. For voxels within $1.0\text{ mm}$ of the CAD surface, sample an $8 \times 8 \times 8$ regular grid of point queries inside the voxel space.
3. Compute $\alpha_{\text{metal}} = \frac{N_{\text{inside}}}{512}$.
4. If $\alpha_{\text{metal}} > 0.75$, classify voxel as metal.
5. If $0.05 \le \alpha_{\text{metal}} \le 0.75$, subtract metal contribution:
   $$\text{HU}_{\text{corrected}} = \frac{\text{HU}_{\text{obs}} - \alpha_{\text{metal}} \text{HU}_{\text{metal}}}{1 - \alpha_{\text{metal}}}$$
6. If $1 - \alpha_{\text{metal}} < 0.25$, exclude voxel from quantitative density statistics to avoid excessive noise amplification.
