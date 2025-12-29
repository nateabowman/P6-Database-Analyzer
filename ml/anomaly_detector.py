"""ML-based anomaly detection."""

from typing import Dict, List, Any
import numpy as np
from sklearn.ensemble import IsolationForest
from utils.logging_config import get_logger

logger = get_logger(__name__)


class MLAnomalyDetector:
    """Machine learning-based anomaly detector."""
    
    def __init__(self, contamination: float = 0.1):
        """
        Initialize ML anomaly detector.
        
        Args:
            contamination: Expected proportion of anomalies
        """
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_fitted = False
    
    def fit(self, data: np.ndarray):
        """
        Fit the anomaly detection model.
        
        Args:
            data: Training data (n_samples, n_features)
        """
        try:
            self.model.fit(data)
            self.is_fitted = True
            logger.info("Anomaly detection model fitted")
        except Exception as e:
            logger.error(f"Failed to fit model: {str(e)}")
            raise
    
    def predict(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Predict anomalies in data.
        
        Args:
            data: Data to analyze (n_samples, n_features)
        
        Returns:
            Dictionary with predictions
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        try:
            predictions = self.model.predict(data)
            anomaly_scores = self.model.score_samples(data)
            
            # -1 = anomaly, 1 = normal
            anomaly_indices = np.where(predictions == -1)[0]
            
            return {
                'anomalies': anomaly_indices.tolist(),
                'anomaly_scores': anomaly_scores.tolist(),
                'anomaly_count': len(anomaly_indices),
                'normal_count': len(predictions) - len(anomaly_indices)
            }
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise

