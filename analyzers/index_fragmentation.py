"""Index fragmentation analyzer for P6 databases."""

from typing import Dict, List, Any
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union
from utils.logging_config import get_logger
from utils.exceptions import AnalysisError
from utils.metrics import get_metrics

logger = get_logger(__name__)
metrics = get_metrics()


class IndexFragmentationChecker:
    """Checks index fragmentation in P6 databases."""
    
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
    
    def check_fragmentation(self, threshold: float = 30.0) -> Dict[str, Any]:
        """
        Check index fragmentation.
        
        Args:
            threshold: Fragmentation percentage threshold (default 30%)
        
        Returns:
            Dictionary with fragmentation analysis results
        """
        timer_id = metrics.start_timer('analysis.index_fragmentation', {'db_type': self.db_type})
        logger.info(f"Starting index fragmentation check (threshold: {threshold}%)")
        
        results = {
            'status': 'healthy',
            'total_indexes': 0,
            'fragmented_indexes': [],
            'high_fragmentation': [],
            'medium_fragmentation': [],
            'low_fragmentation': [],
            'recommendations': []
        }
        
        try:
            fragmented_indexes = self._get_fragmented_indexes(threshold)
            results['fragmented_indexes'] = fragmented_indexes
            results['total_indexes'] = len(fragmented_indexes)
            logger.info(f"Found {len(fragmented_indexes)} fragmented indexes")
            
            for idx in fragmented_indexes:
                frag_pct = idx.get('fragmentation_percent', 0)
                if frag_pct >= 50:
                    results['high_fragmentation'].append(idx)
                    results['status'] = 'critical'
                elif frag_pct >= threshold:
                    results['medium_fragmentation'].append(idx)
                    if results['status'] == 'healthy':
                        results['status'] = 'warning'
                else:
                    results['low_fragmentation'].append(idx)
            
            if results['high_fragmentation']:
                logger.warning(f"Found {len(results['high_fragmentation'])} indexes with high fragmentation (>=50%)")
            
            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(results)
            
            metrics.increment('analysis.index_fragmentation.success', {'db_type': self.db_type})
            logger.info(f"Index fragmentation check completed with status: {results['status']}")
            
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            metrics.increment('analysis.index_fragmentation.error', {'db_type': self.db_type})
            logger.error(f"Index fragmentation check failed: {str(e)}", exc_info=True)
            raise AnalysisError(f"Index fragmentation check failed: {str(e)}")
        finally:
            metrics.stop_timer(timer_id)
        
        return results
    
    def _get_fragmented_indexes(self, threshold: float) -> List[Dict]:
        """Get list of fragmented indexes."""
        if self.db_type == 'oracle':
            return self._get_oracle_fragmentation()
        else:
            return self._get_mssql_fragmentation(threshold)
    
    def _get_oracle_fragmentation(self) -> List[Dict]:
        """Get Oracle index fragmentation using ANALYZE results."""
        fragmented = []
        
        try:
            # Oracle uses ANALYZE INDEX to check fragmentation
            # This is a simplified check - in production, you'd run ANALYZE first
            query = """
                SELECT 
                    i.index_name,
                    i.table_name,
                    i.num_rows,
                    i.distinct_keys,
                    i.blevel,
                    CASE 
                        WHEN i.num_rows > 0 THEN 
                            ROUND((1 - (i.distinct_keys / NULLIF(i.num_rows, 0))) * 100, 2)
                        ELSE 0
                    END as estimated_fragmentation
                FROM user_indexes i
                WHERE i.index_type = 'NORMAL'
                AND i.num_rows > 1000
                ORDER BY estimated_fragmentation DESC
            """
            
            results = self.connector.execute_query(query)
            for row in results:
                frag_pct = float(row.get('estimated_fragmentation', 0) or 0)
                if frag_pct > 0:
                    fragmented.append({
                        'index_name': row.get('index_name'),
                        'table_name': row.get('table_name'),
                        'fragmentation_percent': frag_pct,
                        'num_rows': row.get('num_rows'),
                        'blevel': row.get('blevel'),
                        'db_type': 'oracle'
                    })
        except Exception as e:
            # If query fails, return empty list
            pass
        
        return fragmented
    
    def _get_mssql_fragmentation(self, threshold: float) -> List[Dict]:
        """Get MSSQL index fragmentation using sys.dm_db_index_physical_stats."""
        fragmented = []
        
        try:
            query = """
                SELECT 
                    OBJECT_NAME(ips.object_id) AS table_name,
                    i.name AS index_name,
                    ips.avg_fragmentation_in_percent,
                    ips.page_count,
                    ips.fragment_count,
                    ips.avg_fragment_size_in_pages
                FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
                INNER JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
                WHERE ips.avg_fragmentation_in_percent > ?
                AND ips.page_count > 100
                ORDER BY ips.avg_fragmentation_in_percent DESC
            """
            
            results = self.connector.execute_query(query, {'threshold': threshold})
            for row in results:
                fragmented.append({
                    'index_name': row.get('index_name'),
                    'table_name': row.get('table_name'),
                    'fragmentation_percent': float(row.get('avg_fragmentation_in_percent', 0)),
                    'page_count': row.get('page_count'),
                    'fragment_count': row.get('fragment_count'),
                    'db_type': 'mssql'
                })
        except Exception as e:
            # If DMV is not available or query fails
            try:
                # Fallback to simpler query
                query = """
                    SELECT 
                        OBJECT_NAME(object_id) AS table_name,
                        name AS index_name,
                        0 as avg_fragmentation_in_percent
                    FROM sys.indexes
                    WHERE object_id > 100
                    AND type > 0
                """
                results = self.connector.execute_query(query)
                for row in results:
                    fragmented.append({
                        'index_name': row.get('index_name'),
                        'table_name': row.get('table_name'),
                        'fragmentation_percent': 0,
                        'db_type': 'mssql',
                        'note': 'Fragmentation data not available - requires sys.dm_db_index_physical_stats permissions'
                    })
            except:
                pass
        
        return fragmented
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate remediation recommendations."""
        recommendations = []
        
        high_frag = len(results.get('high_fragmentation', []))
        medium_frag = len(results.get('medium_fragmentation', []))
        
        if high_frag > 0:
            recommendations.append(
                f"URGENT: {high_frag} indexes have fragmentation > 50%. "
                "Rebuild these indexes immediately to improve performance."
            )
        
        if medium_frag > 0:
            recommendations.append(
                f"WARNING: {medium_frag} indexes have fragmentation > 30%. "
                "Consider reorganizing or rebuilding these indexes during maintenance window."
            )
        
        if self.db_type == 'oracle':
            recommendations.append(
                "For Oracle: Run 'ALTER INDEX <index_name> REBUILD' for fragmented indexes."
            )
        else:
            recommendations.append(
                "For MSSQL: Use 'ALTER INDEX <index_name> ON <table> REBUILD' or REORGANIZE."
            )
        
        if not recommendations:
            recommendations.append("No index fragmentation issues detected.")
        
        return recommendations

