"""
Anomaly detection and analysis for MEX.
Identifies suspicious patterns and inconsistencies in metadata.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detect anomalies and suspicious patterns in metadata."""
    
    # Known software release dates for validation
    SOFTWARE_RELEASE_DATES = {
        'photoshop': {'name': 'Adobe Photoshop', 'first_release': 1990},
        'lightroom': {'name': 'Adobe Lightroom', 'first_release': 2007},
        'gimp': {'name': 'GIMP', 'first_release': 1996},
        'word': {'name': 'Microsoft Word', 'first_release': 1983},
        'excel': {'name': 'Microsoft Excel', 'first_release': 1985},
    }
    
    def __init__(self, metadata_list: List[Dict[str, Any]]):
        """
        Initialize anomaly detector.
        
        Args:
            metadata_list: List of metadata dictionaries
        """
        self.metadata_list = metadata_list
        self.anomalies = []
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform anomaly detection on all files.
        
        Returns:
            Dictionary containing detected anomalies and statistics
        """
        for idx, metadata in enumerate(self.metadata_list):
            file_name = metadata.get('file_info', {}).get('name', f'file_{idx}')
            
            # Run all anomaly checks
            self._check_timestamp_anomalies(file_name, metadata)
            self._check_software_anomalies(file_name, metadata)
            self._check_gps_anomalies(file_name, metadata)
            self._check_metadata_tampering(file_name, metadata)
            self._check_file_anomalies(file_name, metadata)
        
        # Build summary
        summary = self._build_summary()
        
        return {
            'total_files_analyzed': len(self.metadata_list),
            'total_anomalies': len(self.anomalies),
            'anomalies': self.anomalies,
            'summary': summary
        }
    
    def _check_timestamp_anomalies(self, file_name: str, metadata: Dict[str, Any]):
        """Check for timestamp inconsistencies."""
        timestamps = metadata.get('timestamps', {})
        
        try:
            # Parse timestamps
            created = date_parser.parse(timestamps.get('created')) if timestamps.get('created') else None
            modified = date_parser.parse(timestamps.get('modified')) if timestamps.get('modified') else None
            
            # Check if modified is before created
            if created and modified and modified < created:
                self.anomalies.append({
                    'file': file_name,
                    'type': 'timestamp_inconsistency',
                    'severity': 'high',
                    'description': f'Modified date ({modified}) is before created date ({created})',
                    'details': {
                        'created': str(created),
                        'modified': str(modified)
                    }
                })
            
            # Check for future dates
            now = datetime.now()
            if created and created > now:
                self.anomalies.append({
                    'file': file_name,
                    'type': 'future_timestamp',
                    'severity': 'high',
                    'description': f'Created date is in the future: {created}',
                    'details': {'created': str(created)}
                })
            
            if modified and modified > now:
                self.anomalies.append({
                    'file': file_name,
                    'type': 'future_timestamp',
                    'severity': 'high',
                    'description': f'Modified date is in the future: {modified}',
                    'details': {'modified': str(modified)}
                })
            
            # Check EXIF vs file system timestamp discrepancy
            exif_dates = metadata.get('metadata', {}).get('exif', {}).get('dates', {})
            if exif_dates.get('datetime_original'):
                exif_date = date_parser.parse(exif_dates['datetime_original'])
                if created and abs((exif_date - created).days) > 365:
                    self.anomalies.append({
                        'file': file_name,
                        'type': 'timestamp_discrepancy',
                        'severity': 'medium',
                        'description': f'EXIF date differs significantly from file system date',
                        'details': {
                            'exif_date': str(exif_date),
                            'file_created': str(created),
                            'difference_days': abs((exif_date - created).days)
                        }
                    })
        
        except Exception as e:
            logger.debug(f"Error checking timestamps for {file_name}: {e}")
    
    def _check_software_anomalies(self, file_name: str, metadata: Dict[str, Any]):
        """Check for software-related anomalies."""
        # Check image software
        img_meta = metadata.get('metadata', {}).get('exif', {})
        software = img_meta.get('software', {}).get('software', '')
        
        if software:
            # Check if software date makes sense
            exif_dates = img_meta.get('dates', {})
            if exif_dates.get('datetime_original'):
                try:
                    file_date = date_parser.parse(exif_dates['datetime_original'])
                    
                    # Check against known software release dates
                    for key, info in self.SOFTWARE_RELEASE_DATES.items():
                        if key in software.lower():
                            if file_date.year < info['first_release']:
                                self.anomalies.append({
                                    'file': file_name,
                                    'type': 'impossible_software_date',
                                    'severity': 'high',
                                    'description': f'File claims to be created with {info["name"]} before it existed',
                                    'details': {
                                        'software': software,
                                        'file_date': str(file_date),
                                        'software_release': info['first_release']
                                    }
                                })
                except:
                    pass
        
        # Check for multiple different software in edit history
        doc = metadata.get('metadata', {}).get('document', {})
        creator = doc.get('creator', '').lower()
        producer = doc.get('producer', '').lower()
        
        if creator and producer and creator != producer:
            # Different creator and producer might indicate editing
            if not any(x in creator for x in ['microsoft', 'adobe', 'libre']) or \
               not any(x in producer for x in ['microsoft', 'adobe', 'libre']):
                self.anomalies.append({
                    'file': file_name,
                    'type': 'software_inconsistency',
                    'severity': 'low',
                    'description': 'Document shows different creation and production software',
                    'details': {
                        'creator': creator,
                        'producer': producer
                    }
                })
    
    def _check_gps_anomalies(self, file_name: str, metadata: Dict[str, Any]):
        """Check for GPS-related anomalies."""
        img_meta = metadata.get('metadata', {}).get('exif', {})
        gps = img_meta.get('gps', {})
        
        if gps.get('coordinates'):
            coords = gps['coordinates']
            lat = coords.get('latitude', 0)
            lon = coords.get('longitude', 0)
            
            # Check for invalid coordinates
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                self.anomalies.append({
                    'file': file_name,
                    'type': 'invalid_gps',
                    'severity': 'high',
                    'description': 'GPS coordinates are out of valid range',
                    'details': {'latitude': lat, 'longitude': lon}
                })
            
            # Check for null island (0,0)
            if abs(lat) < 0.1 and abs(lon) < 0.1:
                self.anomalies.append({
                    'file': file_name,
                    'type': 'suspicious_gps',
                    'severity': 'medium',
                    'description': 'GPS coordinates near (0,0) - possible default value',
                    'details': {'latitude': lat, 'longitude': lon}
                })
            
            # Check GPS timestamp vs EXIF timestamp
            exif_dates = img_meta.get('dates', {})
            if exif_dates.get('datetime_original') and gps.get('timestamp'):
                try:
                    exif_dt = date_parser.parse(exif_dates['datetime_original'])
                    # GPS timestamp is usually just time, but check if available
                    # This is a simplified check
                    pass
                except:
                    pass
    
    def _check_metadata_tampering(self, file_name: str, metadata: Dict[str, Any]):
        """Check for signs of metadata tampering."""
        # Check if metadata is suspiciously minimal
        meta_content = metadata.get('metadata', {})
        
        file_type = metadata.get('file_info', {}).get('type')
        
        # Images should have EXIF data
        if file_type == 'image':
            if not meta_content.get('exif') and not meta_content.get('image'):
                self.anomalies.append({
                    'file': file_name,
                    'type': 'missing_metadata',
                    'severity': 'medium',
                    'description': 'Image file has no EXIF metadata - may have been stripped',
                    'details': {}
                })
        
        # Documents should have author/creator
        if file_type == 'document':
            doc = meta_content.get('document', {})
            if not any([doc.get('author'), doc.get('creator'), doc.get('producer')]):
                self.anomalies.append({
                    'file': file_name,
                    'type': 'missing_metadata',
                    'severity': 'low',
                    'description': 'Document has no author/creator metadata',
                    'details': {}
                })
        
        # Check for metadata-only modifications
        timestamps = metadata.get('timestamps', {})
        if timestamps.get('created') and timestamps.get('modified'):
            try:
                created = date_parser.parse(timestamps['created'])
                modified = date_parser.parse(timestamps['modified'])
                
                # If file was modified but size is suspiciously small change
                # (This would require tracking file history, simplified here)
                pass
            except:
                pass
    
    def _check_file_anomalies(self, file_name: str, metadata: Dict[str, Any]):
        """Check for general file anomalies."""
        file_info = metadata.get('file_info', {})
        
        # Check for suspicious file size
        size = file_info.get('size', 0)
        file_type = file_info.get('type')
        
        # Very small files that shouldn't be
        if file_type == 'image' and size < 100:
            self.anomalies.append({
                'file': file_name,
                'type': 'suspicious_file_size',
                'severity': 'low',
                'description': f'Image file is suspiciously small ({size} bytes)',
                'details': {'size': size}
            })
        
        # Check hash collisions (same hash, different names)
        # This would be checked across all files in correlate module
        
        # Check for hidden data in archives
        if file_type == 'archive':
            archive_meta = metadata.get('metadata', {}).get('archive', {})
            if archive_meta.get('file_count', 0) == 0:
                self.anomalies.append({
                    'file': file_name,
                    'type': 'empty_archive',
                    'severity': 'low',
                    'description': 'Archive contains no files',
                    'details': {}
                })
    
    def _build_summary(self) -> Dict[str, Any]:
        """Build anomaly summary statistics."""
        summary = {
            'by_severity': {'high': 0, 'medium': 0, 'low': 0},
            'by_type': {},
            'affected_files': set()
        }
        
        for anomaly in self.anomalies:
            # Count by severity
            severity = anomaly.get('severity', 'low')
            summary['by_severity'][severity] += 1
            
            # Count by type
            anom_type = anomaly.get('type', 'unknown')
            summary['by_type'][anom_type] = summary['by_type'].get(anom_type, 0) + 1
            
            # Track affected files
            summary['affected_files'].add(anomaly.get('file'))
        
        summary['affected_files'] = list(summary['affected_files'])
        
        return summary


