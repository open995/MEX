"""
Executable metadata extractor for MEX.
Supports: EXE, DLL, ELF, Mach-O, and other executable formats.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from mex.utils import (
    create_metadata_template,
    format_timestamp,
    sanitize_metadata,
    compute_file_hash
)

logger = logging.getLogger(__name__)


class ExecutableExtractor:
    """Extract metadata from executable files."""
    
    SUPPORTED_FORMATS = {'.exe', '.dll', '.so', '.dylib', '.bin', '.elf'}
    
    @staticmethod
    def can_extract(file_path: str) -> bool:
        """Check if this extractor can handle the file."""
        ext = Path(file_path).suffix.lower()
        if ext in ExecutableExtractor.SUPPORTED_FORMATS:
            return True
        # Also check if file has no extension but might be ELF
        if not ext:
            try:
                with open(file_path, 'rb') as f:
                    magic = f.read(4)
                    return magic == b'\x7fELF'  # ELF magic number
            except:
                pass
        return False
    
    @staticmethod
    def extract(file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from executable file.
        
        Args:
            file_path: Path to executable file
            
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
            'type': 'executable',
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
        
        # Determine executable type and extract
        exec_data = ExecutableExtractor._detect_and_extract(file_path)
        
        if exec_data:
            metadata['metadata']['executable'] = exec_data
        
        return metadata
    
    @staticmethod
    def _detect_and_extract(file_path: str) -> Dict[str, Any]:
        """Detect executable type and extract metadata."""
        # Try PE first (Windows executables)
        pe_data = ExecutableExtractor._extract_pe(file_path)
        if pe_data:
            return pe_data
        
        # Try ELF (Linux executables)
        elf_data = ExecutableExtractor._extract_elf(file_path)
        if elf_data:
            return elf_data
        
        # Try Mach-O (macOS executables)
        macho_data = ExecutableExtractor._extract_macho(file_path)
        if macho_data:
            return macho_data
        
        return {}
    
    @staticmethod
    def _extract_pe(file_path: str) -> Dict[str, Any]:
        """Extract metadata from PE (Windows) executables."""
        try:
            import pefile
            
            pe = pefile.PE(file_path)
            
            result = {
                'format': 'PE (Portable Executable)',
                'architecture': 'x64' if pe.FILE_HEADER.Machine == 0x8664 else 'x86',
                'subsystem': pefile.SUBSYSTEM_TYPE.get(pe.OPTIONAL_HEADER.Subsystem, 'Unknown'),
                'compilation_timestamp': format_timestamp(pe.FILE_HEADER.TimeDateStamp),
                'entry_point': hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint),
                'image_base': hex(pe.OPTIONAL_HEADER.ImageBase),
                'sections': []
            }
            
            # Extract section information
            for section in pe.sections:
                result['sections'].append({
                    'name': section.Name.decode('utf-8', errors='ignore').strip('\x00'),
                    'virtual_address': hex(section.VirtualAddress),
                    'virtual_size': section.Misc_VirtualSize,
                    'raw_size': section.SizeOfRawData,
                    'entropy': section.get_entropy()
                })
            
            # Extract imports
            imports = []
            if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                for entry in pe.DIRECTORY_ENTRY_IMPORT[:10]:  # Limit to first 10
                    dll_name = entry.dll.decode('utf-8', errors='ignore')
                    imports.append(dll_name)
            result['imports'] = imports
            
            # Extract exports
            exports = []
            if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
                for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols[:20]:  # Limit to first 20
                    if exp.name:
                        exports.append(exp.name.decode('utf-8', errors='ignore'))
            result['exports'] = exports
            
            # Extract version information
            if hasattr(pe, 'VS_VERSIONINFO'):
                version_info = {}
                if hasattr(pe, 'FileInfo'):
                    for fileinfo in pe.FileInfo:
                        if hasattr(fileinfo, 'StringTable'):
                            for st in fileinfo.StringTable:
                                for entry in st.entries.items():
                                    key = entry[0].decode('utf-8', errors='ignore')
                                    value = entry[1].decode('utf-8', errors='ignore')
                                    version_info[key] = value
                if version_info:
                    result['version_info'] = version_info
            
            # Digital signature
            if hasattr(pe, 'DIRECTORY_ENTRY_SECURITY'):
                result['has_signature'] = True
            else:
                result['has_signature'] = False
            
            pe.close()
            return result
            
        except Exception as e:
            logger.debug(f"PE extraction failed: {e}")
            return {}
    
    @staticmethod
    def _extract_elf(file_path: str) -> Dict[str, Any]:
        """Extract metadata from ELF (Linux) executables."""
        try:
            import lief
            
            binary = lief.parse(file_path)
            if binary is None or binary.format != lief.EXE_FORMATS.ELF:
                return {}
            
            result = {
                'format': 'ELF (Executable and Linkable Format)',
                'architecture': str(binary.header.machine_type),
                'entry_point': hex(binary.entrypoint),
                'type': str(binary.header.file_type),
                'sections': []
            }
            
            # Extract section information
            for section in binary.sections[:20]:  # Limit sections
                result['sections'].append({
                    'name': section.name,
                    'type': str(section.type),
                    'virtual_address': hex(section.virtual_address),
                    'size': section.size,
                    'entropy': section.entropy
                })
            
            # Extract dynamic entries
            if binary.has_dynamic_entries:
                libraries = [lib for lib in binary.libraries[:10]]  # Limit to 10
                result['libraries'] = libraries
            
            # Extract symbols
            symbols = []
            for sym in binary.symbols[:20]:  # Limit to 20
                if sym.name:
                    symbols.append(sym.name)
            result['symbols'] = symbols
            
            return result
            
        except Exception as e:
            logger.debug(f"ELF extraction failed: {e}")
            return {}
    
    @staticmethod
    def _extract_macho(file_path: str) -> Dict[str, Any]:
        """Extract metadata from Mach-O (macOS) executables."""
        try:
            import lief
            
            binary = lief.parse(file_path)
            if binary is None or binary.format != lief.EXE_FORMATS.MACHO:
                return {}
            
            result = {
                'format': 'Mach-O (macOS Executable)',
                'architecture': str(binary.header.cpu_type),
                'file_type': str(binary.header.file_type),
                'sections': []
            }
            
            # Extract section information
            for section in binary.sections[:20]:
                result['sections'].append({
                    'name': section.name,
                    'segment_name': section.segment_name,
                    'virtual_address': hex(section.virtual_address),
                    'size': section.size
                })
            
            # Extract libraries
            libraries = [lib for lib in binary.libraries[:10]]
            result['libraries'] = libraries
            
            return result
            
        except Exception as e:
            logger.debug(f"Mach-O extraction failed: {e}")
            return {}


