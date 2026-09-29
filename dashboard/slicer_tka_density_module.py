"""
3D Slicer Extension Scripted Module: TKABoneDensityEstimator
Enables loading, displaying, and interacting with patient-specific quantitative
TKA bone density volumes directly inside 3D Slicer.
"""

try:
    import slicer
    from slicer.ScriptedLoadableModule import *
    import vtk, qt, ctk
except ImportError:
    # Running outside 3D Slicer environment
    slicer = None

class TKABoneDensityEstimator:
    """
    3D Slicer extension metadata class.
    """
    def __init__(self, parent):
        if parent:
            parent.title = "TKA Peri-Implant Bone Density Estimator"
            parent.categories = ["Orthopedics", "Quantification"]
            parent.dependencies = []
            parent.contributors = ["Antigravity Medical Imaging Team"]
            parent.helpText = (
                "Loads calibrated vBMD volumes (mg HA/cm3), displays multi-class segmentations "
                "(Metal, PMMA cement, cortical shell, trabecular bone), and overlays 3D Ewald/Kozinn zones."
            )
            parent.acknowledgementText = "Developed with support from DeepMind Advanced Agentic Coding."

def load_density_volume_in_slicer(dicom_dir_or_mha_path: str):
    """
    Convenience function callable from 3D Slicer Python Interactor.
    """
    if slicer is None:
        print("Error: This function must be executed inside 3D Slicer's Python environment.")
        return None

    volume_node = slicer.util.loadVolume(dicom_dir_or_mha_path)
    if volume_node:
        # Assign custom orthopedic Rainbow/Jet color lookup table
        color_node = slicer.util.getNode("Rainbow")
        if color_node:
            volume_node.GetDisplayNode().SetAndObserveColorNodeID(color_node.GetID())
        print(f"Loaded TKA Density Volume: {volume_node.GetName()}")
    return volume_node
