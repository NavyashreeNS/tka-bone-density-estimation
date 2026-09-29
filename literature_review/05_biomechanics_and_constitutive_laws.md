# 05: Biomechanics, Constitutive Laws, and Bone Remodeling

## 1. Density-to-Elasticity Relationships
In computational biomechanics and finite element modeling (FEA) of TKA, bone is modeled as an inhomogeneous continuum where Young's modulus $E$ and yield strength $\sigma_y$ are mapped directly from quantitative bone density.

```
+---------------------------------------------------------------------------------------+
| EMPIRICAL CONSTITUTIVE FORMULATIONS IN ORTHOPEDIC LITERATURE                           |
+---------------------------------------------------------------------------------------+
|                                                                                       |
| 1. Carter & Hayes (1977):                                                             |
|    E = 3790 · ε̇^0.06 · ρ_app^3.00   [MPa]                                             |
|                                                                                       |
| 2. Keller (1994) - Proximal Tibia Specific:                                           |
|    E = 2017 · ρ_ash^1.67            [MPa]                                             |
|                                                                                       |
| 3. Keyak et al. (1994) - Tibial Trabecular:                                           |
|    E = 33900 · ρ_app^2.20           [MPa] (for ρ_app ≤ 0.27 g/cm³)                    |
|    E = 10200 · ρ_app^0.80           [MPa] (for ρ_app > 0.27 g/cm³)                    |
|                                                                                       |
| 4. Morgan & Keaveny (2001) - Proximal Tibia Anatomically Calibrated:                  |
|    E = 3790 · ρ_ash^2.18            [MPa]                                             |
|    where ρ_ash ≈ 0.6 · ρ_app                                                          |
|                                                                                       |
+---------------------------------------------------------------------------------------+
```

### 1.1 Non-Linear Sensitivity to CT Errors
Because the exponent in $E = a \cdot \rho^b$ ranges from $1.67$ to $2.20$, errors in CT calibration or residual metal artifacts propagate non-linearly into modulus predictions:
$$\frac{\Delta E}{E} \approx b \cdot \frac{\Delta \rho}{\rho}$$
A $20\%$ artifactual depression in HU yields an approximate $40\text{--}45\%$ reduction in estimated bone stiffness, skewing interface micromotion and stress distribution analyses.

---

## 2. Bone Remodeling and Stress Shielding Mechanics
Total knee components are made of stiff materials ($E_{\text{CoCr}} \approx 210\text{ GPa}$, $E_{\text{Ti}} \approx 110\text{ GPa}$) compared to trabecular bone ($E \approx 0.1\text{--}2.0\text{ GPa}$). This stiffness mismatch unloads proximal cancellous bone, triggering adaptive bone resorption (stress shielding).

### 2.1 Huiskes Adaptive Bone Remodeling Theory
Huiskes et al. (1987) formalized strain-adaptive remodeling based on Strain Energy Density (SED):
$$U = \frac{1}{2} \mathbf{\sigma} : \mathbf{\epsilon}$$
The local mechanical stimulus is defined as $S = U / \rho$. Bone remodeling rate is governed by:
$$\frac{d\rho}{dt} = \begin{cases} 
B (S - (1 + s) S_{\text{ref}}), & S > (1 + s) S_{\text{ref}} \quad (\text{Bone Formation}) \\
0, & (1 - s) S_{\text{ref}} \le S \le (1 + s) S_{\text{ref}} \quad (\text{Dead Zone}) \\
B (S - (1 - s) S_{\text{ref}}), & S < (1 - s) S_{\text{ref}} \quad (\text{Bone Resorption})
\end{cases}$$
where $s \approx 0.10\text{--}0.20$ is the threshold half-width, $B$ is the remodeling rate constant, and $S_{\text{ref}}$ is the pre-operative physiological stimulus.

### 2.2 ISO 14243 Gait Cycle Boundary Conditions
Validation of peri-implant mechanical stability requires testing under standard ISO 14243 load conditions:
- Axial Compressive Force: Peaks at $2600\text{ N}$ ($60\%$ on medial plateau, $40\%$ on lateral plateau).
- Anterior-Posterior Shear: Peaks at $350\text{ N}$.
- Internal-External Tibial Torque: Peaks at $6.0\text{ N}\cdot\text{m}$.
- Micromotion Threshold: Relative interface micromotion $> 150\ \mu\text{m}$ inhibits bone ingrowth and leads to fibrous tissue formation, whereas $< 40\ \mu\text{m}$ allows stable osseointegration.
