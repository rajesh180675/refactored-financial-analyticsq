import io
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List


class ReportingService:
    def __init__(self, config_manager, state_manager, event_system):
        self.config = config_manager
        self.state = state_manager
        self.events = event_system
        self.logger = logging.getLogger(__name__)

    def generate_excel_report(self, analysis: Dict[str, Any], filename: str = "analysis.xlsx") -> bytes:
        try:
            self.events.publish("report_generation_started", {"type": "excel", "filename": filename}, "ReportingService")
            
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Summary sheet
                if 'summary' in analysis:
                    summary_df = pd.DataFrame([analysis['summary']])
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Ratios sheets
                if 'ratios' in analysis:
                    for category, ratio_df in analysis['ratios'].items():
                        if isinstance(ratio_df, pd.DataFrame):
                            sheet_name = f'Ratios_{category}'[:31]
                            ratio_df.to_excel(writer, sheet_name=sheet_name)
                
                # Trends sheet
                if 'trends' in analysis:
                    trends_data = []
                    for metric, trend in analysis['trends'].items():
                        if isinstance(trend, dict):
                            trend_row = {'Metric': metric}
                            trend_row.update(trend)
                            trends_data.append(trend_row)
                    
                    if trends_data:
                        trends_df = pd.DataFrame(trends_data)
                        trends_df.to_excel(writer, sheet_name='Trends', index=False)
                
                # Insights sheet
                if 'insights' in analysis:
                    insights_df = pd.DataFrame({'Insights': analysis['insights']})
                    insights_df.to_excel(writer, sheet_name='Insights', index=False)
            
            output.seek(0)
            report_data = output.read()
            
            self.events.publish("report_generation_completed", {"type": "excel", "size": len(report_data)}, "ReportingService")
            return report_data
            
        except Exception as e:
            self.logger.error(f"Excel report generation failed: {e}")
            self.events.publish("report_generation_failed", {"type": "excel", "error": str(e)}, "ReportingService")
            raise

    def generate_markdown_report(self, analysis: Dict[str, Any]) -> str:
        try:
            self.events.publish("report_generation_started", {"type": "markdown"}, "ReportingService")
            
            lines = [
                f"# Financial Analysis Report",
                f"\n**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"\n**Company:** {analysis.get('company_name', 'Financial Analysis')}",
                "\n---\n"
            ]
            
            # Summary section
            if 'summary' in analysis:
                summary = analysis['summary']
                lines.extend([
                    "## Executive Summary\n",
                    f"- **Total Metrics Analyzed:** {summary.get('total_metrics', 'N/A')}",
                    f"- **Period Covered:** {summary.get('year_range', 'N/A')}",
                ])
                
                if 'quality_score' in analysis:
                    lines.append(f"- **Data Quality Score:** {analysis['quality_score']:.1f}%")
                
                lines.append("\n")
            
            # Key Insights
            if 'insights' in analysis and analysis['insights']:
                lines.extend([
                    "## Key Insights\n"
                ])
                for insight in analysis['insights']:
                    lines.append(f"- {insight}")
                lines.append("\n")
            
            # Financial Ratios
            if 'ratios' in analysis:
                lines.extend([
                    "## Financial Ratios\n"
                ])
                
                for category, ratio_df in analysis['ratios'].items():
                    if isinstance(ratio_df, pd.DataFrame) and not ratio_df.empty:
                        lines.append(f"\n### {category} Ratios\n")
                        lines.append(ratio_df.to_markdown())
                        lines.append("\n")
            
            report_content = "\n".join(lines)
            
            self.events.publish("report_generation_completed", {"type": "markdown", "size": len(report_content)}, "ReportingService")
            return report_content
            
        except Exception as e:
            self.logger.error(f"Markdown report generation failed: {e}")
            self.events.publish("report_generation_failed", {"type": "markdown", "error": str(e)}, "ReportingService")
            raise
