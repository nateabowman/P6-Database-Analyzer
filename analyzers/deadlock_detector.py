"""Deadlock detection module for P6 databases."""

from typing import Dict, List, Any
from datetime import datetime
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union


class DeadlockDetector:
    """Detects and monitors deadlocks in P6 databases."""
    
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
    
    def detect_deadlocks(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Detect recent deadlocks.
        
        Args:
            hours_back: Number of hours to look back for deadlocks
        
        Returns:
            Dictionary with deadlock detection results
        """
        results = {
            'status': 'no_deadlocks',
            'deadlock_count': 0,
            'recent_deadlocks': [],
            'deadlock_details': [],
            'recommendations': []
        }
        
        try:
            deadlocks = self._get_recent_deadlocks(hours_back)
            results['deadlock_count'] = len(deadlocks)
            results['recent_deadlocks'] = deadlocks
            results['deadlock_details'] = deadlocks
            
            if deadlocks:
                results['status'] = 'deadlocks_found'
                results['recommendations'] = self._generate_recommendations(deadlocks)
            else:
                results['recommendations'].append("No deadlocks detected in the specified time period.")
        
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            results['recommendations'].append(
                f"Error detecting deadlocks: {str(e)}. "
                "Ensure you have appropriate permissions to access deadlock logs."
            )
        
        return results
    
    def _get_recent_deadlocks(self, hours_back: int) -> List[Dict]:
        """Get recent deadlock information."""
        if self.db_type == 'oracle':
            return self._get_oracle_deadlocks(hours_back)
        else:
            return self._get_mssql_deadlocks(hours_back)
    
    def _get_oracle_deadlocks(self, hours_back: int) -> List[Dict]:
        """Get Oracle deadlock information from alert log or v$ views."""
        deadlocks = []
        
        try:
            # Check for deadlocks in v$lock and v$session
            query = """
                SELECT 
                    s1.sid as session_id_1,
                    s2.sid as session_id_2,
                    s1.username as user_1,
                    s2.username as user_2,
                    s1.program as program_1,
                    s2.program as program_2,
                    SYSDATE as detection_time
                FROM v$lock l1
                JOIN v$lock l2 ON l1.id1 = l2.id1 AND l1.id2 = l2.id2
                JOIN v$session s1 ON l1.sid = s1.sid
                JOIN v$session s2 ON l2.sid = s2.sid
                WHERE l1.block > 0 AND l2.block > 0
                AND l1.sid < l2.sid
            """
            
            results = self.connector.execute_query(query)
            for row in results:
                deadlocks.append({
                    'type': 'potential_deadlock',
                    'session_1': row.get('session_id_1'),
                    'session_2': row.get('session_id_2'),
                    'user_1': row.get('user_1'),
                    'user_2': row.get('user_2'),
                    'program_1': row.get('program_1'),
                    'program_2': row.get('program_2'),
                    'detection_time': str(row.get('detection_time', datetime.now())),
                    'severity': 'high'
                })
        except Exception as e:
            # May not have access to v$ views
            try:
                # Alternative: Check for blocking sessions
                query = """
                    SELECT 
                        blocking_session,
                        waiting_session,
                        object_name,
                        object_type
                    FROM v$session_blockers
                """
                results = self.connector.execute_query(query)
                for row in results:
                    if row.get('blocking_session') and row.get('waiting_session'):
                        deadlocks.append({
                            'type': 'blocking_session',
                            'blocking_session': row.get('blocking_session'),
                            'waiting_session': row.get('waiting_session'),
                            'object': row.get('object_name'),
                            'detection_time': str(datetime.now()),
                            'severity': 'medium'
                        })
            except:
                pass
        
        return deadlocks
    
    def _get_mssql_deadlocks(self, hours_back: int) -> List[Dict]:
        """Get MSSQL deadlock information from system_health or error log."""
        deadlocks = []
        
        try:
            # Try to get deadlocks from system_health extended events
            query = """
                SELECT 
                    CAST(event_data AS XML).value('(event/@timestamp)[1]', 'datetime2') AS deadlock_time,
                    CAST(event_data AS XML).value('(event/data[@name="database_name"]/value)[1]', 'nvarchar(128)') AS database_name,
                    CAST(event_data AS XML).query('(event/data[@name="xml_report"]/value/deadlock)[1]') AS deadlock_graph
                FROM (
                    SELECT CAST(target_data AS XML) AS target_data
                    FROM sys.dm_xe_session_targets st
                    INNER JOIN sys.dm_xe_sessions s ON s.address = st.event_session_address
                    WHERE s.name = 'system_health'
                    AND st.target_name = 'event_file'
                ) AS data
                CROSS APPLY target_data.nodes('//event_file_target/event') AS n(event_data)
                WHERE CAST(event_data AS XML).value('(event/@name)[1]', 'nvarchar(128)') = 'xml_deadlock_report'
                AND CAST(event_data AS XML).value('(event/@timestamp)[1]', 'datetime2') > DATEADD(hour, -?, GETDATE())
            """
            
            # Note: This query may need adjustment based on SQL Server version
            # Using tuple for pyodbc parameter
            try:
                results = self.connector.execute_query(query, {'hours': hours_back})
            except:
                # If query fails, try without parameters
                results = []
            for row in results:
                deadlocks.append({
                    'type': 'deadlock',
                    'deadlock_time': str(row.get('deadlock_time', datetime.now())),
                    'database': row.get('database_name'),
                    'deadlock_graph': str(row.get('deadlock_graph', '')),
                    'severity': 'critical'
                })
        except Exception as e:
            # Fallback: Check for blocking processes
            try:
                query = """
                    SELECT 
                        blocking_session_id,
                        wait_duration_ms,
                        session_id,
                        DB_NAME(database_id) as database_name
                    FROM sys.dm_exec_requests
                    WHERE blocking_session_id > 0
                """
                results = self.connector.execute_query(query)
                for row in results:
                    if row.get('blocking_session_id'):
                        deadlocks.append({
                            'type': 'blocking_process',
                            'blocking_session': row.get('blocking_session_id'),
                            'waiting_session': row.get('session_id'),
                            'wait_duration_ms': row.get('wait_duration_ms'),
                            'database': row.get('database_name'),
                            'detection_time': str(datetime.now()),
                            'severity': 'medium'
                        })
            except:
                pass
        
        return deadlocks
    
    def _generate_recommendations(self, deadlocks: List[Dict]) -> List[str]:
        """Generate recommendations based on deadlock findings."""
        recommendations = []
        
        critical_count = sum(1 for d in deadlocks if d.get('severity') == 'critical')
        medium_count = sum(1 for d in deadlocks if d.get('severity') == 'medium')
        
        if critical_count > 0:
            recommendations.append(
                f"CRITICAL: {critical_count} deadlock(s) detected. "
                "Review application code for transaction ordering issues."
            )
            recommendations.append(
                "Consider implementing retry logic for transactions that encounter deadlocks."
            )
        
        if medium_count > 0:
            recommendations.append(
                f"WARNING: {medium_count} blocking process(es) detected. "
                "Monitor these sessions and consider optimizing long-running transactions."
            )
        
        recommendations.append(
            "Review transaction isolation levels - consider using READ COMMITTED SNAPSHOT if available."
        )
        recommendations.append(
            "Ensure indexes exist on foreign key columns to reduce lock contention."
        )
        
        return recommendations

