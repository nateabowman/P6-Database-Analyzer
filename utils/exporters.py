"""Additional export formats for analysis results."""

import csv
import json
from typing import Dict, Any, List
from pathlib import Path
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DataExporter:
    """Exports analysis results to various formats."""
    
    @staticmethod
    def export_to_csv(results: Dict[str, Any], filename: str):
        """
        Export results to CSV format.
        
        Args:
            results: Analysis results dictionary
            filename: Output filename
        """
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['Analysis Type', 'Status', 'Details'])
                
                # Write results
                for analysis_type, data in results.items():
                    if isinstance(data, dict):
                        status = data.get('status', 'unknown')
                        details = json.dumps(data, default=str)
                        writer.writerow([analysis_type, status, details])
            
            logger.info(f"Results exported to CSV: {filename}")
        
        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")
            raise
    
    @staticmethod
    def export_to_json(results: Dict[str, Any], filename: str):
        """
        Export results to JSON format.
        
        Args:
            results: Analysis results dictionary
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results exported to JSON: {filename}")
        
        except Exception as e:
            logger.error(f"Failed to export JSON: {str(e)}")
            raise

