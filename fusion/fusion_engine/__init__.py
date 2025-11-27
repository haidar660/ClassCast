"""
ClassCast Fusion Package
Final production version - Batch fusion with retry logic
"""

from .batch_fusion import batch_fuse_segments
from .fusion_controller import FusionController

__all__ = ['batch_fuse_segments', 'FusionController']