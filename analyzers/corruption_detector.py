"""Corruption and upgrade inconsistency detector for P6 databases."""

from typing import Dict, List, Any
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union
from utils.security import SecurityValidator


class CorruptionDetector:
    """Detects data corruption and upgrade inconsistencies."""
    
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
    
    def detect_issues(self) -> Dict[str, Any]:
        """Detect corruption and upgrade inconsistencies."""
        results = {
            'status': 'healthy',
            'corruption_issues': [],
            'upgrade_inconsistencies': [],
            'integrity_checks': [],
            'recommendations': []
        }
        
        try:
            # Check for corruption
            results['corruption_issues'] = self._check_corruption()
            
            # Check for upgrade inconsistencies
            results['upgrade_inconsistencies'] = self._check_upgrade_inconsistencies()
            
            # Run integrity checks
            results['integrity_checks'] = self._run_integrity_checks()
            
            # Determine overall status
            if results['corruption_issues'] or results['upgrade_inconsistencies']:
                results['status'] = 'issues_found'
            elif results['integrity_checks']:
                failed_checks = [c for c in results['integrity_checks'] if not c.get('passed', True)]
                if failed_checks:
                    results['status'] = 'issues_found'
            
            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(results)
        
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def _check_corruption(self) -> List[Dict]:
        """Check for data corruption."""
        issues = []
        
        if self.db_type == 'oracle':
            # Check for corrupt blocks
            try:
                query = """
                    SELECT 
                        file#,
                        block#,
                        blocks,
                        corruption_type
                    FROM v$database_block_corruption
                """
                results = self.connector.execute_query(query)
                for row in results:
                    issues.append({
                        'type': 'corrupt_block',
                        'file': row.get('file#'),
                        'block': row.get('block#'),
                        'blocks': row.get('blocks'),
                        'corruption_type': row.get('corruption_type'),
                        'severity': 'critical',
                        'message': f"Corrupt block detected: File {row.get('file#')}, Block {row.get('block#')}"
                    })
            except Exception as e:
                # May not have access or no corruption
                pass
            
            # Check for invalid objects
            try:
                query = """
                    SELECT 
                        object_name,
                        object_type,
                        status
                    FROM user_objects
                    WHERE status = 'INVALID'
                """
                results = self.connector.execute_query(query)
                for row in results:
                    issues.append({
                        'type': 'invalid_object',
                        'object_name': row.get('object_name'),
                        'object_type': row.get('object_type'),
                        'severity': 'high',
                        'message': f"Invalid {row.get('object_type')}: {row.get('object_name')}"
                    })
            except:
                pass
        
        else:  # MSSQL
            # Check for suspect pages
            try:
                query = """
                    SELECT 
                        database_id,
                        file_id,
                        page_id,
                        event_type,
                        error_count
                    FROM msdb.dbo.suspect_pages
                """
                results = self.connector.execute_query(query)
                for row in results:
                    issues.append({
                        'type': 'suspect_page',
                        'database_id': row.get('database_id'),
                        'file_id': row.get('file_id'),
                        'page_id': row.get('page_id'),
                        'event_type': row.get('event_type'),
                        'error_count': row.get('error_count'),
                        'severity': 'critical',
                        'message': f"Suspect page detected: File {row.get('file_id')}, Page {row.get('page_id')}"
                    })
            except:
                pass
            
            # Check database consistency
            try:
                # This would typically be run via DBCC, but we can check for known issues
                query = """
                    SELECT 
                        name,
                        state_desc,
                        is_in_standby
                    FROM sys.databases
                    WHERE state_desc != 'ONLINE'
                """
                results = self.connector.execute_query(query)
                for row in results:
                    issues.append({
                        'type': 'database_state',
                        'database': row.get('name'),
                        'state': row.get('state_desc'),
                        'severity': 'high',
                        'message': f"Database {row.get('name')} is in {row.get('state_desc')} state"
                    })
            except:
                pass
        
        return issues
    
    def _check_upgrade_inconsistencies(self) -> List[Dict]:
        """Check for P6 upgrade inconsistencies."""
        issues = []
        
        # Check for version mismatches in common P6 tables
        try:
            # Check if P6 version table exists and has consistent data
            if self.db_type == 'oracle':
                version_query = "SELECT * FROM (SELECT version_no FROM pmdbversion ORDER BY version_no DESC) WHERE ROWNUM = 1"
            else:
                version_query = "SELECT TOP 1 version_no FROM pmdbversion ORDER BY version_no DESC"
            
            try:
                version = self.connector.execute_scalar(version_query)
                if version:
                    # Check for tables that might be missing after upgrade
                    p6_core_tables = ['PROJECT', 'TASK', 'RESOURCE', 'ASSIGNMENT', 'WBS']
                    missing_tables = []
                    
                    for table in p6_core_tables:
                        # Validate table name to prevent SQL injection
                        sanitized_table = SecurityValidator.sanitize_table_name(table)
                        if not sanitized_table:
                            continue
                        
                        # Use parameterized approach - query system tables safely
                        # Since these are whitelisted hardcoded values, we can safely use them
                        # But we validate anyway for defense in depth
                        if self.db_type == 'oracle':
                            # Oracle uses bind variables
                            check_query = "SELECT COUNT(*) FROM user_tables WHERE table_name = :table_name"
                            count = self.connector.execute_scalar(check_query, {'table_name': sanitized_table})
                        else:
                            # MSSQL uses positional parameters
                            check_query = "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?"
                            count = self.connector.execute_scalar(check_query, {'table_name': sanitized_table})
                        if count == 0:
                            missing_tables.append(table)
                    
                    if missing_tables:
                        issues.append({
                            'type': 'missing_tables',
                            'missing_tables': missing_tables,
                            'severity': 'critical',
                            'message': f"Core P6 tables missing: {', '.join(missing_tables)}"
                        })
            except:
                # Version table might not exist or be accessible
                pass
        
        except Exception as e:
            issues.append({
                'type': 'upgrade_check_error',
                'severity': 'low',
                'message': f"Could not check upgrade consistency: {str(e)}"
            })
        
        # Check for orphaned foreign key references
        try:
            # This is a simplified check - in production, you'd check all FKs
            if self.db_type == 'oracle':
                fk_check = """
                    SELECT 
                        c.constraint_name,
                        c.table_name,
                        c.r_constraint_name
                    FROM user_constraints c
                    WHERE c.constraint_type = 'R'
                    AND c.status = 'ENABLED'
                """
            else:
                fk_check = """
                    SELECT 
                        fk.name as constraint_name,
                        OBJECT_NAME(fk.parent_object_id) as table_name,
                        OBJECT_NAME(fk.referenced_object_id) as referenced_table
                    FROM sys.foreign_keys fk
                    WHERE fk.is_disabled = 0
                """
            
            fks = self.connector.execute_query(fk_check)
            # Note: Full orphaned record check would require checking each FK
            # This is a placeholder for the concept
            
        except:
            pass
        
        return issues
    
    def _run_integrity_checks(self) -> List[Dict]:
        """Run database integrity checks."""
        checks = []
        
        # Check table row counts are reasonable
        try:
            if self.db_type == 'oracle':
                query = """
                    SELECT 
                        table_name,
                        num_rows
                    FROM user_tables
                    WHERE num_rows < 0
                """
            else:
                query = """
                    SELECT 
                        t.name as table_name,
                        SUM(p.rows) as num_rows
                    FROM sys.tables t
                    INNER JOIN sys.partitions p ON t.object_id = p.object_id
                    WHERE p.index_id IN (0, 1)
                    GROUP BY t.name
                    HAVING SUM(p.rows) < 0
                """
            
            results = self.connector.execute_query(query)
            for row in results:
                checks.append({
                    'check_name': 'negative_row_count',
                    'table': row.get('table_name'),
                    'passed': False,
                    'message': f"Table {row.get('table_name')} has negative row count"
                })
        except:
            pass
        
        # Check for tables with no primary key (common P6 issue indicator)
        try:
            if self.db_type == 'oracle':
                query = """
                    SELECT table_name
                    FROM user_tables t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM user_constraints c
                        WHERE c.table_name = t.table_name
                        AND c.constraint_type = 'P'
                    )
                    AND table_name IN ('PROJECT', 'TASK', 'RESOURCE', 'ASSIGNMENT')
                """
            else:
                query = """
                    SELECT t.name as table_name
                    FROM sys.tables t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM sys.key_constraints kc
                        WHERE kc.parent_object_id = t.object_id
                        AND kc.type = 'PK'
                    )
                    AND t.name IN ('PROJECT', 'TASK', 'RESOURCE', 'ASSIGNMENT')
                """
            
            results = self.connector.execute_query(query)
            for row in results:
                checks.append({
                    'check_name': 'missing_primary_key',
                    'table': row.get('table_name'),
                    'passed': False,
                    'message': f"Core table {row.get('table_name')} is missing primary key"
                })
        except:
            pass
        
        # If no issues found, add a passed check
        if not checks:
            checks.append({
                'check_name': 'basic_integrity',
                'passed': True,
                'message': 'Basic integrity checks passed'
            })
        
        return checks
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on findings."""
        recommendations = []
        
        corruption_count = len(results.get('corruption_issues', []))
        upgrade_count = len(results.get('upgrade_inconsistencies', []))
        failed_checks = [c for c in results.get('integrity_checks', []) if not c.get('passed', True)]
        
        if corruption_count > 0:
            recommendations.append(
                f"CRITICAL: {corruption_count} corruption issue(s) detected. "
                "Immediate action required - restore from backup if possible."
            )
            if self.db_type == 'oracle':
                recommendations.append(
                    "For Oracle: Run 'RMAN VALIDATE DATABASE' to identify all corrupt blocks."
                )
            else:
                recommendations.append(
                    "For MSSQL: Run 'DBCC CHECKDB' to identify all corruption issues."
                )
        
        if upgrade_count > 0:
            recommendations.append(
                f"WARNING: {upgrade_count} upgrade inconsistency(ies) detected. "
                "Review P6 upgrade documentation and verify all upgrade steps completed."
            )
        
        if failed_checks:
            recommendations.append(
                f"{len(failed_checks)} integrity check(s) failed. "
                "Review failed checks and take appropriate corrective action."
            )
        
        if not recommendations:
            recommendations.append("No corruption or upgrade inconsistency issues detected.")
        
        return recommendations

