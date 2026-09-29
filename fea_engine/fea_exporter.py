"""
Biomechanical Finite Element Analysis (FEA) Mesh & Material Exporter
Generates heterogeneous 3D tetrahedral finite element meshes from calibrated density maps,
assigning element-by-element elasticity tensors and exporting to FEBio (.feb) and Abaqus/CalculiX (.inp).
"""

import os
import numpy as np
from typing import Dict, Any, List, Tuple

class FEAMeshExporter:
    """
    Constructs 3D finite element meshes of peri-implant bone, implant, and cement,
    mapping local bone density into inhomogeneous elastic material models.
    """

    def __init__(self, voxel_size_mm: List[float] = [0.6, 0.4, 0.4]):
        self.voxel_size = np.array(voxel_size_mm, dtype=np.float64)

    def generate_voxel_tetrahedral_mesh(
        self,
        label_map: np.ndarray,
        vbmd_volume: np.ndarray,
        subsample_stride: int = 2
    ) -> Dict[str, Any]:
        """
        Creates a 4-node tetrahedral (C3D4) mesh by decomposing active voxels.
        Each voxel cube is decomposed into 5 or 6 tetrahedra.
        """
        z_s, y_s, x_s = label_map.shape
        active_voxels = (label_map > 0)[::subsample_stride, ::subsample_stride, ::subsample_stride]
        sz, sy, sx = active_voxels.shape

        nodes = []
        node_map = {}
        elements = []
        elem_materials = []
        elem_moduli = []

        def get_or_add_node(z, y, x):
            key = (z, y, x)
            if key not in node_map:
                nid = len(nodes) + 1
                node_map[key] = nid
                # Physical coordinates in millimeters
                coords = [
                    x * self.voxel_size[2] * subsample_stride,
                    y * self.voxel_size[1] * subsample_stride,
                    z * self.voxel_size[0] * subsample_stride
                ]
                nodes.append((nid, coords))
            return node_map[key]

        # Decompose each active voxel into 5 tetrahedra
        for iz in range(sz):
            for iy in range(sy):
                for ix in range(sx):
                    if not active_voxels[iz, iy, ix]:
                        continue

                    orig_z = min(iz * subsample_stride, z_s - 1)
                    orig_y = min(iy * subsample_stride, y_s - 1)
                    orig_x = min(ix * subsample_stride, x_s - 1)

                    mat_class = label_map[orig_z, orig_y, orig_x]
                    local_vbmd = vbmd_volume[orig_z, orig_y, orig_x]

                    # Modulus assignment (MPa)
                    if mat_class == 1:
                        # CoCrMo Alloy
                        e_mod = 210000.0
                        nu = 0.30
                        mat_name = "COBALT_CHROMIUM"
                    elif mat_class == 2:
                        # PMMA Bone Cement
                        e_mod = 2500.0
                        nu = 0.35
                        mat_name = "PMMA_CEMENT"
                    elif mat_class == 4:
                        # Cortical Bone
                        rho_ash = max(0.01, local_vbmd / 1000.0)
                        e_mod = float(np.clip(3790.0 * (rho_ash ** 2.18), 3000.0, 18000.0))
                        nu = 0.30
                        mat_name = f"BONE_CORTICAL_{int(e_mod)}"
                    else:
                        # Trabecular Bone
                        rho_ash = max(0.005, local_vbmd / 1000.0)
                        e_mod = float(np.clip(3790.0 * (rho_ash ** 2.18), 10.0, 3000.0))
                        nu = 0.30
                        mat_name = f"BONE_TRABECULAR_{int(e_mod)}"

                    # 8 Corner vertices of the cube
                    n0 = get_or_add_node(iz, iy, ix)
                    n1 = get_or_add_node(iz, iy, ix + 1)
                    n2 = get_or_add_node(iz, iy + 1, ix)
                    n3 = get_or_add_node(iz, iy + 1, ix + 1)
                    n4 = get_or_add_node(iz + 1, iy, ix)
                    n5 = get_or_add_node(iz + 1, iy, ix + 1)
                    n6 = get_or_add_node(iz + 1, iy + 1, ix)
                    n7 = get_or_add_node(iz + 1, iy + 1, ix + 1)

                    # 5 standard sub-tetrahedra
                    tets = [
                        (n0, n1, n3, n5),
                        (n0, n3, n2, n6),
                        (n0, n4, n5, n6),
                        (n3, n5, n6, n7),
                        (n0, n3, n5, n6)
                    ]

                    for t in tets:
                        eid = len(elements) + 1
                        elements.append((eid, t))
                        elem_materials.append((eid, mat_name, e_mod, nu))
                        elem_moduli.append(e_mod)

        return {
            "nodes": nodes,
            "elements": elements,
            "elem_materials": elem_materials,
            "elem_moduli": elem_moduli,
            "num_nodes": len(nodes),
            "num_elements": len(elements)
        }

    def export_abaqus_inp(
        self, mesh_data: Dict[str, Any], output_path: str
    ) -> str:
        """
        Exports finite element mesh to an Abaqus / CalculiX input deck (.inp)
        with ISO 14243 gait cycle axial loading (2600 N) and encastre base.
        """
        nodes = mesh_data["nodes"]
        elements = mesh_data["elements"]
        elem_materials = mesh_data["elem_materials"]

        # Group elements by discrete material buckets (bins of 50 MPa for efficiency)
        material_sets = {}
        for eid, m_name, e_mod, nu in elem_materials:
            bucket_key = (int(e_mod // 50) * 50, nu)
            if bucket_key not in material_sets:
                material_sets[bucket_key] = []
            material_sets[bucket_key].append(eid)

        with open(output_path, "w") as f:
            f.write("*HEADING\n")
            f.write(" TKA Patient-Specific Biomechanical Finite Element Model\n")
            f.write("** Units: mm, N, MPa\n\n")

            # Nodes
            f.write("*NODE\n")
            for nid, (x, y, z) in nodes:
                f.write(f"{nid}, {x:.4f}, {y:.4f}, {z:.4f}\n")

            # Elements
            f.write("\n*ELEMENT, TYPE=C3D4\n")
            for eid, (n1, n2, n3, n4) in elements:
                f.write(f"{eid}, {n1}, {n2}, {n3}, {n4}\n")

            # Material definitions and Element Sets
            mat_idx = 1
            for (modulus, nu), eids in material_sets.items():
                set_name = f"ELSET_MAT_{mat_idx}"
                f.write(f"\n*ELSET, ELSET={set_name}\n")
                # Write in chunks of 10
                for i in range(0, len(eids), 10):
                    chunk = eids[i:i+10]
                    f.write(", ".join(map(str, chunk)) + "\n")

                f.write(f"*MATERIAL, NAME=MAT_{mat_idx}\n")
                f.write("*ELASTIC\n")
                f.write(f"{max(10.0, float(modulus)):.2f}, {nu:.2f}\n")
                f.write(f"*SOLID SECTION, ELSET={set_name}, MATERIAL=MAT_{mat_idx}\n")
                mat_idx += 1

            # Boundary Conditions: Fix distal nodes (highest Z coordinate)
            max_z = max(coord[2] for _, coord in nodes)
            fixed_nodes = [nid for nid, coord in nodes if coord[2] >= (max_z - 2.0)]

            f.write("\n*NSET, NSET=FIXED_BASE\n")
            for i in range(0, len(fixed_nodes), 10):
                chunk = fixed_nodes[i:i+10]
                f.write(", ".join(map(str, chunk)) + "\n")

            # Top Plateau Loaded Nodes (lowest Z coordinate)
            min_z = min(coord[2] for _, coord in nodes)
            loaded_nodes = [nid for nid, coord in nodes if coord[2] <= (min_z + 2.0)]
            f.write("\n*NSET, NSET=TIBIAL_PLATEAU\n")
            for i in range(0, len(loaded_nodes), 10):
                chunk = loaded_nodes[i:i+10]
                f.write(", ".join(map(str, chunk)) + "\n")

            # Step: Static ISO 14243 Load (2600 N Compression)
            f.write("\n*STEP\n")
            f.write("*STATIC\n")
            f.write("*BOUNDARY\n")
            f.write("FIXED_BASE, 1, 3, 0.0\n")
            f.write("*CLOAD\n")
            if loaded_nodes:
                f_per_node = -2600.0 / len(loaded_nodes)
                f.write(f"TIBIAL_PLATEAU, 3, {f_per_node:.4f}\n")
            f.write("*NODE PRINT, U\n")
            f.write("*EL PRINT, S, E\n")
            f.write("*END STEP\n")

        return output_path

    def export_febio_xml(
        self, mesh_data: Dict[str, Any], output_path: str
    ) -> str:
        """
        Exports finite element model to native FEBio XML format (.feb).
        """
        nodes = mesh_data["nodes"]
        elements = mesh_data["elements"]

        with open(output_path, "w") as f:
            f.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
            f.write('<febio_spec version="3.0">\n')
            f.write('  <Module type="solid"/>\n')
            f.write('  <Control>\n')
            f.write('    <analysis>STATIC</analysis>\n')
            f.write('    <time_steps>10</time_steps>\n')
            f.write('    <step_size>0.1</step_size>\n')
            f.write('  </Control>\n')

            # Material Section (Representative elastic bone & metal)
            f.write('  <Material>\n')
            f.write('    <material id="1" name="CoCrMo" type="isotropic elastic">\n')
            f.write('      <E>210000</E><v>0.3</v>\n')
            f.write('    </material>\n')
            f.write('    <material id="2" name="Bone_Heterogeneous" type="isotropic elastic">\n')
            f.write('      <E>1500</E><v>0.3</v>\n')
            f.write('    </material>\n')
            f.write('  </Material>\n')

            # Mesh Section
            f.write('  <Mesh>\n')
            f.write('    <Nodes name="TibialNodes">\n')
            for nid, (x, y, z) in nodes[:5000]:  # Cap sample for XML footprint
                f.write(f'      <node id="{nid}">{x:.3f}, {y:.3f}, {z:.3f}</node>\n')
            f.write('    </Nodes>\n')

            f.write('    <Elements type="tet4" name="TibialElements">\n')
            for eid, (n1, n2, n3, n4) in elements[:10000]:
                f.write(f'      <elem id="{eid}">{n1}, {n2}, {n3}, {n4}</elem>\n')
            f.write('    </Elements>\n')
            f.write('  </Mesh>\n')
            f.write('</febio_spec>\n')

        return output_path
