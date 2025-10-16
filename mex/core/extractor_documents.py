"""
Document metadata extractor for MEX.
Supports: PDF, DOCX, ODT, RTF, and other document formats.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from io import BytesIO

from mex.utils import (
    create_metadata_template,
    format_timestamp,
    sanitize_metadata,
    compute_file_hash
)

logger = logging.getLogger(__name__)


class DocumentExtractor:
    """Extract metadata from document files."""
    
    SUPPORTED_FORMATS = {'.pdf', '.doc', '.docx', '.odt', '.rtf'}
    
    @staticmethod
    def can_extract(file_path: str) -> bool:
        """Check if this extractor can handle the file."""
        return Path(file_path).suffix.lower() in DocumentExtractor.SUPPORTED_FORMATS
    
    @staticmethod
    def extract(file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from document file.
        
        Args:
            file_path: Path to document file
            
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
            'type': 'document',
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
        
        # Extract based on file type
        extension = path.suffix.lower()
        if extension == '.pdf':
            doc_metadata = DocumentExtractor._extract_pdf(file_path)
        elif extension in {'.docx', '.doc'}:
            doc_metadata = DocumentExtractor._extract_docx(file_path)
        elif extension == '.odt':
            doc_metadata = DocumentExtractor._extract_odt(file_path)
        elif extension == '.rtf':
            doc_metadata = DocumentExtractor._extract_rtf(file_path)
        else:
            doc_metadata = {}
        
        if doc_metadata:
            metadata['metadata']['document'] = doc_metadata
        
        return metadata
    
    @staticmethod
    def _extract_pdf(file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF file."""
        try:
            from pdfminer.pdfparser import PDFParser
            from pdfminer.pdfdocument import PDFDocument
            
            with open(file_path, 'rb') as f:
                parser = PDFParser(f)
                doc = PDFDocument(parser)
                
                metadata = {}
                if doc.info:
                    for info in doc.info:
                        for key, value in info.items():
                            try:
                                # Decode bytes to string
                                if isinstance(value, bytes):
                                    value = value.decode('utf-8', errors='ignore')
                                metadata[key.decode() if isinstance(key, bytes) else key] = value
                            except Exception as e:
                                logger.debug(f"Error processing PDF metadata key {key}: {e}")
                
                result = {
                    'author': metadata.get('Author', metadata.get('/Author')),
                    'title': metadata.get('Title', metadata.get('/Title')),
                    'subject': metadata.get('Subject', metadata.get('/Subject')),
                    'creator': metadata.get('Creator', metadata.get('/Creator')),
                    'producer': metadata.get('Producer', metadata.get('/Producer')),
                    'creation_date': format_timestamp(
                        metadata.get('CreationDate', metadata.get('/CreationDate'))
                    ),
                    'modification_date': format_timestamp(
                        metadata.get('ModDate', metadata.get('/ModDate'))
                    ),
                    'keywords': metadata.get('Keywords', metadata.get('/Keywords')),
                    'raw_metadata': sanitize_metadata(metadata)
                }
                
                # Remove None values
                return {k: v for k, v in result.items() if v is not None}
                
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}")
            return {}
    
    @staticmethod
    def _extract_docx(file_path: str) -> Dict[str, Any]:
        """Extract metadata from DOCX file."""
        try:
            from docx import Document
            
            doc = Document(file_path)
            core_props = doc.core_properties
            
            result = {
                'author': core_props.author,
                'title': core_props.title,
                'subject': core_props.subject,
                'keywords': core_props.keywords,
                'comments': core_props.comments,
                'category': core_props.category,
                'created': format_timestamp(core_props.created),
                'modified': format_timestamp(core_props.modified),
                'last_modified_by': core_props.last_modified_by,
                'revision': core_props.revision,
                'version': core_props.version,
                'language': core_props.language,
                'content_status': core_props.content_status
            }
            
            # Remove None values
            return {k: v for k, v in result.items() if v is not None}
            
        except Exception as e:
            logger.error(f"Error extracting DOCX metadata: {e}")
            return {}
    
    @staticmethod
    def _extract_odt(file_path: str) -> Dict[str, Any]:
        """Extract metadata from ODT file."""
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Read meta.xml
                with zf.open('meta.xml') as meta_file:
                    tree = ET.parse(meta_file)
                    root = tree.getroot()
                    
                    # Define namespaces
                    ns = {
                        'meta': 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0',
                        'dc': 'http://purl.org/dc/elements/1.1/'
                    }
                    
                    result = {}
                    
                    # Extract common metadata
                    meta_fields = {
                        'dc:creator': 'author',
                        'dc:title': 'title',
                        'dc:subject': 'subject',
                        'dc:description': 'description',
                        'meta:keyword': 'keywords',
                        'meta:generator': 'generator',
                        'meta:creation-date': 'created',
                        'dc:date': 'modified',
                        'meta:editing-cycles': 'editing_cycles',
                        'meta:editing-duration': 'editing_duration'
                    }
                    
                    for xpath, key in meta_fields.items():
                        elements = root.findall(f'.//{xpath}', ns)
                        if elements and elements[0].text:
                            value = elements[0].text
                            if 'date' in key:
                                value = format_timestamp(value)
                            result[key] = value
                    
                    return result
                    
        except Exception as e:
            logger.error(f"Error extracting ODT metadata: {e}")
            return {}
    
    @staticmethod
    def _extract_rtf(file_path: str) -> Dict[str, Any]:
        """Extract metadata from RTF file."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read(8192).decode('latin-1', errors='ignore')
                
                result = {}
                
                # Extract common RTF metadata fields
                metadata_patterns = {
                    r'\\author\s+([^}]+)': 'author',
                    r'\\title\s+([^}]+)': 'title',
                    r'\\subject\s+([^}]+)': 'subject',
                    r'\\keywords\s+([^}]+)': 'keywords',
                    r'\\operator\s+([^}]+)': 'operator',
                    r'\\company\s+([^}]+)': 'company'
                }
                
                import re
                for pattern, key in metadata_patterns.items():
                    match = re.search(pattern, content)
                    if match:
                        result[key] = match.group(1).strip()
                
                return result
                
        except Exception as e:
            logger.error(f"Error extracting RTF metadata: {e}")
            return {}


