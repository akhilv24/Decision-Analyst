"""
Export Module
Handles data export to various formats including professional PDF reports with charts.
"""

import pandas as pd
import logging
import os
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataExporter:
    """Handles data export to various formats."""
    
    def __init__(self, df):
        """
        Initialize exporter with dataframe.
        
        Args:
            df (pd.DataFrame): Data to export
        """
        self.df = df.copy() if df is not None else None
    
    def export_to_csv(self, output_path):
        """Export data to CSV format."""
        if self.df is None:
            logger.error("No data to export")
            return False
        
        try:
            self.df.to_csv(output_path, index=False)
            logger.info(f"Data exported to CSV: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False
    
    def export_category_summary(self, output_path):
        """Export category summary to CSV."""
        if self.df is None:
            logger.error("No data to export")
            return False
        
        try:
            if 'category' in self.df.columns and 'amount' in self.df.columns:
                summary = self.df.groupby('category')['amount'].agg(['sum', 'count', 'mean']).reset_index()
                summary.columns = ['Category', 'Total', 'Count', 'Average']
                summary.to_csv(output_path, index=False)
                logger.info(f"Category summary exported to: {output_path}")
                return True
            else:
                logger.error("Required columns (category, amount) not found")
                return False
        except Exception as e:
            logger.error(f"Error exporting category summary: {str(e)}")
            return False
    
    def get_export_summary(self):
        """Get summary of exported data."""
        if self.df is None:
            return {}
        
        return {
            'total_records': len(self.df),
            'columns': list(self.df.columns),
            'date_range': f"{self.df['date'].min()} to {self.df['date'].max()}" if 'date' in self.df.columns else 'N/A',
            'file_size_kb': self.df.memory_usage(deep=True).sum() / 1024,
            'export_timestamp': datetime.now().isoformat()
        }

    def generate_professional_pdf(self, analysis_results, ai_insights=None):
        """
        Generate a professional financial dashboard-style PDF report.
        
        Args:
            analysis_results (dict): Analysis results from TransactionAnalyzer
            ai_insights (dict): AI insights from AIAnalyzer (optional)
            
        Returns:
            BytesIO: PDF document as byte stream, or None on error
        """
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            pdf_buffer = BytesIO()
            # Use landscape orientation for better dashboard layout
            doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4), topMargin=0.3*inch, bottomMargin=0.3*inch, 
                                   leftMargin=0.4*inch, rightMargin=0.4*inch)
            
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'Title', parent=styles['Heading1'], fontSize=32, 
                textColor=colors.HexColor('#0056b3'), spaceAfter=6, alignment=1, 
                fontName='Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'Subtitle', parent=styles['Normal'], fontSize=12, 
                textColor=colors.HexColor('#666666'), spaceAfter=16, alignment=1
            )
            
            metric_label_style = ParagraphStyle(
                'MetricLabel', parent=styles['Normal'], fontSize=10, 
                textColor=colors.HexColor('#999999'), spaceAfter=4, alignment=1
            )
            
            metric_value_style = ParagraphStyle(
                'MetricValue', parent=styles['Heading2'], fontSize=18, 
                textColor=colors.HexColor('#0056b3'), spaceAfter=2, alignment=1, 
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'SectionHeading', parent=styles['Heading2'], fontSize=14, 
                textColor=colors.white, backColor=colors.HexColor('#0056b3'), 
                spaceAfter=12, spaceBefore=12, leftIndent=10, rightIndent=10,
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'Normal', parent=styles['Normal'], fontSize=9, spaceAfter=6, alignment=4
            )
            
            content = []
            
            # ===== HEADER =====
            content.append(Paragraph("DECISION ANALYST", title_style))
            content.append(Paragraph("Professional Financial Analysis Report", subtitle_style))
            content.append(Spacer(1, 0.15*inch))
            
            # ===== KEY METRICS CARDS (DASHBOARD STYLE) =====
            stats = analysis_results.get('summary_statistics', {})
            
            # Create metric cards in grid layout
            total_spent = stats.get('total_spent', 0)
            total_transactions = stats.get('total_transactions', 0)
            avg_transaction = stats.get('average_transaction', 0)
            max_transaction = stats.get('max_transaction', 0)
            
            metric_card_width = 1.8 * inch
            metric_cards = [
                ['Total Spending', 'Total Transactions', 'Average Transaction', 'Max Transaction'],
                [
                    f"Rs. {total_spent:,.0f}",
                    f"{total_transactions:,}",
                    f"Rs. {avg_transaction:,.0f}",
                    f"Rs. {max_transaction:,.0f}"
                ]
            ]
            
            metric_table = Table(metric_cards, colWidths=[metric_card_width]*4)
            metric_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#666666')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#0056b3')),
                ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, 1), 14),
                ('TOPPADDING', (0, 1), (-1, 1), 12),
                ('BOTTOMPADDING', (0, 1), (-1, 1), 12),
                ('ROWBACKGROUNDS', (0, 0), (-1, 1), [colors.white, colors.HexColor('#0056b3')]),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0'))
            ]))
            
            content.append(metric_table)
            content.append(Spacer(1, 0.2*inch))
            
            # ===== CATEGORY ANALYSIS TABLE =====
            cat_analysis = analysis_results.get('category_analysis', {})
            if cat_analysis:
                cat_data = [['Category', 'Total Amount', 'Transactions', 'Average', 'Percentage']]
                total_amount = sum([v.get('total', 0) for v in cat_analysis.values()])
                
                sorted_categories = sorted(cat_analysis.items(), key=lambda x: x[1].get('total', 0), reverse=True)
                for cat, details in sorted_categories[:10]:
                    total = details.get('total', 0)
                    count = details.get('count', 0)
                    average = details.get('average', 0)
                    percentage = (total / total_amount * 100) if total_amount > 0 else 0
                    
                    cat_data.append([
                        cat[:20],
                        f"Rs. {total:,.0f}",
                        str(count),
                        f"Rs. {average:,.0f}",
                        f"{percentage:.1f}%"
                    ])
                
                cat_table = Table(cat_data, colWidths=[1.5*inch, 1.3*inch, 1*inch, 1.3*inch, 0.9*inch])
                cat_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0056b3')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                content.append(Paragraph("📈 Spending by Category", heading_style))
                content.append(cat_table)
                content.append(Spacer(1, 0.2*inch))
                
                # Generate and embed charts
                try:
                    pie_chart = self._generate_pie_chart(cat_analysis)
                    if pie_chart:
                        chart_img = RLImage(pie_chart, width=3.5*inch, height=2.8*inch)
                        content.append(Paragraph("Distribution Visualization", heading_style))
                        content.append(chart_img)
                        content.append(Spacer(1, 0.15*inch))
                except Exception as e:
                    logger.warning(f"Chart generation failed: {str(e)}")
            
            # ===== AI INSIGHTS SECTION =====
            if ai_insights:
                content.append(PageBreak())
                content.append(Paragraph("🤖 AI Financial Analysis", heading_style))
                
                # Executive Summary
                summary_text = ai_insights.get('summary', 'Analysis completed.')
                if summary_text:
                    content.append(Paragraph(f"<b>Executive Summary:</b>", heading_style))
                    content.append(Paragraph(summary_text, normal_style))
                    content.append(Spacer(1, 0.15*inch))
                
                # Recommendations
                recommendations = ai_insights.get('recommendations', [])
                if recommendations:
                    content.append(Paragraph("<b>Smart Recommendations:</b>", heading_style))
                    for i, rec in enumerate(recommendations[:8], 1):
                        rec_text = str(rec) if rec else f"Recommendation {i}"
                        content.append(Paragraph(f"{i}. {rec_text}", normal_style))
                    content.append(Spacer(1, 0.12*inch))
                
                # Patterns
                patterns = ai_insights.get('patterns', [])
                if patterns:
                    content.append(Paragraph("<b>Spending Patterns:</b>", heading_style))
                    for pattern in patterns[:5]:
                        pattern_text = str(pattern) if pattern else "Pattern detected"
                        content.append(Paragraph(f"• {pattern_text}", normal_style))
                    content.append(Spacer(1, 0.12*inch))
                
                # Anomalies
                anomalies = ai_insights.get('anomalies', [])
                if anomalies:
                    content.append(Paragraph("<b>Anomalies & Risk Flags:</b>", heading_style))
                    for anom in anomalies[:5]:
                        anom_text = str(anom) if anom else "Anomaly detected"
                        content.append(Paragraph(f"⚠️  {anom_text}", normal_style))
                    content.append(Spacer(1, 0.12*inch))
                
                # Risk Level
                risk_level = ai_insights.get('risk_level', 'MEDIUM')
                risk_colors = {
                    'LOW': '#10b981',
                    'MEDIUM': '#f59e0b',
                    'HIGH': '#ef4444',
                    'CRITICAL': '#dc2626'
                }
                risk_color = risk_colors.get(str(risk_level).upper(), '#f59e0b')
                content.append(Paragraph(
                    f"<b>Overall Risk Assessment:</b> <font color='{risk_color}'><b>{str(risk_level).upper()}</b></font>",
                    normal_style
                ))
            
            # ===== FOOTER =====
            content.append(Spacer(1, 0.3*inch))
            content.append(Paragraph(
                "© 2025-2026 Decision Analyst. Professional Finance Analysis System | Report Generated: " + 
                datetime.now().strftime('%B %d, %Y'),
                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#999999'), alignment=1)
            ))
            
            doc.build(content)
            pdf_buffer.seek(0)
            
            logger.info("Professional PDF generated successfully")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error generating professional PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_bar_chart(self, cat_analysis):
        """Generate a horizontal bar chart for category spending."""
        try:
            if not cat_analysis:
                return None
            
            categories = list(cat_analysis.keys())[:8]
            amounts = [cat_analysis[cat].get('total', 0) for cat in categories]
            
            fig, ax = plt.subplots(figsize=(10, 5))
            colors_list = ['#0056b3', '#0066cc', '#0077dd', '#0088ff', '#1199ff', '#22aaff', '#33bbff', '#44ccff']
            ax.barh(categories, amounts, color=colors_list[:len(categories)])
            ax.set_xlabel('Amount (Rs.)', fontsize=10, fontweight='bold')
            ax.set_title('Spending by Category', fontsize=12, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)
            
            # Format x-axis as currency
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'Rs. {x/100000:.1f}L' if x >= 100000 else f'Rs. {x/1000:.0f}K'))
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer
        except Exception as e:
            logger.warning(f"Bar chart generation failed: {str(e)}")
            return None
    
    def _generate_trend_chart(self, df):
        """Generate a line chart for spending trends over time."""
        try:
            if df is None or len(df) == 0:
                return None
            
            if 'date' not in df.columns or 'amount' not in df.columns:
                return None
            
            # Group by date and sum amounts
            daily_spending = df.groupby(pd.to_datetime(df['date']).dt.date)['amount'].sum().sort_index()
            
            if len(daily_spending) == 0:
                return None
            
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(range(len(daily_spending)), daily_spending.values, marker='o', linewidth=2, 
                   color='#0056b3', markersize=4)
            ax.fill_between(range(len(daily_spending)), daily_spending.values, alpha=0.2, color='#0056b3')
            ax.set_xlabel('Date', fontsize=10, fontweight='bold')
            ax.set_ylabel('Amount (Rs.)', fontsize=10, fontweight='bold')
            ax.set_title('Spending Trend', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Set x-axis labels
            step = max(1, len(daily_spending) // 6)
            ax.set_xticks(range(0, len(daily_spending), step))
            ax.set_xticklabels([str(daily_spending.index[i]) for i in range(0, len(daily_spending), step)], rotation=45)
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100, facecolor='white')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer
        except Exception as e:
            logger.warning(f"Trend chart generation failed: {str(e)}")
            return None

