"""Anomaly detection using statistical methods."""

from typing import Dict, List, Any
import numpy as np
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union
from utils.logging_config import get_logger
from utils.exceptions import AnalysisError
from utils.metrics import get_metrics

logger = get_logger(__name__)
metrics = get_metrics()


class AnomalyDetector:
    """Detects anomalies in database metrics."""
    
    def __init__(self, connector: Union[OracleConnector, MSSQLConnector]):
        self.connector = connector
        self.db_type = self._detect_db_type()
    
    def _detect_db_type(self) -> str:
        """Detect database type from connector."""
        if isinstance(self.connector, OracleConnector):
            return 'oracle'
        elif isinstance(self.connector, MSSQLConnector):
            return 'mssql'
        else:
            raise ValueError("Unknown connector type")
    
    def detect_anomalies(
        self,
        metric_data: List[float],
        method: str = "zscore",
        threshold: float = 3.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies in metric data.
        
        Args:
            metric_data: List of metric values
            method: Detection method (zscore, iqr)
            threshold: Anomaly threshold
        
        Returns:
            Dictionary with anomaly detection results
        """
        timer_id = metrics.start_timer('analysis.anomaly_detection')
        logger.info(f"Starting anomaly detection using {method} method")
        
        results = {
            'status': 'success',
            'method': method,
            'anomalies': [],
            'anomaly_count': 0,
            'anomaly_indices': []
        }
        
        try:
            if len(metric_data) < 3:
                results['status'] = 'insufficient_data'
                results['message'] = 'Need at least 3 data points'
                return results
            
            data_array = np.array(metric_data)
            
            if method == "zscore":
                anomalies = self._zscore_detection(data_array, threshold)
            elif method == "iqr":
                anomalies = self._iqr_detection(data_array)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            results['anomalies'] = [
                {
                    'index': int(idx),
                    'value': float(data_array[idx]),
                    'zscore': float(anomalies['zscores'][idx]) if 'zscores' in anomalies else None
                }
                for idx in anomalies['indices']
            ]
            results['anomaly_count'] = len(results['anomalies'])
            results['anomaly_indices'] = [int(idx) for idx in anomalies['indices']]
            
            metrics.increment('analysis.anomaly_detection.success')
            logger.info(f"Anomaly detection completed: {results['anomaly_count']} anomalies found")
        
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            metrics.increment('analysis.anomaly_detection.error')
            logger.error(f"Anomaly detection failed: {str(e)}", exc_info=True)
            raise AnalysisError(f"Anomaly detection failed: {str(e)}")
        finally:
            metrics.stop_timer(timer_id)
        
        return results
    
    def _zscore_detection(self, data: np.ndarray, threshold: float) -> Dict[str, Any]:
        """Detect anomalies using Z-score method."""
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return {'indices': [], 'zscores': np.zeros_like(data)}
        
        zscores = np.abs((data - mean) / std)
        anomaly_indices = np.where(zscores > threshold)[0]
        
        return {
            'indices': anomaly_indices,
            'zscores': zscores,
            'mean': mean,
            'std': std
        }
    
    def _iqr_detection(self, data: np.ndarray) -> Dict[str, Any]:
        """Detect anomalies using IQR (Interquartile Range) method."""
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        anomaly_indices = np.where((data < lower_bound) | (data > upper_bound))[0]
        
        return {
            'indices': anomaly_indices,
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound
        }

