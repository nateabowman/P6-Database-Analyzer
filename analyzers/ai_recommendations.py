"""AI-powered recommendations for database optimization."""

from typing import Dict, List, Any
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union
from utils.logging_config import get_logger
from utils.exceptions import AnalysisError
from utils.metrics import get_metrics
from ml.predictor import get_predictor

logger = get_logger(__name__)
metrics = get_metrics()


class AIRecommendations:
    """Generates AI-powered recommendations."""
    
    def __init__(self, connector: Union[OracleConnector, MSSQLConnector]):
        self.connector = connector
        self.db_type = self._detect_db_type()
        self.predictor = get_predictor()
    
    def _detect_db_type(self) -> str:
        """Detect database type from connector."""
        if isinstance(self.connector, OracleConnector):
            return 'oracle'
        elif isinstance(self.connector, MSSQLConnector):
            return 'mssql'
        else:
            raise ValueError("Unknown connector type")
    
    def generate_recommendations(
        self,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate AI-powered recommendations based on analysis results.
        
        Args:
            analysis_results: Results from various analyses
        
        Returns:
            Dictionary with AI recommendations
        """
        timer_id = metrics.start_timer('analysis.ai_recommendations', {'db_type': self.db_type})
        logger.info("Generating AI-powered recommendations")
        
        results = {
            'status': 'success',
            'recommendations': [],
            'priority_scores': {},
            'predicted_impact': {}
        }
        
        try:
            # Extract features from analysis results
            features = self._extract_features(analysis_results)
            
            # Generate recommendations using ML
            recommendations = self._generate_ml_recommendations(features, analysis_results)
            results['recommendations'] = recommendations
            
            # Calculate priority scores
            for rec in recommendations:
                priority = self._calculate_priority(rec, features)
                results['priority_scores'][rec['id']] = priority
                rec['priority'] = priority
            
            # Predict impact
            results['predicted_impact'] = self._predict_impact(features, recommendations)
            
            metrics.increment('analysis.ai_recommendations.success', {'db_type': self.db_type})
            logger.info(f"Generated {len(recommendations)} AI recommendations")
        
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            metrics.increment('analysis.ai_recommendations.error', {'db_type': self.db_type})
            logger.error(f"AI recommendations failed: {str(e)}", exc_info=True)
            raise AnalysisError(f"AI recommendations failed: {str(e)}")
        finally:
            metrics.stop_timer(timer_id)
        
        return results
    
    def _extract_features(self, analysis_results: Dict[str, Any]) -> Dict[str, float]:
        """Extract features from analysis results for ML."""
        features = {}
        
        # Schema health features
        if 'schema_health' in analysis_results:
            sh = analysis_results['schema_health']
            features['schema_issues_count'] = len(sh.get('issues', []))
            features['missing_indexes_count'] = len(sh.get('missing_indexes', []))
        
        # Index fragmentation features
        if 'index_fragmentation' in analysis_results:
            idx = analysis_results['index_fragmentation']
            features['fragmented_indexes_count'] = len(idx.get('fragmented_indexes', []))
            features['high_fragmentation_count'] = len(idx.get('high_fragmentation', []))
        
        # Table analysis features
        if 'table_analysis' in analysis_results:
            ta = analysis_results['table_analysis']
            features['large_tables_count'] = len(ta.get('large_tables', []))
            features['total_size_mb'] = ta.get('total_size_mb', 0)
        
        return features
    
    def _generate_ml_recommendations(
        self,
        features: Dict[str, float],
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations using ML models."""
        recommendations = []
        
        # Use predictor to generate recommendations
        if self.predictor:
            try:
                ml_recommendations = self.predictor.predict_recommendations(features)
                recommendations.extend(ml_recommendations)
            except Exception as e:
                logger.warning(f"ML prediction failed: {str(e)}. Using rule-based recommendations.")
        
        # Fallback to rule-based recommendations
        if not recommendations:
            recommendations = self._generate_rule_based_recommendations(features, analysis_results)
        
        return recommendations
    
    def _generate_rule_based_recommendations(
        self,
        features: Dict[str, float],
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate rule-based recommendations as fallback."""
        recommendations = []
        
        if features.get('missing_indexes_count', 0) > 0:
            recommendations.append({
                'id': 'rec_missing_indexes',
                'type': 'index_optimization',
                'title': 'Add Missing Indexes',
                'description': f"Found {features['missing_indexes_count']} missing indexes on foreign keys",
                'impact': 'high',
                'effort': 'medium'
            })
        
        if features.get('high_fragmentation_count', 0) > 0:
            recommendations.append({
                'id': 'rec_index_rebuild',
                'type': 'maintenance',
                'title': 'Rebuild Fragmented Indexes',
                'description': f"Found {features['high_fragmentation_count']} highly fragmented indexes",
                'impact': 'high',
                'effort': 'high'
            })
        
        return recommendations
    
    def _calculate_priority(self, recommendation: Dict[str, Any], features: Dict[str, float]) -> float:
        """Calculate priority score for a recommendation."""
        # Simple priority calculation based on impact and effort
        impact_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        effort_scores = {'low': 3, 'medium': 2, 'high': 1}
        
        impact = impact_scores.get(recommendation.get('impact', 'medium'), 2)
        effort = effort_scores.get(recommendation.get('effort', 'medium'), 2)
        
        # Priority = impact / effort
        return impact / effort if effort > 0 else impact
    
    def _predict_impact(
        self,
        features: Dict[str, float],
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Predict impact of implementing recommendations."""
        if self.predictor:
            try:
                return self.predictor.predict_impact(features, recommendations)
            except Exception as e:
                logger.warning(f"Impact prediction failed: {str(e)}")
        
        # Default impact prediction
        return {
            'performance_improvement': 'estimated',
            'risk_reduction': 'estimated',
            'maintenance_cost_reduction': 'estimated'
        }

