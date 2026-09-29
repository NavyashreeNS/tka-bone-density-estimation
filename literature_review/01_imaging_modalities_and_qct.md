# 01: Quantitative Imaging Modalities in Total Knee Arthroplasty

## 1. Introduction & Physical Principles
Accurately assessing peri-implant bone mineral density (BMD) requires isolating cortical and trabecular compartments without corruption from metallic prostheses. 

### 1.1 Dual-Energy X-ray Absorptiometry (DXA)
DXA calculates areal bone mineral density ($\text{aBMD}, \text{g/cm}^2$) by transmitting two distinct effective energy spectra ($E_{\text{low}} \approx 40\text{--}45\text{ keV}$, $E_{\text{high}} \approx 70\text{--}100\text{ keV}$):
$$I(E) = I_0(E) \exp\left[ -\left( \left(\frac{\mu}{\rho}\right)_{\text{bone}}(E) \cdot M_{\text{bone}} + \left(\frac{\mu}{\rho}\right)_{\text{soft}}(E) \cdot M_{\text{soft}} \right) \right]$$
Solving the system yields $M_{\text{bone}} = \text{aBMD}$.
* **Clinical Findings**: Petersen et al. (1995) and van Loon et al. (2001) demonstrated significant early bone loss ($15\text{--}35\%$ within 6 to 12 months post-op) around tibial trays due to stress shielding.
* **Limitations**: DXA produces 2D projections, superimposing medial and lateral condyles, tibial keels, and cortical envelopes. True peri-implant bone within $1\text{--}3\text{ mm}$ of the implant is obscured by metal silhouettes.

### 1.2 Quantitative Computed Tomography (QCT)
QCT measures volumetric attenuation $\mu(x,y,z)$ and calibrates it against known chemical standards (calcium hydroxyapatite, $\text{HA}$, or dipotassium phosphate, $\text{K}_2\text{HPO}_4$):
$$v\text{BMD}(\mathbf{x}) = m \cdot \text{HU}(\mathbf{x}) + c \quad [\text{mg HA/cm}^3]$$
* **Advantages**: Full 3D spatial decomposition of cortical shell ($Ct.Th$, $v\text{BMD} \sim 800\text{--}1800\text{ mg/cm}^3$) from trabecular cancellous bone ($v\text{BMD} \sim 50\text{--}350\text{ mg/cm}^3$).
* **Limitations**: Polychromatic diagnostic X-ray spectra generate severe beam hardening and photon starvation artifacts around Cobalt-Chromium-Molybdenum (CoCrMo) and Titanium (Ti6Al4V) components.

### 1.3 High-Resolution Peripheral QCT (HR-pQCT)
HR-pQCT delivers isotropic resolution down to $61\text{--}82\ \mu\text{m}$, resolving individual trabeculae ($Tb.Th, Tb.Sp, Tb.N$).
* Stilling et al. (2012) tested HR-pQCT in periprosthetic knee specimens. They proved superior diagnostic sensitivity over DXA in uninstrumented bones; however, around primary metallic knee components, severe detector saturation and projection truncation produce catastrophic ring and streak artifacts that destroy segmentation within $3\text{ mm}$ of the implant.

### 1.4 Dual-Energy Computed Tomography (DECT)
DECT acquires two attenuation datasets at different energy spectra (e.g., $80\text{ kVp}$ and $140\text{ kVp}$ with tin filtering). Through two-material or three-material basis decomposition, DECT generates Virtual Monochromatic Images (VMI) at high energy levels ($110\text{--}150\text{ keV}$), suppressing beam hardening streaks and providing a stable baseline for density quantification.

### 1.5 SPECT/CT
Combines structural low-dose CT with metabolic gamma emission from osteotropic radiotracers ($^{99\text{m}}\text{Tc}\text{-HDP}$). While effective at detecting osteoblastic hyperactivity indicative of micro-instability, the spatial resolution of SPECT ($5\text{--}8\text{ mm}$) is insufficient for micro-structural density mapping.

## 2. Summary Comparison

| Modality | In-Plane Resolution | Volumetric Capability | Metal Artifact Impact | Typical Effective Dose |
| :--- | :--- | :--- | :--- | :--- |
| **DXA** | $0.5\text{--}1.0\text{ mm}$ | No (2D Projection) | Critical (Planar Superposition) | $< 0.01\text{ mSv}$ |
| **Clinical QCT** | $0.3\text{--}0.6\text{ mm}$ | Yes (3D) | High (Streaks, Blooming) | $1.5\text{--}3.5\text{ mSv}$ |
| **HR-pQCT** | $60\text{--}82\ \mu\text{m}$ | Yes (3D) | Extreme (Detector Saturation) | $< 0.05\text{ mSv}$ |
| **DECT (High VMI)**| $0.4\text{--}0.6\text{ mm}$ | Yes (3D) | Moderate-Low | $2.0\text{--}4.5\text{ mSv}$ |
| **SPECT/CT** | $5\text{--}8\text{ mm}$ (SPECT) | Yes (3D) | Moderate | $4.0\text{--}6.5\text{ mSv}$ |
