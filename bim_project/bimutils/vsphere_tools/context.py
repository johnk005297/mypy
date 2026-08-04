from .service import Vsphere

class VsphereContext:
    """Store shared vsphere parameters"""
    def __init__(self):
        self.vs = Vsphere()
        self.headers = None

vs_ctx = VsphereContext()