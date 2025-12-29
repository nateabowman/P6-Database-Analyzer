"""PDF report generator for P6 database analysis."""

from typing import Dict, Any
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class PDFReportGenerator:
    """Generates PDF reports from analysis results."""
    
    def generate_report(self, results: Dict[str, Any], filename: str):
        """
        Generate PDF report.
        
        Args:
            results: Analysis results dictionary
            filename: Output filename
        """
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30
        )
        story.append(Paragraph("Primavera P6 Database Analysis Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_data = [['Metric', 'Value']]
        
        if 'schema_health' in results:
            sh = results['schema_health']
            summary_data.append(['Schema Health', sh.get('status', 'unknown').upper()])
        
        if 'index_fragmentation' in results:
            idx = results['index_fragmentation']
            summary_data.append(['Index Fragmentation', idx.get('status', 'unknown').upper()])
            summary_data.append(['Fragmented Indexes', len(idx.get('fragmented_indexes', []))])
        
        if 'deadlocks' in results:
            dl = results['deadlocks']
            summary_data.append(['Deadlocks', dl.get('deadlock_count', 0)])
        
        if 'table_analysis' in results:
            ta = results['table_analysis']
            summary_data.append(['Total Tables', ta.get('total_tables', 0)])
            summary_data.append(['Total Size (MB)', f"{ta.get('total_size_mb', 0):.2f}"])
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Schema Health
        if 'schema_health' in results:
            story.append(PageBreak())
            story.append(Paragraph("Schema Health Analysis", styles['Heading2']))
            sh = results['schema_health']
            story.append(Paragraph(f"Status: {sh.get('status', 'unknown').upper()}", styles['Normal']))
            story.append(Paragraph(f"Tables: {sh.get('table_count', 0)}, Indexes: {sh.get('index_count', 0)}", styles['Normal']))
            
            if sh.get('issues'):
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("Issues Found", styles['Heading3']))
                issue_data = [['Type', 'Table', 'Severity', 'Message']]
                for issue in sh['issues'][:50]:  # Limit to 50 for PDF
                    issue_data.append([
                        issue.get('type', ''),
                        issue.get('table', 'N/A'),
                        issue.get('severity', ''),
                        issue.get('message', '')[:100]  # Truncate long messages
                    ])
                
                issue_table = Table(issue_data, colWidths=[1*inch, 1.5*inch, 1*inch, 3.5*inch])
                issue_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.beige])
                ]))
                story.append(issue_table)
        
        # Index Fragmentation
        if 'index_fragmentation' in results:
            story.append(PageBreak())
            story.append(Paragraph("Index Fragmentation Analysis", styles['Heading2']))
            idx = results['index_fragmentation']
            story.append(Paragraph(f"Status: {idx.get('status', 'unknown').upper()}", styles['Normal']))
            
            if idx.get('fragmented_indexes'):
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("Fragmented Indexes", styles['Heading3']))
                frag_data = [['Table', 'Index', 'Fragmentation %', 'Rows']]
                for frag_idx in idx['fragmented_indexes'][:50]:
                    frag_data.append([
                        frag_idx.get('table_name', ''),
                        frag_idx.get('index_name', ''),
                        f"{frag_idx.get('fragmentation_percent', 0):.2f}",
                        str(frag_idx.get('num_rows', frag_idx.get('page_count', 'N/A')))
                    ])
                
                frag_table = Table(frag_data, colWidths=[2*inch, 2*inch, 1.5*inch, 1.5*inch])
                frag_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.beige])
                ]))
                story.append(frag_table)
        
        # Deadlocks
        if 'deadlocks' in results:
            story.append(PageBreak())
            story.append(Paragraph("Deadlock Analysis", styles['Heading2']))
            dl = results['deadlocks']
            story.append(Paragraph(f"Deadlock Count: {dl.get('deadlock_count', 0)}", styles['Normal']))
            
            if dl.get('recent_deadlocks'):
                story.append(Spacer(1, 0.2*inch))
                deadlock_data = [['Type', 'Session 1', 'Session 2', 'Time', 'Severity']]
                for deadlock in dl['recent_deadlocks'][:30]:
                    deadlock_data.append([
                        deadlock.get('type', ''),
                        str(deadlock.get('session_1', deadlock.get('blocking_session', 'N/A'))),
                        str(deadlock.get('session_2', deadlock.get('waiting_session', 'N/A'))),
                        str(deadlock.get('detection_time', deadlock.get('deadlock_time', '')))[:20],
                        deadlock.get('severity', '')
                    ])
                
                dl_table = Table(deadlock_data, colWidths=[1*inch, 1*inch, 1*inch, 2*inch, 1*inch])
                dl_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.beige])
                ]))
                story.append(dl_table)
        
        # Remediation
        if 'remediation' in results:
            story.append(PageBreak())
            story.append(Paragraph("Remediation Plan", styles['Heading2']))
            rem = results['remediation']
            story.append(Paragraph(f"Estimated Impact: {rem.get('estimated_impact', 'unknown').upper()}", styles['Normal']))
            
            if rem.get('critical_actions'):
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("Critical Actions", styles['Heading3']))
                for action in rem['critical_actions'][:20]:
                    story.append(Paragraph(f"• {action.get('action', '')}", styles['Normal']))
                    story.append(Paragraph(f"  Command: {action.get('command', '')}", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            if rem.get('high_priority_actions'):
                story.append(Paragraph("High Priority Actions", styles['Heading3']))
                for action in rem['high_priority_actions'][:20]:
                    story.append(Paragraph(f"• {action.get('action', '')}", styles['Normal']))
                    story.append(Spacer(1, 0.05*inch))
        
        # Build PDF
        doc.build(story)

