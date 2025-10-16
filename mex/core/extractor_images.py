"""
Image metadata extractor for MEX.
Supports: JPG, PNG, TIFF, HEIC, and other image formats.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import exifread

from mex.utils import (
    create_metadata_template,
    parse_gps_coordinates,
    format_timestamp,
    sanitize_metadata,
    compute_file_hash
)

logger = logging.getLogger(__name__)


class ImageExtractor:
    """Extract metadata from image files."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.heic', '.webp'}
    
    @staticmethod
    def can_extract(file_path: str) -> bool:
        """Check if this extractor can handle the file."""
        return Path(file_path).suffix.lower() in ImageExtractor.SUPPORTED_FORMATS
    
    @staticmethod
    def extract(file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from image file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Metadata dictionary
        """
        metadata = create_metadata_template()
        path = Path(file_path)
        
        # Basic file info
        metadata['file_info'].update({
            'name': path.name,
            'path': str(path.absolute()),
            'size': path.stat().st_size,
            'type': 'image',
            'hash_md5': compute_file_hash(file_path, 'md5'),
            'hash_sha256': compute_file_hash(file_path, 'sha256')
        })
        
        # Timestamps
        stat = path.stat()
        metadata['timestamps'].update({
            'created': format_timestamp(stat.st_ctime),
            'modified': format_timestamp(stat.st_mtime),
            'accessed': format_timestamp(stat.st_atime)
        })
        
        # Extract EXIF data using multiple methods
        exif_data = ImageExtractor._extract_exif_pillow(file_path)
        exif_data_detailed = ImageExtractor._extract_exif_exifread(file_path)
        
        # Image properties
        try:
            with Image.open(file_path) as img:
                metadata['metadata']['image'] = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
        except Exception as e:
            logger.debug(f"Error reading image properties: {e}")
        
        # Process EXIF data
        if exif_data or exif_data_detailed:
            metadata['metadata']['exif'] = ImageExtractor._process_exif(
                exif_data, exif_data_detailed
            )
        
        return metadata
    
    @staticmethod
    def _extract_exif_pillow(file_path: str) -> Dict[str, Any]:
        """Extract EXIF using Pillow."""
        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    return {
                        TAGS.get(key, key): value
                        for key, value in exif_data.items()
                    }
        except Exception as e:
            logger.debug(f"Pillow EXIF extraction failed: {e}")
        return {}
    
    @staticmethod
    def _extract_exif_exifread(file_path: str) -> Dict[str, Any]:
        """Extract EXIF using exifread library."""
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=True)
                return {
                    key: str(value) for key, value in tags.items()
                }
        except Exception as e:
            logger.debug(f"exifread extraction failed: {e}")
        return {}
    
    @staticmethod
    def _process_exif(pillow_data: Dict, exifread_data: Dict) -> Dict[str, Any]:
        """Process and combine EXIF data from multiple sources."""
        processed = {
            'camera': {},
            'settings': {},
            'gps': {},
            'software': {},
            'dates': {},
            'raw': {}
        }
        
        # Camera information
        camera_fields = {
            'Make': 'make',
            'Model': 'model',
            'LensMake': 'lens_make',
            'LensModel': 'lens_model'
        }
        for exif_key, out_key in camera_fields.items():
            if exif_key in pillow_data:
                processed['camera'][out_key] = str(pillow_data[exif_key])
        
        # Camera settings
        settings_fields = {
            'ExposureTime': 'exposure_time',
            'FNumber': 'f_number',
            'ISO': 'iso',
            'ISOSpeedRatings': 'iso',
            'FocalLength': 'focal_length',
            'Flash': 'flash',
            'WhiteBalance': 'white_balance'
        }
        for exif_key, out_key in settings_fields.items():
            if exif_key in pillow_data:
                processed['settings'][out_key] = str(pillow_data[exif_key])
        
        # GPS data
        if 'GPSInfo' in pillow_data:
            gps_raw = pillow_data['GPSInfo']
            gps_decoded = {}
            for key, val in gps_raw.items():
                gps_decoded[GPSTAGS.get(key, key)] = val
            
            coordinates = parse_gps_coordinates(gps_decoded)
            if coordinates:
                processed['gps']['coordinates'] = coordinates
            
            if 'GPSAltitude' in gps_decoded:
                processed['gps']['altitude'] = str(gps_decoded['GPSAltitude'])
            if 'GPSTimeStamp' in gps_decoded:
                processed['gps']['timestamp'] = str(gps_decoded['GPSTimeStamp'])
        
        # Software information
        software_fields = {
            'Software': 'software',
            'ProcessingSoftware': 'processing_software',
            'Artist': 'artist',
            'Copyright': 'copyright'
        }
        for exif_key, out_key in software_fields.items():
            if exif_key in pillow_data:
                processed['software'][out_key] = str(pillow_data[exif_key])
        
        # Dates
        date_fields = {
            'DateTime': 'datetime',
            'DateTimeOriginal': 'datetime_original',
            'DateTimeDigitized': 'datetime_digitized'
        }
        for exif_key, out_key in date_fields.items():
            if exif_key in pillow_data:
                processed['dates'][out_key] = format_timestamp(str(pillow_data[exif_key]))
        
        # Add all raw EXIF data from exifread
        processed['raw'] = sanitize_metadata(exifread_data)
        
        return processed


