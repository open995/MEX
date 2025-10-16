"""
Core metadata extraction modules for different file types.
"""

from mex.core.extractor_images import ImageExtractor
from mex.core.extractor_documents import DocumentExtractor
from mex.core.extractor_videos import VideoExtractor
from mex.core.extractor_archives import ArchiveExtractor
from mex.core.extractor_executables import ExecutableExtractor
from mex.core.extractor_web import WebExtractor

__all__ = [
    'ImageExtractor',
    'DocumentExtractor',
    'VideoExtractor',
    'ArchiveExtractor',
    'ExecutableExtractor',
    'WebExtractor'
]


