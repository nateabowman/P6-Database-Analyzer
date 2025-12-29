"""Table analyzer for identifying large and problematic tables."""

from typing import Dict, List, Any
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union


class TableAnalyzer:
    """Analyzes tables for size, growth, and warning conditions."""
    
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
    
    def analyze_tables(self, large_table_threshold_mb: float = 1000.0) -> Dict[str, Any]:
        """
        Analyze all tables for size and warning conditions.
        
        Args:
            large_table_threshold_mb: Size threshold in MB for flagging large tables
        
        Returns:
            Dictionary with table analysis results
        """
        results = {
            'status': 'healthy',
            'total_tables': 0,
            'large_tables': [],
            'warning_tables': [],
            'table_details': [],
            'total_size_mb': 0.0,
            'recommendations': []
        }
        
        try:
            table_details = self._get_table_details()
            results['table_details'] = table_details
            results['total_tables'] = len(table_details)
            
            # Calculate total size
            results['total_size_mb'] = sum(
                float(t.get('size_mb', 0) or 0) for t in table_details
            )
            
            # Identify large tables
            for table in table_details:
                size_mb = float(table.get('size_mb', 0) or 0)
                if size_mb >= large_table_threshold_mb:
                    results['large_tables'].append(table)
            
            # Identify warning tables
            results['warning_tables'] = self._identify_warning_tables(table_details)
            
            # Determine overall status
            if results['warning_tables']:
                results['status'] = 'warnings_found'
            if results['large_tables']:
                if results['status'] == 'healthy':
                    results['status'] = 'large_tables'
            
            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(results)
        
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def _get_table_details(self) -> List[Dict]:
        """Get detailed information about all tables."""
        if self.db_type == 'oracle':
            return self._get_oracle_table_details()
        else:
            return self._get_mssql_table_details()
    
    def _get_oracle_table_details(self) -> List[Dict]:
        """Get Oracle table details including size."""
        tables = []
        
        try:
            query = """
                SELECT 
                    t.table_name,
                    t.num_rows,
                    t.avg_row_len,
                    ROUND((t.blocks * ts.block_size) / 1024 / 1024, 2) as size_mb,
                    t.last_analyzed,
                    t.tablespace_name,
                    CASE 
                        WHEN t.num_rows > 0 AND t.last_analyzed < SYSDATE - 7 THEN 'Y'
                        ELSE 'N'
                    END as needs_analyze
                FROM user_tables t
                LEFT JOIN user_tablespaces ts ON t.tablespace_name = ts.tablespace_name
                ORDER BY size_mb DESC NULLS LAST
            """
            
            results = self.connector.execute_query(query)
            for row in results:
                tables.append({
                    'table_name': row.get('table_name'),
                    'num_rows': row.get('num_rows', 0),
                    'avg_row_len': row.get('avg_row_len', 0),
                    'size_mb': row.get('size_mb', 0),
                    'last_analyzed': str(row.get('last_analyzed', '')) if row.get('last_analyzed') else None,
                    'tablespace_name': row.get('tablespace_name'),
                    'needs_analyze': row.get('needs_analyze') == 'Y',
                    'db_type': 'oracle'
                })
        except Exception as e:
            # Fallback to simpler query
            try:
                query = """
                    SELECT 
                        table_name,
                        num_rows,
                        0 as size_mb
                    FROM user_tables
                    ORDER BY num_rows DESC NULLS LAST
                """
                results = self.connector.execute_query(query)
                for row in results:
                    tables.append({
                        'table_name': row.get('table_name'),
                        'num_rows': row.get('num_rows', 0),
                        'size_mb': 0,
                        'db_type': 'oracle',
                        'note': 'Size calculation not available'
                    })
            except:
                pass
        
        return tables
    
    def _get_mssql_table_details(self) -> List[Dict]:
        """Get MSSQL table details including size."""
        tables = []
        
        try:
            query = """
                SELECT 
                    t.name AS table_name,
                    p.rows AS num_rows,
                    ROUND(SUM(a.total_pages) * 8 / 1024.0, 2) AS size_mb,
                    MAX(iu.last_user_update) AS last_updated
                FROM sys.tables t
                INNER JOIN sys.indexes i ON t.object_id = i.object_id
                INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                LEFT JOIN sys.dm_db_index_usage_stats iu ON i.object_id = iu.object_id AND i.index_id = iu.index_id
                WHERE t.is_ms_shipped = 0
                AND i.object_id > 255
                GROUP BY t.name, p.rows
                ORDER BY size_mb DESC
            """
            
            results = self.connector.execute_query(query)
            for row in results:
                tables.append({
                    'table_name': row.get('table_name'),
                    'num_rows': row.get('num_rows', 0),
                    'size_mb': row.get('size_mb', 0),
                    'last_updated': str(row.get('last_updated', '')) if row.get('last_updated') else None,
                    'db_type': 'mssql'
                })
        except Exception as e:
            # Fallback to simpler query
            try:
                query = """
                    SELECT 
                        TABLE_NAME as table_name,
                        0 as num_rows,
                        0 as size_mb
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                """
                results = self.connector.execute_query(query)
                for row in results:
                    tables.append({
                        'table_name': row.get('table_name'),
                        'num_rows': 0,
                        'size_mb': 0,
                        'db_type': 'mssql',
                        'note': 'Size calculation not available'
                    })
            except:
                pass
        
        return tables
    
    def _identify_warning_tables(self, tables: List[Dict]) -> List[Dict]:
        """Identify tables with warning conditions."""
        warnings = []
        
        for table in tables:
            issues = []
            
            # Check for very large row count
            num_rows = table.get('num_rows', 0) or 0
            if num_rows > 10000000:  # 10 million rows
                issues.append('Very large row count')
            
            # Check for tables that need analyze (Oracle)
            if table.get('needs_analyze'):
                issues.append('Statistics outdated')
            
            # Check for zero rows but non-zero size (potential issue)
            if num_rows == 0 and float(table.get('size_mb', 0) or 0) > 10:
                issues.append('Zero rows but significant size')
            
            if issues:
                warning_table = table.copy()
                warning_table['warning_reasons'] = issues
                warnings.append(warning_table)
        
        return warnings
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on table analysis."""
        recommendations = []
        
        large_count = len(results.get('large_tables', []))
        warning_count = len(results.get('warning_tables', []))
        total_size = results.get('total_size_mb', 0)
        
        if large_count > 0:
            recommendations.append(
                f"{large_count} large table(s) detected. "
                "Consider partitioning for tables over 10GB."
            )
            recommendations.append(
                "Review large tables for archiving opportunities."
            )
        
        if warning_count > 0:
            recommendations.append(
                f"{warning_count} table(s) have warning conditions. "
                "Review these tables for optimization opportunities."
            )
        
        if total_size > 50000:  # 50 GB
            recommendations.append(
                f"Total database size is {total_size:.2f} MB. "
                "Consider implementing a data retention policy."
            )
        
        if self.db_type == 'oracle':
            needs_analyze = sum(1 for t in results.get('table_details', []) if t.get('needs_analyze'))
            if needs_analyze > 0:
                recommendations.append(
                    f"{needs_analyze} table(s) need statistics update. "
                    "Run DBMS_STATS.GATHER_TABLE_STATS for better query performance."
                )
        
        if not recommendations:
            recommendations.append("No table-related issues detected.")
        
        return recommendations

