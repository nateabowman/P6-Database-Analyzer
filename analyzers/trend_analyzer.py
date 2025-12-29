"""Trend analysis for historical data patterns."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union
from utils.logging_config import get_logger
from utils.exceptions import AnalysisError
from utils.metrics import get_metrics
from storage.repository import get_repository

logger = get_logger(__name__)
metrics = get_metrics()


class TrendAnalyzer:
    """Analyzes trends in historical analysis data."""
    
    def __init__(self, connector: Union[OracleConnector, MSSQLConnector]):
        self.connector = connector
        self.db_type = self._detect_db_type()
        self.repository = get_repository()
    
    def _detect_db_type(self) -> str:
        """Detect database type from connector."""
        if isinstance(self.connector, OracleConnector):
            return 'oracle'
        elif isinstance(self.connector, MSSQLConnector):
            return 'mssql'
        else:
            raise ValueError("Unknown connector type")
    
    def analyze_trends(
        self,
        analysis_type: str,
        days: int = 30,
        metric: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze trends for a specific analysis type.
        
        Args:
            analysis_type: Type of analysis to analyze
            days: Number of days to look back
            metric: Specific metric to analyze
        
        Returns:
            Dictionary with trend analysis results
        """
        timer_id = metrics.start_timer('analysis.trends', {'analysis_type': analysis_type})
        logger.info(f"Starting trend analysis for {analysis_type} over {days} days")
        
        results = {
            'status': 'success',
            'analysis_type': analysis_type,
            'period_days': days,
            'trends': [],
            'summary': {}
        }
        
        try:
            # Get historical data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            historical_data = self.repository.get_analysis_history(
                analysis_type=analysis_type,
                start_date=start_date,
                end_date=end_date
            )
            
            if not historical_data:
                results['status'] = 'no_data'
                results['message'] = 'No historical data available'
                return results
            
            # Analyze trends
            trends = self._calculate_trends(historical_data, metric)
            results['trends'] = trends
            
            # Generate summary
            results['summary'] = self._generate_summary(trends)
            
            metrics.increment('analysis.trends.success', {'analysis_type': analysis_type})
            logger.info("Trend analysis completed")
        
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            metrics.increment('analysis.trends.error', {'analysis_type': analysis_type})
            logger.error(f"Trend analysis failed: {str(e)}", exc_info=True)
            raise AnalysisError(f"Trend analysis failed: {str(e)}")
        finally:
            metrics.stop_timer(timer_id)
        
        return results
    
    def _calculate_trends(
        self,
        historical_data: List[Dict[str, Any]],
        metric: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Calculate trends from historical data."""
        trends = []
        
        # Group by date
        daily_data = {}
        for record in historical_data:
            date = record.get('created_at', datetime.utcnow())
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            date_key = date.date()
            
            if date_key not in daily_data:
                daily_data[date_key] = []
            daily_data[date_key].append(record)
        
        # Calculate daily metrics
        for date, records in sorted(daily_data.items()):
            if metric:
                values = [r.get('results', {}).get(metric) for r in records if r.get('results', {}).get(metric)]
            else:
                # Default: count of issues
                values = [len(r.get('results', {}).get('issues', [])) for r in records]
            
            if values:
                trend_point = {
                    'date': date.isoformat(),
                    'count': len(records),
                    'avg_value': sum(values) / len(values) if values else 0,
                    'min_value': min(values) if values else 0,
                    'max_value': max(values) if values else 0
                }
                trends.append(trend_point)
        
        return trends
    
    def _generate_summary(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from trends."""
        if not trends:
            return {}
        
        values = [t.get('avg_value', 0) for t in trends]
        
        # Calculate trend direction
        if len(values) >= 2:
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            
            if second_half > first_half * 1.1:
                direction = "increasing"
            elif second_half < first_half * 0.9:
                direction = "decreasing"
            else:
                direction = "stable"
        else:
            direction = "insufficient_data"
        
        return {
            'total_points': len(trends),
            'avg_value': sum(values) / len(values) if values else 0,
            'min_value': min(values) if values else 0,
            'max_value': max(values) if values else 0,
            'trend_direction': direction
        }

