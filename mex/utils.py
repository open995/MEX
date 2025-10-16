"""
Utility functions for MEX metadata extractor.
"""

import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def compute_file_hash(file_path: str, algorithm: str = 'sha256') -> Optional[str]:
    """
    Compute hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (md5, sha1, sha256)
        
    Returns:
        Hex digest of the hash or None if error
    """
    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return None


def validate_file_path(file_path: str) -> bool:
    """
    Validate if file path exists and is accessible.
    
    Args:
        file_path: Path to validate
        
    Returns:
        True if valid and accessible, False otherwise
    """
    path = Path(file_path)
    return path.exists() and path.is_file()


def format_timestamp(timestamp: Any) -> Optional[str]:
    """
    Format various timestamp formats to ISO 8601.
    
    Args:
        timestamp: Timestamp in various formats
        
    Returns:
        ISO 8601 formatted string or None
    """
    if timestamp is None:
        return None
    
    try:
        if isinstance(timestamp, str):
            # Try parsing common formats
            from dateutil import parser
            dt = parser.parse(timestamp)
            return dt.isoformat()
        elif isinstance(timestamp, (int, float)):
            # Unix timestamp
            dt = datetime.fromtimestamp(timestamp)
            return dt.isoformat()
        elif isinstance(timestamp, datetime):
            return timestamp.isoformat()
        else:
            return str(timestamp)
    except Exception as e:
        logger.debug(f"Error formatting timestamp {timestamp}: {e}")
        return str(timestamp) if timestamp else None


def get_file_type(file_path: str) -> Dict[str, str]:
    """
    Determine file type and category.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with mime_type and category
    """
    path = Path(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    extension = path.suffix.lower()
    
    # Category mapping
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.heic', '.webp'}
    document_extensions = {'.pdf', '.doc', '.docx', '.odt', '.rtf', '.txt'}
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
    audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
    archive_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}
    executable_extensions = {'.exe', '.dll', '.so', '.dylib', '.bin'}
    web_extensions = {'.html', '.htm', '.xml'}
    
    if extension in image_extensions:
        category = 'image'
    elif extension in document_extensions:
        category = 'document'
    elif extension in video_extensions:
        category = 'video'
    elif extension in audio_extensions:
        category = 'audio'
    elif extension in archive_extensions:
        category = 'archive'
    elif extension in executable_extensions:
        category = 'executable'
    elif extension in web_extensions:
        category = 'web'
    else:
        category = 'unknown'
    
    return {
        'mime_type': mime_type or 'application/octet-stream',
        'category': category,
        'extension': extension
    }


def safe_extract(data: Dict, *keys, default=None) -> Any:
    """
    Safely extract nested dictionary values.
    
    Args:
        data: Dictionary to extract from
        *keys: Chain of keys to traverse
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def parse_gps_coordinates(gps_data: Dict) -> Optional[Dict[str, float]]:
    """
    Parse GPS coordinates from EXIF format to decimal degrees.
    
    Args:
        gps_data: GPS data dictionary
        
    Returns:
        Dictionary with latitude and longitude or None
    """
    try:
        def convert_to_degrees(value):
            """Convert GPS coordinates to degrees."""
            if isinstance(value, (list, tuple)) and len(value) == 3:
                d, m, s = value
                if hasattr(d, 'num'):  # IFD Rational
                    d = d.num / d.den if d.den else 0
                if hasattr(m, 'num'):
                    m = m.num / m.den if m.den else 0
                if hasattr(s, 'num'):
                    s = s.num / s.den if s.den else 0
                return float(d) + float(m) / 60.0 + float(s) / 3600.0
            return float(value)
        
        lat = gps_data.get('GPSLatitude')
        lat_ref = gps_data.get('GPSLatitudeRef', 'N')
        lon = gps_data.get('GPSLongitude')
        lon_ref = gps_data.get('GPSLongitudeRef', 'E')
        
        if lat and lon:
            latitude = convert_to_degrees(lat)
            longitude = convert_to_degrees(lon)
            
            if lat_ref == 'S':
                latitude = -latitude
            if lon_ref == 'W':
                longitude = -longitude
                
            return {'latitude': latitude, 'longitude': longitude}
    except Exception as e:
        logger.debug(f"Error parsing GPS coordinates: {e}")
    
    return None


def create_metadata_template() -> Dict[str, Any]:
    """
    Create a standard metadata template.
    
    Returns:
        Empty metadata dictionary structure
    """
    return {
        'file_info': {
            'name': None,
            'path': None,
            'size': None,
            'type': None,
            'hash_md5': None,
            'hash_sha256': None
        },
        'timestamps': {
            'created': None,
            'modified': None,
            'accessed': None
        },
        'metadata': {},
        'extracted_by': 'MEX v1.0.0',
        'extraction_timestamp': datetime.now().isoformat()
    }


def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata by removing binary data and converting to JSON-safe types.
    
    Args:
        metadata: Raw metadata dictionary
        
    Returns:
        Sanitized metadata dictionary
    """
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, bytes):
            # Convert bytes to hex string
            sanitized[key] = value.hex()[:100]  # Limit length
        elif isinstance(value, dict):
            sanitized[key] = sanitize_metadata(value)
        elif isinstance(value, (list, tuple)):
            sanitized[key] = [sanitize_metadata({'v': v})['v'] if isinstance(v, dict) 
                            else v for v in value]
        elif isinstance(value, (str, int, float, bool, type(None))):
            sanitized[key] = value
        else:
            # Convert other types to string
            sanitized[key] = str(value)
    return sanitized


