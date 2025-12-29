"""Chart generation for reports."""

from typing import Dict, List, Any
import plotly.graph_objects as go
import plotly.express as px
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ChartGenerator:
    """Generates charts for reports."""
    
    def generate_bar_chart(
        self,
        data: Dict[str, float],
        title: str = "Bar Chart"
    ) -> str:
        """Generate bar chart HTML."""
        fig = go.Figure(data=[
            go.Bar(x=list(data.keys()), y=list(data.values()))
        ])
        fig.update_layout(title=title)
        return fig.to_html(include_plotlyjs='cdn')
    
    def generate_line_chart(
        self,
        data: List[Dict[str, Any]],
        x_field: str,
        y_field: str,
        title: str = "Line Chart"
    ) -> str:
        """Generate line chart HTML."""
        x_values = [d[x_field] for d in data]
        y_values = [d[y_field] for d in data]
        
        fig = go.Figure(data=go.Scatter(x=x_values, y=y_values, mode='lines+markers'))
        fig.update_layout(title=title)
        return fig.to_html(include_plotlyjs='cdn')
    
    def generate_pie_chart(
        self,
        data: Dict[str, float],
        title: str = "Pie Chart"
    ) -> str:
        """Generate pie chart HTML."""
        fig = go.Figure(data=[go.Pie(labels=list(data.keys()), values=list(data.values()))])
        fig.update_layout(title=title)
        return fig.to_html(include_plotlyjs='cdn')

