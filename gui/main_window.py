"""Main GUI window for P6 Database Analyzer."""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit, QComboBox,
                               QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
                               QGroupBox, QFormLayout, QMessageBox, QProgressBar,
                               QFileDialog, QSplitter)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
import os
from pathlib import Path
from database.db_factory import DatabaseFactory
from analyzers.schema_health import SchemaHealthScanner
from analyzers.index_fragmentation import IndexFragmentationChecker
from analyzers.deadlock_detector import DeadlockDetector
from analyzers.table_analyzer import TableAnalyzer
from analyzers.corruption_detector import CorruptionDetector
from analyzers.remediation_engine import RemediationEngine
from reports.html_report import HTMLReportGenerator
from reports.pdf_report import PDFReportGenerator
from datetime import datetime
from utils.security import SecurityValidator
from utils.logging_config import get_logger

logger = get_logger(__name__)


class AnalysisThread(QThread):
    """Thread for running database analysis."""
    
    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, connector, analysis_type):
        super().__init__()
        self.connector = connector
        self.analysis_type = analysis_type
    
    def run(self):
        """Run the analysis."""
        try:
            results = {}
            
            if 'schema' in self.analysis_type:
                self.progress.emit("Scanning schema health...")
                scanner = SchemaHealthScanner(self.connector)
                results['schema_health'] = scanner.scan_schema_health()
            
            if 'index' in self.analysis_type:
                self.progress.emit("Checking index fragmentation...")
                checker = IndexFragmentationChecker(self.connector)
                results['index_fragmentation'] = checker.check_fragmentation()
            
            if 'deadlock' in self.analysis_type:
                self.progress.emit("Detecting deadlocks...")
                detector = DeadlockDetector(self.connector)
                results['deadlocks'] = detector.detect_deadlocks()
            
            if 'table' in self.analysis_type:
                self.progress.emit("Analyzing tables...")
                analyzer = TableAnalyzer(self.connector)
                results['table_analysis'] = analyzer.analyze_tables()
            
            if 'corruption' in self.analysis_type:
                self.progress.emit("Detecting corruption...")
                detector = CorruptionDetector(self.connector)
                results['corruption'] = detector.detect_issues()
            
            if 'remediation' in self.analysis_type:
                self.progress.emit("Generating remediation plan...")
                engine = RemediationEngine(self.connector)
                results['remediation'] = engine.generate_remediation_plan(results)
            
            self.finished.emit(results)
        
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.connector = None
        self.analysis_results = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Primavera P6 Database Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Connection panel
        connection_group = QGroupBox("Database Connection")
        connection_layout = QFormLayout()
        
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["Oracle", "MSSQL"])
        connection_layout.addRow("Database Type:", self.db_type_combo)
        
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("hostname or server")
        connection_layout.addRow("Host/Server:", self.host_input)
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("1521 (Oracle) or 1433 (MSSQL)")
        connection_layout.addRow("Port:", self.port_input)
        
        self.service_input = QLineEdit()
        self.service_input.setPlaceholderText("Service name (Oracle) or Database name (MSSQL)")
        connection_layout.addRow("Service/Database:", self.service_input)
        
        self.username_input = QLineEdit()
        connection_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        connection_layout.addRow("Password:", self.password_input)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_database)
        connection_layout.addRow("", self.connect_btn)
        
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)
        
        # Analysis panel
        analysis_group = QGroupBox("Analysis Options")
        analysis_layout = QHBoxLayout()
        
        self.schema_check = QPushButton("Schema Health")
        self.schema_check.setCheckable(True)
        self.schema_check.setChecked(True)
        analysis_layout.addWidget(self.schema_check)
        
        self.index_check = QPushButton("Index Fragmentation")
        self.index_check.setCheckable(True)
        self.index_check.setChecked(True)
        analysis_layout.addWidget(self.index_check)
        
        self.deadlock_check = QPushButton("Deadlocks")
        self.deadlock_check.setCheckable(True)
        self.deadlock_check.setChecked(True)
        analysis_layout.addWidget(self.deadlock_check)
        
        self.table_check = QPushButton("Table Analysis")
        self.table_check.setCheckable(True)
        self.table_check.setChecked(True)
        analysis_layout.addWidget(self.table_check)
        
        self.corruption_check = QPushButton("Corruption")
        self.corruption_check.setCheckable(True)
        self.corruption_check.setChecked(True)
        analysis_layout.addWidget(self.corruption_check)
        
        self.run_analysis_btn = QPushButton("Run Analysis")
        self.run_analysis_btn.clicked.connect(self.run_analysis)
        self.run_analysis_btn.setEnabled(False)
        analysis_layout.addWidget(self.run_analysis_btn)
        
        analysis_group.setLayout(analysis_layout)
        main_layout.addWidget(analysis_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # Results tabs
        self.results_tabs = QTabWidget()
        main_layout.addWidget(self.results_tabs)
        
        # Create result tabs
        self.create_result_tabs()
        
        # Export buttons
        export_layout = QHBoxLayout()
        self.export_html_btn = QPushButton("Export HTML Report")
        self.export_html_btn.clicked.connect(self.export_html)
        self.export_html_btn.setEnabled(False)
        export_layout.addWidget(self.export_html_btn)
        
        self.export_pdf_btn = QPushButton("Export PDF Report")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_pdf_btn.setEnabled(False)
        export_layout.addWidget(self.export_pdf_btn)
        
        main_layout.addLayout(export_layout)
    
    def create_result_tabs(self):
        """Create tabs for displaying results."""
        # Summary tab
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.results_tabs.addTab(self.summary_text, "Summary")
        
        # Schema Health tab
        self.schema_table = QTableWidget()
        self.results_tabs.addTab(self.schema_table, "Schema Health")
        
        # Index Fragmentation tab
        self.index_table = QTableWidget()
        self.results_tabs.addTab(self.index_table, "Index Fragmentation")
        
        # Deadlocks tab
        self.deadlock_table = QTableWidget()
        self.results_tabs.addTab(self.deadlock_table, "Deadlocks")
        
        # Tables tab
        self.tables_table = QTableWidget()
        self.results_tabs.addTab(self.tables_table, "Tables")
        
        # Corruption tab
        self.corruption_table = QTableWidget()
        self.results_tabs.addTab(self.corruption_table, "Corruption")
        
        # Remediation tab
        self.remediation_text = QTextEdit()
        self.remediation_text.setReadOnly(True)
        self.results_tabs.addTab(self.remediation_text, "Remediation")
        
        # Log viewer tab
        log_widget = QWidget()
        log_layout = QVBoxLayout()
        log_widget.setLayout(log_layout)
        
        log_controls = QHBoxLayout()
        self.refresh_logs_btn = QPushButton("Refresh Logs")
        self.refresh_logs_btn.clicked.connect(self.refresh_logs)
        self.clear_logs_btn = QPushButton("Clear Display")
        self.clear_logs_btn.clicked.connect(self.clear_log_display)
        log_controls.addWidget(self.refresh_logs_btn)
        log_controls.addWidget(self.clear_logs_btn)
        log_controls.addStretch()
        log_layout.addLayout(log_controls)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFontFamily("Courier")
        log_layout.addWidget(self.log_text)
        
        self.results_tabs.addTab(log_widget, "Logs")
        
        # Set up log refresh timer
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.refresh_logs)
        self.log_timer.start(5000)  # Refresh every 5 seconds
        
        # Initial log load
        self.refresh_logs()
    
    def connect_database(self):
        """Connect to the database."""
        try:
            db_type = self.db_type_combo.currentText().lower()
            host = self.host_input.text().strip()
            port_str = self.port_input.text().strip()
            service = self.service_input.text().strip()
            username = self.username_input.text().strip()
            password = self.password_input.text()
            
            # Validate inputs
            if not all([host, service, username, password]):
                QMessageBox.warning(self, "Missing Information", 
                                  "Please fill in all connection fields.")
                return
            
            # Validate hostname
            if not SecurityValidator.validate_hostname(host):
                QMessageBox.warning(self, "Invalid Input", 
                                  "Invalid hostname or server name.")
                return
            
            # Validate port
            if port_str and not SecurityValidator.validate_port(port_str):
                QMessageBox.warning(self, "Invalid Input", 
                                  "Port must be a number between 1 and 65535.")
                return
            
            port = int(port_str or ("1521" if db_type == 'oracle' else "1433"))
            
            if db_type == 'oracle':
                self.connector = DatabaseFactory.create_connector(
                    'oracle',
                    host=host,
                    port=port,
                    service_name=service,
                    username=username,
                    password=password
                )
            else:
                self.connector = DatabaseFactory.create_connector(
                    'mssql',
                    server=host,
                    database=service,
                    username=username,
                    password=password
                )
            
            self.connector.connect()
            self.status_label.setText("Connected successfully")
            self.run_analysis_btn.setEnabled(True)
            QMessageBox.information(self, "Success", "Connected to database successfully!")
        
        except Exception as e:
            # Don't expose detailed error information that might leak sensitive data
            error_msg = str(e)
            # Sanitize error message to avoid exposing connection details
            if 'password' in error_msg.lower() or 'credential' in error_msg.lower():
                error_msg = "Authentication failed. Please check your credentials."
            elif 'network' in error_msg.lower() or 'timeout' in error_msg.lower():
                error_msg = "Connection timeout. Please check network connectivity and server address."
            else:
                error_msg = "Connection failed. Please verify your connection settings."
            
            QMessageBox.critical(self, "Connection Error", error_msg)
            self.status_label.setText("Connection failed")
    
    def run_analysis(self):
        """Run the selected analyses."""
        if not self.connector:
            QMessageBox.warning(self, "Not Connected", "Please connect to a database first.")
            return
        
        # Determine which analyses to run
        analysis_types = []
        if self.schema_check.isChecked():
            analysis_types.append('schema')
        if self.index_check.isChecked():
            analysis_types.append('index')
        if self.deadlock_check.isChecked():
            analysis_types.append('deadlock')
        if self.table_check.isChecked():
            analysis_types.append('table')
        if self.corruption_check.isChecked():
            analysis_types.append('corruption')
        
        if not analysis_types:
            QMessageBox.warning(self, "No Selection", "Please select at least one analysis type.")
            return
        
        # Always include remediation
        analysis_types.append('remediation')
        
        # Disable button and show progress
        self.run_analysis_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setText("Running analysis...")
        
        # Run analysis in thread
        self.analysis_thread = AnalysisThread(self.connector, analysis_types)
        self.analysis_thread.progress.connect(self.status_label.setText)
        self.analysis_thread.finished.connect(self.on_analysis_complete)
        self.analysis_thread.error.connect(self.on_analysis_error)
        self.analysis_thread.start()
    
    def on_analysis_complete(self, results):
        """Handle analysis completion."""
        self.analysis_results = results
        self.progress_bar.setVisible(False)
        self.run_analysis_btn.setEnabled(True)
        self.status_label.setText("Analysis complete")
        self.export_html_btn.setEnabled(True)
        self.export_pdf_btn.setEnabled(True)
        
        # Display results
        self.display_results(results)
    
    def on_analysis_error(self, error_msg):
        """Handle analysis error."""
        self.progress_bar.setVisible(False)
        self.run_analysis_btn.setEnabled(True)
        self.status_label.setText(f"Analysis error: {error_msg}")
        QMessageBox.critical(self, "Analysis Error", f"Error during analysis: {error_msg}")
    
    def display_results(self, results):
        """Display analysis results in the UI."""
        # Summary
        summary = self.generate_summary(results)
        self.summary_text.setHtml(summary)
        
        # Schema Health
        if 'schema_health' in results:
            self.populate_schema_table(results['schema_health'])
        
        # Index Fragmentation
        if 'index_fragmentation' in results:
            self.populate_index_table(results['index_fragmentation'])
        
        # Deadlocks
        if 'deadlocks' in results:
            self.populate_deadlock_table(results['deadlocks'])
        
        # Tables
        if 'table_analysis' in results:
            self.populate_tables_table(results['table_analysis'])
        
        # Corruption
        if 'corruption' in results:
            self.populate_corruption_table(results['corruption'])
        
        # Remediation
        if 'remediation' in results:
            self.populate_remediation_text(results['remediation'])
    
    def generate_summary(self, results):
        """Generate HTML summary."""
        # Sanitize HTML output to prevent XSS
        html = "<h2>Analysis Summary</h2>"
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html += f"<p><b>Analysis Date:</b> {SecurityValidator.sanitize_for_html(date_str)}</p>"
        
        # Schema Health
        if 'schema_health' in results:
            sh = results['schema_health']
            status = SecurityValidator.sanitize_for_html(sh.get('status', 'unknown').upper())
            html += f"<h3>Schema Health: {status}</h3>"
            html += f"<p>Tables: {sh.get('table_count', 0)}, "
            html += f"Issues: {len(sh.get('issues', []))}</p>"
        
        # Index Fragmentation
        if 'index_fragmentation' in results:
            idx = results['index_fragmentation']
            status = SecurityValidator.sanitize_for_html(idx.get('status', 'unknown').upper())
            html += f"<h3>Index Fragmentation: {status}</h3>"
            html += f"<p>Fragmented Indexes: {len(idx.get('fragmented_indexes', []))}</p>"
        
        # Deadlocks
        if 'deadlocks' in results:
            dl = results['deadlocks']
            status = SecurityValidator.sanitize_for_html(dl.get('status', 'unknown').upper())
            html += f"<h3>Deadlocks: {status}</h3>"
            html += f"<p>Recent Deadlocks: {dl.get('deadlock_count', 0)}</p>"
        
        # Tables
        if 'table_analysis' in results:
            ta = results['table_analysis']
            status = SecurityValidator.sanitize_for_html(ta.get('status', 'unknown').upper())
            html += f"<h3>Table Analysis: {status}</h3>"
            html += f"<p>Total Tables: {ta.get('total_tables', 0)}, "
            html += f"Large Tables: {len(ta.get('large_tables', []))}, "
            html += f"Total Size: {ta.get('total_size_mb', 0):.2f} MB</p>"
        
        # Corruption
        if 'corruption' in results:
            corr = results['corruption']
            status = SecurityValidator.sanitize_for_html(corr.get('status', 'unknown').upper())
            html += f"<h3>Corruption: {status}</h3>"
            html += f"<p>Corruption Issues: {len(corr.get('corruption_issues', []))}</p>"
        
        return html
    
    def populate_schema_table(self, data):
        """Populate schema health table."""
        issues = data.get('issues', [])
        self.schema_table.setRowCount(len(issues))
        self.schema_table.setColumnCount(4)
        self.schema_table.setHorizontalHeaderLabels(["Type", "Table", "Severity", "Message"])
        
        for i, issue in enumerate(issues):
            self.schema_table.setItem(i, 0, QTableWidgetItem(issue.get('type', '')))
            self.schema_table.setItem(i, 1, QTableWidgetItem(issue.get('table', '')))
            self.schema_table.setItem(i, 2, QTableWidgetItem(issue.get('severity', '')))
            self.schema_table.setItem(i, 3, QTableWidgetItem(issue.get('message', '')))
        
        self.schema_table.resizeColumnsToContents()
    
    def populate_index_table(self, data):
        """Populate index fragmentation table."""
        indexes = data.get('fragmented_indexes', [])
        self.index_table.setRowCount(len(indexes))
        self.index_table.setColumnCount(4)
        self.index_table.setHorizontalHeaderLabels(["Table", "Index", "Fragmentation %", "Rows"])
        
        for i, idx in enumerate(indexes):
            self.index_table.setItem(i, 0, QTableWidgetItem(idx.get('table_name', '')))
            self.index_table.setItem(i, 1, QTableWidgetItem(idx.get('index_name', '')))
            self.index_table.setItem(i, 2, QTableWidgetItem(f"{idx.get('fragmentation_percent', 0):.2f}"))
            self.index_table.setItem(i, 3, QTableWidgetItem(str(idx.get('num_rows', 0))))
        
        self.index_table.resizeColumnsToContents()
    
    def populate_deadlock_table(self, data):
        """Populate deadlock table."""
        deadlocks = data.get('recent_deadlocks', [])
        self.deadlock_table.setRowCount(len(deadlocks))
        self.deadlock_table.setColumnCount(5)
        self.deadlock_table.setHorizontalHeaderLabels(["Type", "Session 1", "Session 2", "Time", "Severity"])
        
        for i, dl in enumerate(deadlocks):
            self.deadlock_table.setItem(i, 0, QTableWidgetItem(dl.get('type', '')))
            self.deadlock_table.setItem(i, 1, QTableWidgetItem(str(dl.get('session_1', dl.get('blocking_session', '')))))
            self.deadlock_table.setItem(i, 2, QTableWidgetItem(str(dl.get('session_2', dl.get('waiting_session', '')))))
            self.deadlock_table.setItem(i, 3, QTableWidgetItem(dl.get('detection_time', dl.get('deadlock_time', ''))))
            self.deadlock_table.setItem(i, 4, QTableWidgetItem(dl.get('severity', '')))
        
        self.deadlock_table.resizeColumnsToContents()
    
    def populate_tables_table(self, data):
        """Populate tables analysis table."""
        tables = data.get('table_details', [])
        self.tables_table.setRowCount(len(tables))
        self.tables_table.setColumnCount(4)
        self.tables_table.setHorizontalHeaderLabels(["Table Name", "Rows", "Size (MB)", "Status"])
        
        for i, table in enumerate(tables):
            self.tables_table.setItem(i, 0, QTableWidgetItem(table.get('table_name', '')))
            self.tables_table.setItem(i, 1, QTableWidgetItem(str(table.get('num_rows', 0))))
            self.tables_table.setItem(i, 2, QTableWidgetItem(f"{table.get('size_mb', 0):.2f}"))
            status = "Large" if table in data.get('large_tables', []) else "OK"
            self.tables_table.setItem(i, 3, QTableWidgetItem(status))
        
        self.tables_table.resizeColumnsToContents()
    
    def populate_corruption_table(self, data):
        """Populate corruption table."""
        issues = data.get('corruption_issues', []) + data.get('upgrade_inconsistencies', [])
        self.corruption_table.setRowCount(len(issues))
        self.corruption_table.setColumnCount(4)
        self.corruption_table.setHorizontalHeaderLabels(["Type", "Severity", "Object", "Message"])
        
        for i, issue in enumerate(issues):
            self.corruption_table.setItem(i, 0, QTableWidgetItem(issue.get('type', '')))
            self.corruption_table.setItem(i, 1, QTableWidgetItem(issue.get('severity', '')))
            obj = issue.get('object_name', issue.get('table', issue.get('database', '')))
            self.corruption_table.setItem(i, 2, QTableWidgetItem(obj))
            self.corruption_table.setItem(i, 3, QTableWidgetItem(issue.get('message', '')))
        
        self.corruption_table.resizeColumnsToContents()
    
    def populate_remediation_text(self, data):
        """Populate remediation text."""
        html = "<h2>Remediation Plan</h2>"
        
        if data.get('critical_actions'):
            html += "<h3>Critical Actions</h3><ul>"
            for action in data['critical_actions']:
                action_text = SecurityValidator.sanitize_for_html(action.get('action', ''))
                command_text = SecurityValidator.sanitize_for_html(action.get('command', ''))
                impact_text = SecurityValidator.sanitize_for_html(action.get('impact', ''))
                html += f"<li><b>{action_text}</b><br/>"
                html += f"Command: <code>{command_text}</code><br/>"
                html += f"Impact: {impact_text}</li>"
            html += "</ul>"
        
        if data.get('high_priority_actions'):
            html += "<h3>High Priority Actions</h3><ul>"
            for action in data['high_priority_actions']:
                action_text = SecurityValidator.sanitize_for_html(action.get('action', ''))
                command_text = SecurityValidator.sanitize_for_html(action.get('command', ''))
                html += f"<li><b>{action_text}</b><br/>"
                html += f"Command: <code>{command_text}</code></li>"
            html += "</ul>"
        
        if data.get('preventive_measures'):
            html += "<h3>Preventive Measures</h3><ul>"
            for measure in data['preventive_measures']:
                measure_text = SecurityValidator.sanitize_for_html(measure)
                html += f"<li>{measure_text}</li>"
            html += "</ul>"
        
        self.remediation_text.setHtml(html)
    
    def export_html(self):
        """Export results to HTML."""
        if not self.analysis_results:
            QMessageBox.warning(self, "No Data", "Please run analysis first.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save HTML Report", "", "HTML Files (*.html)"
        )
        
        if filename:
            # Validate file path
            if not SecurityValidator.validate_file_path(filename, ['.html']):
                QMessageBox.warning(self, "Invalid Path", "Invalid file path or extension.")
                return
            
            try:
                generator = HTMLReportGenerator()
                generator.generate_report(self.analysis_results, filename)
                QMessageBox.information(self, "Success", "HTML report saved successfully")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export HTML: {str(e)}")
    
    def export_pdf(self):
        """Export results to PDF."""
        if not self.analysis_results:
            QMessageBox.warning(self, "No Data", "Please run analysis first.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save PDF Report", "", "PDF Files (*.pdf)"
        )
        
        if filename:
            # Validate file path
            if not SecurityValidator.validate_file_path(filename, ['.pdf']):
                QMessageBox.warning(self, "Invalid Path", "Invalid file path or extension.")
                return
            
            try:
                generator = PDFReportGenerator()
                generator.generate_report(self.analysis_results, filename)
                QMessageBox.information(self, "Success", "PDF report saved successfully")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {str(e)}")
    
    def refresh_logs(self):
        """Refresh the log viewer with latest log entries."""
        try:
            log_dir = os.path.join(os.getcwd(), 'logs')
            log_file = os.path.join(log_dir, 'p6_analyzer.log')
            
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read last 1000 lines
                    lines = f.readlines()
                    if len(lines) > 1000:
                        lines = lines[-1000:]
                    
                    log_content = ''.join(lines)
                    self.log_text.setPlainText(log_content)
                    # Scroll to bottom
                    cursor = self.log_text.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    self.log_text.setTextCursor(cursor)
        except Exception as e:
            logger.warning(f"Failed to refresh logs: {str(e)}")
    
    def clear_log_display(self):
        """Clear the log display (does not delete log files)."""
        self.log_text.clear()

