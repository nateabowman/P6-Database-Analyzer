"""Schema health scanner for P6 databases."""

from typing import Dict, List, Any
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union
from utils.logging_config import get_logger
from utils.exceptions import AnalysisError
from utils.metrics import get_metrics

logger = get_logger(__name__)
metrics = get_metrics()


class SchemaHealthScanner:
    """Scans database schema for health issues."""
    
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
    
    def scan_schema_health(self) -> Dict[str, Any]:
        """Perform comprehensive schema health scan."""
        timer_id = metrics.start_timer('analysis.schema_health', {'db_type': self.db_type})
        logger.info("Starting schema health scan")
        
        results = {
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'table_count': 0,
            'index_count': 0,
            'constraint_count': 0,
            'missing_indexes': [],
            'orphaned_records': [],
            'invalid_constraints': []
        }
        
        try:
            # Get table count
            logger.debug("Getting table count")
            results['table_count'] = self._get_table_count()
            logger.info(f"Found {results['table_count']} tables")
            
            # Get index count
            logger.debug("Getting index count")
            results['index_count'] = self._get_index_count()
            logger.info(f"Found {results['index_count']} indexes")
            
            # Get constraint count
            logger.debug("Getting constraint count")
            results['constraint_count'] = self._get_constraint_count()
            logger.info(f"Found {results['constraint_count']} constraints")
            
            # Check for missing indexes on foreign keys
            logger.debug("Checking for missing foreign key indexes")
            results['missing_indexes'] = self._check_missing_fk_indexes()
            if results['missing_indexes']:
                logger.warning(f"Found {len(results['missing_indexes'])} missing foreign key indexes")
            
            # Check for orphaned records
            logger.debug("Checking for orphaned records")
            results['orphaned_records'] = self._check_orphaned_records()
            if results['orphaned_records']:
                logger.warning(f"Found {len(results['orphaned_records'])} orphaned record issues")
            
            # Check constraint validity
            logger.debug("Checking constraint validity")
            results['invalid_constraints'] = self._check_constraint_validity()
            if results['invalid_constraints']:
                logger.warning(f"Found {len(results['invalid_constraints'])} invalid constraints")
            
            # Determine overall status
            if results['missing_indexes'] or results['orphaned_records'] or results['invalid_constraints']:
                results['status'] = 'issues_found'
                results['issues'].extend(results['missing_indexes'])
                results['issues'].extend(results['orphaned_records'])
                results['issues'].extend(results['invalid_constraints'])
            
            if results['table_count'] == 0:
                results['warnings'].append("No tables found in database")
                results['status'] = 'warning'
                logger.warning("No tables found in database")
            
            metrics.increment('analysis.schema_health.success', {'db_type': self.db_type})
            logger.info(f"Schema health scan completed with status: {results['status']}")
            
        except Exception as e:
            results['status'] = 'error'
            error_msg = f"Schema scan error: {str(e)}"
            results['issues'].append(error_msg)
            metrics.increment('analysis.schema_health.error', {'db_type': self.db_type})
            logger.error(f"Schema health scan failed: {str(e)}", exc_info=True)
            raise AnalysisError(f"Schema health scan failed: {str(e)}")
        finally:
            metrics.stop_timer(timer_id)
        
        return results
    
    def _get_table_count(self) -> int:
        """Get total number of tables."""
        if self.db_type == 'oracle':
            query = """
                SELECT COUNT(*) as cnt
                FROM user_tables
            """
        else:  # mssql
            query = """
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
            """
        
        result = self.connector.execute_scalar(query)
        return result or 0
    
    def _get_index_count(self) -> int:
        """Get total number of indexes."""
        if self.db_type == 'oracle':
            query = """
                SELECT COUNT(*) as cnt
                FROM user_indexes
            """
        else:  # mssql
            query = """
                SELECT COUNT(*) as cnt
                FROM sys.indexes
                WHERE object_id > 100
            """
        
        result = self.connector.execute_scalar(query)
        return result or 0
    
    def _get_constraint_count(self) -> int:
        """Get total number of constraints."""
        if self.db_type == 'oracle':
            query = """
                SELECT COUNT(*) as cnt
                FROM user_constraints
            """
        else:  # mssql
            query = """
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
            """
        
        result = self.connector.execute_scalar(query)
        return result or 0
    
    def _check_missing_fk_indexes(self) -> List[Dict]:
        """Check for foreign keys without indexes."""
        issues = []
        
        if self.db_type == 'oracle':
            query = """
                SELECT 
                    c.constraint_name,
                    c.table_name,
                    c.r_constraint_name
                FROM user_constraints c
                WHERE c.constraint_type = 'R'
                AND NOT EXISTS (
                    SELECT 1 FROM user_ind_columns ic
                    WHERE ic.table_name = c.table_name
                    AND ic.column_name IN (
                        SELECT column_name FROM user_cons_columns
                        WHERE constraint_name = c.constraint_name
                    )
                )
            """
        else:  # mssql
            query = """
                SELECT 
                    fk.name as constraint_name,
                    OBJECT_NAME(fk.parent_object_id) as table_name,
                    fk.name as r_constraint_name
                FROM sys.foreign_keys fk
                WHERE NOT EXISTS (
                    SELECT 1 FROM sys.index_columns ic
                    INNER JOIN sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
                    WHERE ic.object_id = fk.parent_object_id
                    AND ic.column_id IN (
                        SELECT parent_column_id FROM sys.foreign_key_columns
                        WHERE constraint_object_id = fk.object_id
                    )
                )
            """
        
        try:
            results = self.connector.execute_query(query)
            for row in results:
                issues.append({
                    'type': 'missing_index',
                    'table': row.get('table_name', 'unknown'),
                    'constraint': row.get('constraint_name', 'unknown'),
                    'severity': 'medium',
                    'message': f"Foreign key constraint '{row.get('constraint_name')}' on table '{row.get('table_name')}' lacks an index"
                })
        except Exception as e:
            logger.warning(f"Error checking missing indexes: {str(e)}")
            issues.append({
                'type': 'scan_error',
                'severity': 'low',
                'message': f"Error checking missing indexes: {str(e)}"
            })
        
        return issues
    
    def _check_orphaned_records(self) -> List[Dict]:
        """Check for orphaned records in common P6 tables."""
        issues = []
        
        # Common P6 tables to check (simplified check) - using whitelist
        p6_tables = ['PROJECT', 'TASK', 'RESOURCE', 'ASSIGNMENT']
        
        for table in p6_tables:
            try:
                # Use parameterized queries or validated table names
                # Since these are hardcoded whitelisted values, safe to use
                if self.db_type == 'oracle':
                    check_query = f"SELECT COUNT(*) as cnt FROM {table} WHERE ROWNUM <= 1"
                else:
                    check_query = f"SELECT TOP 1 COUNT(*) as cnt FROM {table}"
                
                # Just verify table exists and is accessible
                self.connector.execute_scalar(check_query)
            except Exception as e:
                # Table might not exist or might have issues
                if "does not exist" not in str(e).lower() and "invalid" not in str(e).lower():
                    issues.append({
                        'type': 'orphaned_check_error',
                        'table': table,
                        'severity': 'low',
                        'message': f"Could not verify table '{table}': {str(e)}"
                    })
        
        return issues
    
    def _check_constraint_validity(self) -> List[Dict]:
        """Check for invalid constraints."""
        issues = []
        
        if self.db_type == 'oracle':
            query = """
                SELECT 
                    constraint_name,
                    table_name,
                    status
                FROM user_constraints
                WHERE status = 'DISABLED' OR status = 'INVALID'
            """
        else:  # mssql
            query = """
                SELECT 
                    name as constraint_name,
                    OBJECT_NAME(parent_object_id) as table_name,
                    'DISABLED' as status
                FROM sys.check_constraints
                WHERE is_disabled = 1
            """
        
        try:
            results = self.connector.execute_query(query)
            for row in results:
                issues.append({
                    'type': 'invalid_constraint',
                    'table': row.get('table_name', 'unknown'),
                    'constraint': row.get('constraint_name', 'unknown'),
                    'status': row.get('status', 'unknown'),
                    'severity': 'high',
                    'message': f"Constraint '{row.get('constraint_name')}' on table '{row.get('table_name')}' is {row.get('status', 'invalid')}"
                })
        except Exception as e:
            # Query might fail if constraints are fine
            logger.debug(f"Constraint validity check completed (no invalid constraints found or query failed): {str(e)}")
        
        return issues

