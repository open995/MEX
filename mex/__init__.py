"""
MEX - Metadata Extractor
A professional OSINT and digital forensics tool for metadata analysis and correlation.
"""

__version__ = "1.0.0"
__author__ = "MEX Development Team"

from mex.utils import (
    compute_file_hash,
    validate_file_path,
    format_timestamp,
    get_file_type
)

__all__ = [
    'compute_file_hash',
    'validate_file_path', 
    'format_timestamp',
    'get_file_type'
]


