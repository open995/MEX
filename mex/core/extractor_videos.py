"""
Video and Audio metadata extractor for MEX.
Supports: MP4, MOV, MP3, WAV, AVI, and other media formats.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from mex.utils import (
    create_metadata_template,
    format_timestamp,
    sanitize_metadata,
    compute_file_hash,
    parse_gps_coordinates
)

logger = logging.getLogger(__name__)


class VideoExtractor:
    """Extract metadata from video and audio files."""
    
    SUPPORTED_FORMATS = {
        '.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm',  # Video
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'  # Audio
    }
    
    @staticmethod
    def can_extract(file_path: str) -> bool:
        """Check if this extractor can handle the file."""
        return Path(file_path).suffix.lower() in VideoExtractor.SUPPORTED_FORMATS
    
    @staticmethod
    def extract(file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from video/audio file.
        
        Args:
            file_path: Path to media file
            
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
            'type': 'video' if path.suffix.lower() in {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm'} else 'audio',
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
        
        # Extract using mutagen (for audio metadata)
        mutagen_data = VideoExtractor._extract_mutagen(file_path)
        
        # Extract using hachoir (for detailed media info)
        hachoir_data = VideoExtractor._extract_hachoir(file_path)
        
        # Combine metadata
        media_metadata = {}
        if mutagen_data:
            media_metadata['audio_tags'] = mutagen_data
        if hachoir_data:
            media_metadata['media_info'] = hachoir_data
        
        if media_metadata:
            metadata['metadata']['media'] = media_metadata
        
        return metadata
    
    @staticmethod
    def _extract_mutagen(file_path: str) -> Dict[str, Any]:
        """Extract audio metadata using mutagen."""
        try:
            from mutagen import File as MutagenFile
            
            audio = MutagenFile(file_path)
            if audio is None:
                return {}
            
            result = {
                'format': type(audio).__name__,
                'length': audio.info.length if hasattr(audio, 'info') else None,
                'bitrate': audio.info.bitrate if hasattr(audio, 'info') and hasattr(audio.info, 'bitrate') else None,
                'sample_rate': audio.info.sample_rate if hasattr(audio, 'info') and hasattr(audio.info, 'sample_rate') else None,
                'channels': audio.info.channels if hasattr(audio, 'info') and hasattr(audio.info, 'channels') else None,
                'tags': {}
            }
            
            # Extract tags
            if audio.tags:
                for key, value in audio.tags.items():
                    try:
                        # Convert to string
                        if isinstance(value, list):
                            result['tags'][key] = [str(v) for v in value]
                        else:
                            result['tags'][key] = str(value)
                    except:
                        pass
            
            # Extract common fields
            common_tags = {
                'artist': ['artist', 'ARTIST', 'TPE1', '©ART'],
                'album': ['album', 'ALBUM', 'TALB', '©alb'],
                'title': ['title', 'TITLE', 'TIT2', '©nam'],
                'date': ['date', 'DATE', 'TDRC', '©day'],
                'genre': ['genre', 'GENRE', 'TCON', '©gen'],
                'comment': ['comment', 'COMMENT', 'COMM', '©cmt'],
                'copyright': ['copyright', 'COPYRIGHT', 'TCOP', '©cpy']
            }
            
            for field, possible_keys in common_tags.items():
                for key in possible_keys:
                    if audio.tags and key in audio.tags:
                        value = audio.tags[key]
                        result[field] = str(value[0]) if isinstance(value, list) else str(value)
                        break
            
            # Remove None values
            return {k: v for k, v in result.items() if v is not None}
            
        except Exception as e:
            logger.debug(f"Mutagen extraction failed: {e}")
            return {}
    
    @staticmethod
    def _extract_hachoir(file_path: str) -> Dict[str, Any]:
        """Extract media metadata using hachoir."""
        try:
            from hachoir.parser import createParser
            from hachoir.metadata import extractMetadata
            
            parser = createParser(file_path)
            if not parser:
                return {}
            
            metadata_obj = extractMetadata(parser)
            if not metadata_obj:
                return {}
            
            result = {}
            
            # Extract all available metadata
            for line in metadata_obj.exportPlaintext():
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    key = key.strip('- ').lower().replace(' ', '_')
                    result[key] = value.strip()
            
            # Extract specific fields
            if hasattr(metadata_obj, 'get'):
                specific_fields = {
                    'width': 'width',
                    'height': 'height',
                    'duration': 'duration',
                    'frame_rate': 'frame_rate',
                    'bit_rate': 'bit_rate',
                    'codec': 'codec',
                    'author': 'author',
                    'producer': 'producer',
                    'creation_date': 'created',
                    'comment': 'comment',
                    'title': 'title',
                    'artist': 'artist'
                }
                
                for meta_key, out_key in specific_fields.items():
                    value = metadata_obj.get(meta_key)
                    if value:
                        if 'date' in out_key:
                            value = format_timestamp(str(value))
                        result[out_key] = str(value)
            
            # GPS data if available
            if hasattr(metadata_obj, 'get'):
                lat = metadata_obj.get('latitude')
                lon = metadata_obj.get('longitude')
                if lat and lon:
                    result['gps'] = {
                        'latitude': float(lat),
                        'longitude': float(lon)
                    }
            
            return result
            
        except Exception as e:
            logger.debug(f"Hachoir extraction failed: {e}")
            return {}


