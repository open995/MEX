"""
Archive metadata extractor for MEX.
Supports: ZIP, RAR, 7Z, TAR, and other archive formats.
Includes recursive extraction of contained files.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import zipfile
import tarfile
import tempfile
import os

from mex.utils import (
    create_metadata_template,
    format_timestamp,
    compute_file_hash,
    get_file_type
)

logger = logging.getLogger(__name__)


class ArchiveExtractor:
    """Extract metadata from archive files and analyze contents."""
    
    SUPPORTED_FORMATS = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tgz'}
    
    @staticmethod
    def can_extract(file_path: str) -> bool:
        """Check if this extractor can handle the file."""
        return Path(file_path).suffix.lower() in ArchiveExtractor.SUPPORTED_FORMATS
    
    @staticmethod
    def extract(file_path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Extract metadata from archive file.
        
        Args:
            file_path: Path to archive file
            recursive: Whether to recursively analyze contained files
            
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
            'type': 'archive',
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
        
        # Extract based on archive type
        extension = path.suffix.lower()
        archive_data = {}
        
        if extension == '.zip':
            archive_data = ArchiveExtractor._extract_zip(file_path)
        elif extension == '.rar':
            archive_data = ArchiveExtractor._extract_rar(file_path)
        elif extension == '.7z':
            archive_data = ArchiveExtractor._extract_7z(file_path)
        elif extension in {'.tar', '.gz', '.bz2', '.xz', '.tgz'}:
            archive_data = ArchiveExtractor._extract_tar(file_path)
        
        if archive_data:
            metadata['metadata']['archive'] = archive_data
            
            # Recursive analysis of contained files if enabled
            if recursive and 'files' in archive_data:
                metadata['metadata']['contained_files_metadata'] = \
                    ArchiveExtractor._analyze_contained_files(file_path, extension)
        
        return metadata
    
    @staticmethod
    def _extract_zip(file_path: str) -> Dict[str, Any]:
        """Extract metadata from ZIP archive."""
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                files = []
                for info in zf.filelist:
                    files.append({
                        'filename': info.filename,
                        'compressed_size': info.compress_size,
                        'uncompressed_size': info.file_size,
                        'compression_type': info.compress_type,
                        'date_time': format_timestamp(
                            f"{info.date_time[0]}-{info.date_time[1]:02d}-{info.date_time[2]:02d} "
                            f"{info.date_time[3]:02d}:{info.date_time[4]:02d}:{info.date_time[5]:02d}"
                        ),
                        'crc': info.CRC,
                        'is_dir': info.is_dir()
                    })
                
                return {
                    'format': 'ZIP',
                    'file_count': len([f for f in files if not f['is_dir']]),
                    'total_compressed_size': sum(f['compressed_size'] for f in files),
                    'total_uncompressed_size': sum(f['uncompressed_size'] for f in files),
                    'files': files,
                    'comment': zf.comment.decode('utf-8', errors='ignore') if zf.comment else None
                }
        except Exception as e:
            logger.error(f"Error extracting ZIP metadata: {e}")
            return {}
    
    @staticmethod
    def _extract_rar(file_path: str) -> Dict[str, Any]:
        """Extract metadata from RAR archive."""
        try:
            import rarfile
            
            with rarfile.RarFile(file_path, 'r') as rf:
                files = []
                for info in rf.infolist():
                    files.append({
                        'filename': info.filename,
                        'compressed_size': info.compress_size,
                        'uncompressed_size': info.file_size,
                        'date_time': format_timestamp(info.date_time),
                        'crc': info.CRC,
                        'is_dir': info.is_dir()
                    })
                
                return {
                    'format': 'RAR',
                    'file_count': len([f for f in files if not f['is_dir']]),
                    'total_compressed_size': sum(f['compressed_size'] for f in files),
                    'total_uncompressed_size': sum(f['uncompressed_size'] for f in files),
                    'files': files,
                    'comment': rf.comment.decode('utf-8', errors='ignore') if rf.comment else None
                }
        except Exception as e:
            logger.error(f"Error extracting RAR metadata: {e}")
            return {}
    
    @staticmethod
    def _extract_7z(file_path: str) -> Dict[str, Any]:
        """Extract metadata from 7Z archive."""
        try:
            import py7zr
            
            with py7zr.SevenZipFile(file_path, 'r') as szf:
                files = []
                for name, info in szf.list():
                    files.append({
                        'filename': name,
                        'uncompressed_size': info.uncompressed,
                        'compressed_size': info.compressed if hasattr(info, 'compressed') else None,
                        'date_time': format_timestamp(info.creationtime) if hasattr(info, 'creationtime') else None,
                        'is_dir': info.is_directory
                    })
                
                return {
                    'format': '7Z',
                    'file_count': len([f for f in files if not f['is_dir']]),
                    'total_uncompressed_size': sum(f['uncompressed_size'] for f in files if f['uncompressed_size']),
                    'files': files
                }
        except Exception as e:
            logger.error(f"Error extracting 7Z metadata: {e}")
            return {}
    
    @staticmethod
    def _extract_tar(file_path: str) -> Dict[str, Any]:
        """Extract metadata from TAR archive."""
        try:
            # Determine compression
            compression_mode = 'r'
            if file_path.endswith('.gz') or file_path.endswith('.tgz'):
                compression_mode = 'r:gz'
            elif file_path.endswith('.bz2'):
                compression_mode = 'r:bz2'
            elif file_path.endswith('.xz'):
                compression_mode = 'r:xz'
            
            with tarfile.open(file_path, compression_mode) as tf:
                files = []
                for member in tf.getmembers():
                    files.append({
                        'filename': member.name,
                        'size': member.size,
                        'mode': oct(member.mode),
                        'owner': member.uname,
                        'group': member.gname,
                        'modified': format_timestamp(member.mtime),
                        'is_dir': member.isdir(),
                        'is_file': member.isfile(),
                        'is_link': member.issym() or member.islnk()
                    })
                
                return {
                    'format': f'TAR ({compression_mode})',
                    'file_count': len([f for f in files if f['is_file']]),
                    'total_size': sum(f['size'] for f in files if f['is_file']),
                    'files': files
                }
        except Exception as e:
            logger.error(f"Error extracting TAR metadata: {e}")
            return {}
    
    @staticmethod
    def _analyze_contained_files(archive_path: str, extension: str) -> List[Dict[str, Any]]:
        """
        Extract and analyze metadata from files contained in archive.
        
        Args:
            archive_path: Path to the archive
            extension: Archive file extension
            
        Returns:
            List of metadata dictionaries for contained files
        """
        results = []
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract files
                if extension == '.zip':
                    with zipfile.ZipFile(archive_path, 'r') as zf:
                        zf.extractall(temp_dir)
                elif extension in {'.tar', '.gz', '.bz2', '.xz', '.tgz'}:
                    compression_mode = 'r'
                    if archive_path.endswith('.gz') or archive_path.endswith('.tgz'):
                        compression_mode = 'r:gz'
                    elif archive_path.endswith('.bz2'):
                        compression_mode = 'r:bz2'
                    elif archive_path.endswith('.xz'):
                        compression_mode = 'r:xz'
                    with tarfile.open(archive_path, compression_mode) as tf:
                        tf.extractall(temp_dir)
                # Note: 7z and RAR require external dependencies
                
                # Analyze each extracted file
                for root, dirs, files in os.walk(temp_dir):
                    for file in files[:10]:  # Limit to first 10 files to prevent excessive processing
                        file_path = os.path.join(root, file)
                        file_type = get_file_type(file_path)
                        
                        # Import extractors here to avoid circular imports
                        from mex.core import (
                            ImageExtractor, DocumentExtractor, VideoExtractor
                        )
                        
                        extractor = None
                        if ImageExtractor.can_extract(file_path):
                            extractor = ImageExtractor
                        elif DocumentExtractor.can_extract(file_path):
                            extractor = DocumentExtractor
                        elif VideoExtractor.can_extract(file_path):
                            extractor = VideoExtractor
                        
                        if extractor:
                            try:
                                file_metadata = extractor.extract(file_path)
                                file_metadata['_archive_source'] = Path(archive_path).name
                                results.append(file_metadata)
                            except Exception as e:
                                logger.debug(f"Error analyzing {file}: {e}")
        
        except Exception as e:
            logger.error(f"Error analyzing archive contents: {e}")
        
        return results


