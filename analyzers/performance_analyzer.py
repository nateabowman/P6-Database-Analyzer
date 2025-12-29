"""Query performance analyzer for P6 databases."""

from typing import Dict, List, Any
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union
from utils.logging_config import get_logger
from utils.exceptions import AnalysisError
from utils.metrics import get_metrics

logger = get_logger(__name__)
metrics = get_metrics()


class PerformanceAnalyzer:
    """Analyzes query performance in P6 databases."""
    
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
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze query performance."""
        timer_id = metrics.start_timer('analysis.performance', {'db_type': self.db_type})
        logger.info("Starting performance analysis")
        
        results = {
            'status': 'healthy',
            'slow_queries': [],
            'missing_indexes': [],
            'table_scans': [],
            'recommendations': []
        }
        
        try:
            if self.db_type == 'oracle':
                results.update(self._analyze_oracle_performance())
            else:
                results.update(self._analyze_mssql_performance())
            
            metrics.increment('analysis.performance.success', {'db_type': self.db_type})
            logger.info("Performance analysis completed")
        
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            metrics.increment('analysis.performance.error', {'db_type': self.db_type})
            logger.error(f"Performance analysis failed: {str(e)}", exc_info=True)
            raise AnalysisError(f"Performance analysis failed: {str(e)}")
        finally:
            metrics.stop_timer(timer_id)
        
        return results
    
    def _analyze_oracle_performance(self) -> Dict[str, Any]:
        """Analyze Oracle performance."""
        results = {}
        
        # Get slow queries from v$sql
        query = """
            SELECT 
                sql_text,
                elapsed_time / 1000000 as elapsed_seconds,
                executions,
                buffer_gets,
                disk_reads
            FROM v$sql
            WHERE elapsed_time > 1000000  -- More than 1 second
            ORDER BY elapsed_time DESC
            FETCH FIRST 10 ROWS ONLY
        """
        
        try:
            slow_queries = self.connector.execute_query(query)
            results['slow_queries'] = slow_queries
        except Exception as e:
            logger.warning(f"Could not retrieve slow queries: {str(e)}")
            results['slow_queries'] = []
        
        return results
    
    def _analyze_mssql_performance(self) -> Dict[str, Any]:
        """Analyze MSSQL performance."""
        results = {}
        
        # Get slow queries from sys.dm_exec_query_stats
        query = """
            SELECT TOP 10
                SUBSTRING(qt.text, (qs.statement_start_offset/2)+1,
                    ((CASE qs.statement_end_offset
                        WHEN -1 THEN DATALENGTH(qt.text)
                        ELSE qs.statement_end_offset
                    END - qs.statement_start_offset)/2)+1) as query_text,
                qs.total_elapsed_time / 1000000.0 as elapsed_seconds,
                qs.execution_count,
                qs.total_logical_reads,
                qs.total_physical_reads
            FROM sys.dm_exec_query_stats qs
            CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
            WHERE qs.total_elapsed_time > 1000000  -- More than 1 second
            ORDER BY qs.total_elapsed_time DESC
        """
        
        try:
            slow_queries = self.connector.execute_query(query)
            results['slow_queries'] = slow_queries
        except Exception as e:
            logger.warning(f"Could not retrieve slow queries: {str(e)}")
            results['slow_queries'] = []
        
        return results

