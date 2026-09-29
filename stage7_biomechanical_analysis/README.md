# Stage 7 Milestone: Biomechanical Modeling & Remodeling Analysis

## Objective
Convert scalar bone mineral density ($v\text{BMD}$) fields into heterogeneous elasticity material tensors ($E(\mathbf{x})$) and track longitudinal bone remodeling against precision-calibrated statistical thresholds.

## Key Formulations
1. **Constitutive Law (Morgan & Keaveny, 2001)**:
   $$E(\mathbf{x}) = 3790 \cdot (\rho_{\text{ash}}(\mathbf{x}))^{2.18} \quad [\text{MPa}]$$
   where $\rho_{\text{ash}} = v\text{BMD} \times 10^{-3}\text{ g/cm}^3$.
2. **Least Significant Change ($\text{LSC}_{95\%}$)**:
   $$\text{LSC}_{95\%} = 2.77 \times \text{RMS-CV} \approx 4.15\%$$
   Ensures changes are flagged as biological remodeling only if they exceed scanner precision error with $95\%$ confidence.
3. **Loosening Vulnerability Index (LVI)**:
   Evaluates bone resorption in the immediate $0\text{--}0.5\text{ mm}$ interface zone (Shell A).
