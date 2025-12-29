"""Remediation suggestion engine for P6 database issues."""

from typing import Dict, List, Any
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union


class RemediationEngine:
    """Generates remediation suggestions based on analysis results."""
    
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
    
    def generate_remediation_plan(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive remediation plan from all analysis results.
        
        Args:
            analysis_results: Dictionary containing results from all analyzers
        
        Returns:
            Dictionary with prioritized remediation plan
        """
        plan = {
            'critical_actions': [],
            'high_priority_actions': [],
            'medium_priority_actions': [],
            'low_priority_actions': [],
            'maintenance_tasks': [],
            'preventive_measures': [],
            'estimated_impact': 'low'
        }
        
        # Process schema health issues
        schema_results = analysis_results.get('schema_health', {})
        plan['critical_actions'].extend(
            self._process_schema_issues(schema_results)
        )
        
        # Process index fragmentation
        index_results = analysis_results.get('index_fragmentation', {})
        plan['high_priority_actions'].extend(
            self._process_index_issues(index_results)
        )
        
        # Process deadlocks
        deadlock_results = analysis_results.get('deadlocks', {})
        plan['critical_actions'].extend(
            self._process_deadlock_issues(deadlock_results)
        )
        
        # Process table issues
        table_results = analysis_results.get('table_analysis', {})
        plan['medium_priority_actions'].extend(
            self._process_table_issues(table_results)
        )
        
        # Process corruption issues
        corruption_results = analysis_results.get('corruption', {})
        plan['critical_actions'].extend(
            self._process_corruption_issues(corruption_results)
        )
        
        # Generate preventive measures
        plan['preventive_measures'] = self._generate_preventive_measures(analysis_results)
        
        # Generate maintenance tasks
        plan['maintenance_tasks'] = self._generate_maintenance_tasks(analysis_results)
        
        # Determine overall impact
        if plan['critical_actions']:
            plan['estimated_impact'] = 'critical'
        elif plan['high_priority_actions']:
            plan['estimated_impact'] = 'high'
        elif plan['medium_priority_actions']:
            plan['estimated_impact'] = 'medium'
        
        return plan
    
    def _process_schema_issues(self, results: Dict) -> List[Dict]:
        """Process schema health issues into remediation actions."""
        actions = []
        
        invalid_constraints = results.get('invalid_constraints', [])
        for constraint in invalid_constraints:
            if constraint.get('severity') == 'high':
                actions.append({
                    'category': 'schema',
                    'priority': 'critical',
                    'action': f"Rebuild or fix constraint '{constraint.get('constraint')}' on table '{constraint.get('table')}'",
                    'command': self._get_constraint_fix_command(constraint),
                    'impact': 'High - may cause data integrity issues'
                })
        
        missing_indexes = results.get('missing_indexes', [])
        for index in missing_indexes:
            actions.append({
                'category': 'schema',
                'priority': 'high',
                'action': f"Create index on foreign key columns for table '{index.get('table')}'",
                'command': self._get_create_index_command(index),
                'impact': 'Medium - improves query performance'
            })
        
        return actions
    
    def _process_index_issues(self, results: Dict) -> List[Dict]:
        """Process index fragmentation issues."""
        actions = []
        
        high_frag = results.get('high_fragmentation', [])
        for idx in high_frag:
            actions.append({
                'category': 'index',
                'priority': 'high',
                'action': f"Rebuild index '{idx.get('index_name')}' on table '{idx.get('table_name')}' (fragmentation: {idx.get('fragmentation_percent', 0):.2f}%)",
                'command': self._get_rebuild_index_command(idx),
                'impact': 'High - significantly improves query performance',
                'maintenance_window': 'Required'
            })
        
        medium_frag = results.get('medium_fragmentation', [])
        for idx in medium_frag:
            actions.append({
                'category': 'index',
                'priority': 'medium',
                'action': f"Reorganize index '{idx.get('index_name')}' on table '{idx.get('table_name')}' (fragmentation: {idx.get('fragmentation_percent', 0):.2f}%)",
                'command': self._get_reorganize_index_command(idx),
                'impact': 'Medium - improves query performance',
                'maintenance_window': 'Recommended'
            })
        
        return actions
    
    def _process_deadlock_issues(self, results: Dict) -> List[Dict]:
        """Process deadlock issues."""
        actions = []
        
        deadlocks = results.get('recent_deadlocks', [])
        critical_deadlocks = [d for d in deadlocks if d.get('severity') == 'critical']
        
        if critical_deadlocks:
            actions.append({
                'category': 'deadlock',
                'priority': 'critical',
                'action': f"Review and fix {len(critical_deadlocks)} deadlock(s) - check transaction ordering in application code",
                'command': 'Review application code and database transaction logs',
                'impact': 'Critical - deadlocks cause application failures',
                'requires_code_review': True
            })
        
        return actions
    
    def _process_table_issues(self, results: Dict) -> List[Dict]:
        """Process table analysis issues."""
        actions = []
        
        warning_tables = results.get('warning_tables', [])
        for table in warning_tables:
            reasons = table.get('warning_reasons', [])
            if 'Statistics outdated' in reasons:
                actions.append({
                    'category': 'table',
                    'priority': 'medium',
                    'action': f"Update statistics for table '{table.get('table_name')}'",
                    'command': self._get_update_stats_command(table),
                    'impact': 'Medium - improves query plan accuracy'
                })
        
        large_tables = results.get('large_tables', [])
        very_large = [t for t in large_tables if float(t.get('size_mb', 0) or 0) > 10000]
        if very_large:
            actions.append({
                'category': 'table',
                'priority': 'medium',
                'action': f"Consider partitioning for {len(very_large)} very large table(s)",
                'command': 'Review partitioning strategy with DBA',
                'impact': 'Medium - improves maintenance and query performance',
                'requires_dba': True
            })
        
        return actions
    
    def _process_corruption_issues(self, results: Dict) -> List[Dict]:
        """Process corruption issues."""
        actions = []
        
        corruption = results.get('corruption_issues', [])
        for issue in corruption:
            if issue.get('severity') == 'critical':
                actions.append({
                    'category': 'corruption',
                    'priority': 'critical',
                    'action': issue.get('message', 'Corruption detected'),
                    'command': self._get_corruption_fix_command(issue),
                    'impact': 'Critical - data integrity at risk',
                    'immediate_action_required': True
                })
        
        upgrade_issues = results.get('upgrade_inconsistencies', [])
        for issue in upgrade_issues:
            if issue.get('severity') == 'critical':
                actions.append({
                    'category': 'upgrade',
                    'priority': 'critical',
                    'action': issue.get('message', 'Upgrade inconsistency detected'),
                    'command': 'Review P6 upgrade documentation and re-run upgrade if necessary',
                    'impact': 'Critical - may cause application errors',
                    'requires_vendor_support': True
                })
        
        return actions
    
    def _get_constraint_fix_command(self, constraint: Dict) -> str:
        """Generate command to fix constraint."""
        table = constraint.get('table', 'table_name')
        constraint_name = constraint.get('constraint', 'constraint_name')
        
        if self.db_type == 'oracle':
            return f"ALTER TABLE {table} ENABLE CONSTRAINT {constraint_name};"
        else:
            return f"ALTER TABLE {table} WITH CHECK CHECK CONSTRAINT {constraint_name};"
    
    def _get_create_index_command(self, index: Dict) -> str:
        """Generate command to create index."""
        table = index.get('table', 'table_name')
        constraint = index.get('constraint', 'fk_constraint')
        index_name = f"IDX_{table}_{constraint}"
        
        if self.db_type == 'oracle':
            return f"CREATE INDEX {index_name} ON {table} (/* FK columns */);"
        else:
            return f"CREATE INDEX {index_name} ON {table} (/* FK columns */);"
    
    def _get_rebuild_index_command(self, index: Dict) -> str:
        """Generate command to rebuild index."""
        index_name = index.get('index_name', 'index_name')
        table_name = index.get('table_name', 'table_name')
        
        if self.db_type == 'oracle':
            return f"ALTER INDEX {index_name} REBUILD;"
        else:
            return f"ALTER INDEX {index_name} ON {table_name} REBUILD;"
    
    def _get_reorganize_index_command(self, index: Dict) -> str:
        """Generate command to reorganize index."""
        index_name = index.get('index_name', 'index_name')
        table_name = index.get('table_name', 'table_name')
        
        if self.db_type == 'oracle':
            return f"ALTER INDEX {index_name} REBUILD ONLINE;"
        else:
            return f"ALTER INDEX {index_name} ON {table_name} REORGANIZE;"
    
    def _get_update_stats_command(self, table: Dict) -> str:
        """Generate command to update statistics."""
        table_name = table.get('table_name', 'table_name')
        
        if self.db_type == 'oracle':
            return f"EXEC DBMS_STATS.GATHER_TABLE_STATS(ownname => USER, tabname => '{table_name}');"
        else:
            return f"UPDATE STATISTICS {table_name};"
    
    def _get_corruption_fix_command(self, issue: Dict) -> str:
        """Generate command to address corruption."""
        issue_type = issue.get('type', 'unknown')
        
        if self.db_type == 'oracle':
            if issue_type == 'corrupt_block':
                return "RMAN> BLOCKRECOVER DATAFILE <file#> BLOCK <block#>;"
            else:
                return "RMAN> VALIDATE DATABASE;"
        else:
            if issue_type == 'suspect_page':
                return f"DBCC CHECKDB WITH REPAIR_ALLOW_DATA_LOSS; -- Use with caution!"
            else:
                return "DBCC CHECKDB;"
    
    def _generate_preventive_measures(self, results: Dict) -> List[str]:
        """Generate preventive measures."""
        measures = []
        
        measures.append("Implement regular index maintenance schedule (weekly/monthly)")
        measures.append("Set up automated statistics updates")
        measures.append("Monitor deadlock frequency and patterns")
        measures.append("Implement regular database consistency checks")
        measures.append("Maintain regular backups and test restore procedures")
        measures.append("Review and optimize long-running queries")
        measures.append("Monitor table growth and implement archiving strategy")
        
        return measures
    
    def _generate_maintenance_tasks(self, results: Dict) -> List[Dict]:
        """Generate recommended maintenance tasks."""
        tasks = []
        
        tasks.append({
            'task': 'Weekly index maintenance',
            'frequency': 'Weekly',
            'description': 'Rebuild or reorganize fragmented indexes',
            'estimated_time': '2-4 hours'
        })
        
        tasks.append({
            'task': 'Statistics update',
            'frequency': 'Weekly',
            'description': 'Update table and index statistics',
            'estimated_time': '1-2 hours'
        })
        
        tasks.append({
            'task': 'Database consistency check',
            'frequency': 'Monthly',
            'description': 'Run DBCC CHECKDB or RMAN VALIDATE',
            'estimated_time': '4-8 hours'
        })
        
        tasks.append({
            'task': 'Review and archive old data',
            'frequency': 'Quarterly',
            'description': 'Archive historical project data',
            'estimated_time': '8-16 hours'
        })
        
        return tasks

