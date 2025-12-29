"""HTML report generator for P6 database analysis."""

from typing import Dict, Any
from datetime import datetime
from jinja2 import Template
from utils.security import SecurityValidator


class HTMLReportGenerator:
    """Generates HTML reports from analysis results."""
    
    def generate_report(self, results: Dict[str, Any], filename: str):
        """
        Generate HTML report.
        
        Args:
            results: Analysis results dictionary
            filename: Output filename
        """
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <title>P6 Database Analysis Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }
        h3 {
            color: #7f8c8d;
            margin-top: 20px;
        }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
            margin: 5px 0;
        }
        .status.healthy { background-color: #2ecc71; color: white; }
        .status.warning { background-color: #f39c12; color: white; }
        .status.critical { background-color: #e74c3c; color: white; }
        .status.issues_found { background-color: #e67e22; color: white; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .severity-high { color: #e74c3c; font-weight: bold; }
        .severity-medium { color: #f39c12; font-weight: bold; }
        .severity-low { color: #95a5a6; }
        .code {
            background-color: #ecf0f1;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 0.9em;
        }
        ul {
            line-height: 1.8;
        }
        .summary-box {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .metric {
            display: inline-block;
            margin: 10px 20px 10px 0;
        }
        .metric-label {
            font-size: 0.9em;
            color: #7f8c8d;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Primavera P6 Database Analysis Report</h1>
        <p><strong>Generated:</strong> {{ report_date }}</p>
        
        <div class="summary-box">
            <h2>Executive Summary</h2>
            {% if schema_health %}
            <div class="metric">
                <div class="metric-label">Schema Health</div>
                <div class="metric-value status {{ schema_health.status }}">{{ schema_health.status|upper }}</div>
            </div>
            {% endif %}
            {% if index_fragmentation %}
            <div class="metric">
                <div class="metric-label">Index Fragmentation</div>
                <div class="metric-value status {{ index_fragmentation.status }}">{{ index_fragmentation.status|upper }}</div>
            </div>
            {% endif %}
            {% if deadlocks %}
            <div class="metric">
                <div class="metric-label">Deadlocks</div>
                <div class="metric-value">{{ deadlocks.deadlock_count }}</div>
            </div>
            {% endif %}
            {% if table_analysis %}
            <div class="metric">
                <div class="metric-label">Total Tables</div>
                <div class="metric-value">{{ table_analysis.total_tables }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Size</div>
                <div class="metric-value">{{ "%.2f"|format(table_analysis.total_size_mb) }} MB</div>
            </div>
            {% endif %}
        </div>
        
        {% if schema_health %}
        <h2>Schema Health Analysis</h2>
        <p><strong>Status:</strong> <span class="status {{ schema_health.status }}">{{ schema_health.status|upper }}</span></p>
        <p>Tables: {{ schema_health.table_count }}, Indexes: {{ schema_health.index_count }}, Constraints: {{ schema_health.constraint_count }}</p>
        
        {% if schema_health.issues %}
        <h3>Issues Found</h3>
        <table>
            <tr>
                <th>Type</th>
                <th>Table</th>
                <th>Severity</th>
                <th>Message</th>
            </tr>
            {% for issue in schema_health.issues %}
            <tr>
                <td>{{ issue.type }}</td>
                <td>{{ issue.table or 'N/A' }}</td>
                <td class="severity-{{ issue.severity }}">{{ issue.severity }}</td>
                <td>{{ issue.message }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        {% endif %}
        
        {% if index_fragmentation %}
        <h2>Index Fragmentation Analysis</h2>
        <p><strong>Status:</strong> <span class="status {{ index_fragmentation.status }}">{{ index_fragmentation.status|upper }}</span></p>
        <p>Fragmented Indexes: {{ index_fragmentation.fragmented_indexes|length }}</p>
        
        {% if index_fragmentation.fragmented_indexes %}
        <h3>Fragmented Indexes</h3>
        <table>
            <tr>
                <th>Table</th>
                <th>Index</th>
                <th>Fragmentation %</th>
                <th>Rows</th>
            </tr>
            {% for idx in index_fragmentation.fragmented_indexes %}
            <tr>
                <td>{{ idx.table_name }}</td>
                <td>{{ idx.index_name }}</td>
                <td>{{ "%.2f"|format(idx.fragmentation_percent) }}%</td>
                <td>{{ idx.num_rows or idx.page_count or 'N/A' }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        {% if index_fragmentation.recommendations %}
        <h3>Recommendations</h3>
        <ul>
            {% for rec in index_fragmentation.recommendations %}
            <li>{{ rec }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        {% endif %}
        
        {% if deadlocks %}
        <h2>Deadlock Analysis</h2>
        <p><strong>Status:</strong> <span class="status {{ deadlocks.status }}">{{ deadlocks.status|upper }}</span></p>
        <p>Deadlock Count: {{ deadlocks.deadlock_count }}</p>
        
        {% if deadlocks.recent_deadlocks %}
        <h3>Recent Deadlocks</h3>
        <table>
            <tr>
                <th>Type</th>
                <th>Session 1</th>
                <th>Session 2</th>
                <th>Time</th>
                <th>Severity</th>
            </tr>
            {% for dl in deadlocks.recent_deadlocks %}
            <tr>
                <td>{{ dl.type }}</td>
                <td>{{ dl.session_1 or dl.blocking_session or 'N/A' }}</td>
                <td>{{ dl.session_2 or dl.waiting_session or 'N/A' }}</td>
                <td>{{ dl.detection_time or dl.deadlock_time }}</td>
                <td class="severity-{{ dl.severity }}">{{ dl.severity }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        {% if deadlocks.recommendations %}
        <h3>Recommendations</h3>
        <ul>
            {% for rec in deadlocks.recommendations %}
            <li>{{ rec }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        {% endif %}
        
        {% if table_analysis %}
        <h2>Table Analysis</h2>
        <p><strong>Status:</strong> <span class="status {{ table_analysis.status }}">{{ table_analysis.status|upper }}</span></p>
        <p>Total Tables: {{ table_analysis.total_tables }}, Total Size: {{ "%.2f"|format(table_analysis.total_size_mb) }} MB</p>
        
        {% if table_analysis.large_tables %}
        <h3>Large Tables (>1000 MB)</h3>
        <table>
            <tr>
                <th>Table Name</th>
                <th>Rows</th>
                <th>Size (MB)</th>
            </tr>
            {% for table in table_analysis.large_tables[:20] %}
            <tr>
                <td>{{ table.table_name }}</td>
                <td>{{ table.num_rows }}</td>
                <td>{{ "%.2f"|format(table.size_mb) }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        {% if table_analysis.warning_tables %}
        <h3>Tables with Warnings</h3>
        <table>
            <tr>
                <th>Table Name</th>
                <th>Issues</th>
            </tr>
            {% for table in table_analysis.warning_tables %}
            <tr>
                <td>{{ table.table_name }}</td>
                <td>{{ table.warning_reasons|join(', ') }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        {% endif %}
        
        {% if corruption %}
        <h2>Corruption & Upgrade Inconsistencies</h2>
        <p><strong>Status:</strong> <span class="status {{ corruption.status }}">{{ corruption.status|upper }}</span></p>
        
        {% if corruption.corruption_issues %}
        <h3>Corruption Issues</h3>
        <table>
            <tr>
                <th>Type</th>
                <th>Severity</th>
                <th>Object</th>
                <th>Message</th>
            </tr>
            {% for issue in corruption.corruption_issues %}
            <tr>
                <td>{{ issue.type }}</td>
                <td class="severity-{{ issue.severity }}">{{ issue.severity }}</td>
                <td>{{ issue.object_name or issue.table or issue.database or 'N/A' }}</td>
                <td>{{ issue.message }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        {% if corruption.upgrade_inconsistencies %}
        <h3>Upgrade Inconsistencies</h3>
        <table>
            <tr>
                <th>Type</th>
                <th>Severity</th>
                <th>Message</th>
            </tr>
            {% for issue in corruption.upgrade_inconsistencies %}
            <tr>
                <td>{{ issue.type }}</td>
                <td class="severity-{{ issue.severity }}">{{ issue.severity }}</td>
                <td>{{ issue.message }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        {% endif %}
        
        {% if remediation %}
        <h2>Remediation Plan</h2>
        <p><strong>Estimated Impact:</strong> <span class="status {{ remediation.estimated_impact }}">{{ remediation.estimated_impact|upper }}</span></p>
        
        {% if remediation.critical_actions %}
        <h3>Critical Actions</h3>
        <ul>
            {% for action in remediation.critical_actions %}
            <li>
                <strong>{{ action.action }}</strong><br/>
                <span class="code">{{ action.command }}</span><br/>
                <em>Impact: {{ action.impact }}</em>
            </li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if remediation.high_priority_actions %}
        <h3>High Priority Actions</h3>
        <ul>
            {% for action in remediation.high_priority_actions %}
            <li>
                <strong>{{ action.action }}</strong><br/>
                <span class="code">{{ action.command }}</span>
            </li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if remediation.medium_priority_actions %}
        <h3>Medium Priority Actions</h3>
        <ul>
            {% for action in remediation.medium_priority_actions %}
            <li>{{ action.action }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if remediation.preventive_measures %}
        <h3>Preventive Measures</h3>
        <ul>
            {% for measure in remediation.preventive_measures %}
            <li>{{ measure }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        {% endif %}
        
        <hr/>
        <p style="text-align: center; color: #7f8c8d; font-size: 0.9em;">
            Report generated by P6 Database Analyzer on {{ report_date }}
        </p>
    </div>
</body>
</html>
        """
        
        # Jinja2 auto-escapes by default when autoescape=True
        template = Template(template_str, autoescape=True)
        
        # Sanitize user-provided data before rendering (defense in depth)
        def sanitize_data(data):
            """Recursively sanitize data for HTML output."""
            if isinstance(data, dict):
                return {k: sanitize_data(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [sanitize_data(item) for item in data]
            elif isinstance(data, str):
                return SecurityValidator.sanitize_for_html(data)
            else:
                return data
        
        # Prepare sanitized results
        sanitized_results = sanitize_data(results)
        
        html_content = template.render(
            report_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            schema_health=sanitized_results.get('schema_health', {}),
            index_fragmentation=sanitized_results.get('index_fragmentation', {}),
            deadlocks=sanitized_results.get('deadlocks', {}),
            table_analysis=sanitized_results.get('table_analysis', {}),
            corruption=sanitized_results.get('corruption', {}),
            remediation=sanitized_results.get('remediation', {})
        )
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

