"""
Interactive 3D Dashboard & Web Visualizer
Generates standalone, interactive 3D HTML dashboards using Plotly,
allowing clinicians to inspect peri-implant bone density heatmaps,
tibial anatomical zones, and radial distance isochrones.
"""

import os
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any, List

class Interactive3DDashboard:
    """
    Builds self-contained, responsive 3D HTML visualizations for orthopedic surgeons.
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_interactive_3d_html(
        self,
        vbmd_volume: np.ndarray,
        metal_mask: np.ndarray,
        bone_mask: np.ndarray,
        patient_id: str = "TKA_PATIENT_001",
        downsample_factor: int = 2
    ) -> str:
        """
        Creates a 3D scatter/mesh interactive view with bone density color mapping
        and metallic implant geometry.
        """
        # Downsample for smooth browser rendering
        v_sub = vbmd_volume[::downsample_factor, ::downsample_factor, ::downsample_factor]
        m_sub = metal_mask[::downsample_factor, ::downsample_factor, ::downsample_factor]
        b_sub = bone_mask[::downsample_factor, ::downsample_factor, ::downsample_factor]

        z_coords, y_coords, x_coords = np.where(b_sub & (v_sub > 20.0))
        densities = v_sub[z_coords, y_coords, x_coords]

        # Cap sample points to 15,000 for responsive WebGL rendering
        if len(densities) > 15000:
            choice_idx = np.random.choice(len(densities), 15000, replace=False)
            z_coords = z_coords[choice_idx]
            y_coords = y_coords[choice_idx]
            x_coords = x_coords[choice_idx]
            densities = densities[choice_idx]

        # 1. Bone Density Scatter Point Cloud
        bone_scatter = go.Scatter3d(
            x=x_coords * downsample_factor * 0.4,
            y=y_coords * downsample_factor * 0.4,
            z=z_coords * downsample_factor * 0.6,
            mode="markers",
            marker=dict(
                size=2.8,
                color=densities,
                colorscale="Jet",
                cmin=50,
                cmax=900,
                colorbar=dict(title="vBMD (mg HA/cm³)", thickness=15, len=0.7),
                opacity=0.85
            ),
            name="Peri-Implant Bone",
            text=[f"vBMD: {d:.1f} mg/cm³" for d in densities],
            hoverinfo="x+y+z+text"
        )

        # 2. Metal Implant Points / Boundary
        mz, my, mx = np.where(m_sub)
        if len(mz) > 5000:
            m_choice = np.random.choice(len(mz), 5000, replace=False)
            mz = mz[m_choice]
            my = my[m_choice]
            mx = mx[m_choice]

        metal_scatter = go.Scatter3d(
            x=mx * downsample_factor * 0.4,
            y=my * downsample_factor * 0.4,
            z=mz * downsample_factor * 0.6,
            mode="markers",
            marker=dict(
                size=3.2,
                color="lightgray",
                opacity=0.60
            ),
            name="Metallic Implant (CoCrMo)",
            hoverinfo="name"
        )

        fig = go.Figure(data=[bone_scatter, metal_scatter])

        fig.update_layout(
            title=dict(
                text=f"<b>Patient-Specific Peri-Implant Bone Mineral Density (3D Interactive)</b><br>Patient: {patient_id}",
                x=0.05,
                y=0.95
            ),
            scene=dict(
                xaxis_title="Mediolateral (mm)",
                yaxis_title="Anteroposterior (mm)",
                zaxis_title="Superoinferior (mm)",
                aspectmode="data",
                camera=dict(
                    eye=dict(x=1.6, y=1.6, z=1.2)
                )
            ),
            margin=dict(l=0, r=0, b=0, t=60),
            template="plotly_dark"
        )

        html_path = os.path.join(self.output_dir, f"{patient_id}_interactive_3d_density.html")
        fig.write_html(html_path, include_plotlyjs="cdn")
        return html_path
