import altair as alt
import pandas as pd
import os
from UI.navigation_interface.workspace.views.analysis.chart_configurations.parameter_holders import HistogramParameters
import plotly.express as px

class PlotGenerator:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def generate_plot(self, chart_type, parameters, plot_name="plot"):
        """Generates the specified chart type using Altair."""

        if chart_type == "histogram":
            x_data, group_data = parameters.get_data(self.data_manager)
            df = pd.DataFrame({'x': x_data, 'group': group_data})

            if parameters.layered:
                fig = px.histogram(
                    df,
                    x="x",
                    color="group",
                    nbins=parameters.num_bins,
                    barmode="overlay",  # For layered histograms
                    opacity=0.3,  # Adjust opacity as needed
                    title=parameters.x_variable,
                    histnorm='percent' if parameters.relative_frequency else None,
                    marginal = 'box'
                )

            else:
                fig = px.histogram(
                    df,
                    x="x",
                    nbins=parameters.num_bins,
                    title=parameters.x_variable,
                    histnorm='percent' if parameters.relative_frequency else None,
                    marginal='box'
                )

            if parameters.show_mean:
                fig.add_vline(x=df['x'].mean(), line_width=3, line_dash="dash", line_color="red")


            plot_html_path = os.path.abspath(os.path.join("temp", f"{plot_name}.html"))
            plot_png_path = os.path.abspath(os.path.join("temp", f"{plot_name}.png"))
            os.makedirs("temp", exist_ok=True)
            fig.write_html(plot_html_path)
            # Optionally generate PNG: fig.write_image(plot_png_path)

            return plot_png_path, plot_html_path
        elif chart_type == "scatter":
            x_data, y_data, size_data, color_data = parameters.get_data(self.data_manager)
            df = pd.DataFrame({'x': x_data, 'y': y_data, 'size': size_data, 'group': color_data})
            trendline_mapping = {"global": "ols", "per group": "ols", "none": None}

            fig = px.scatter(
                df,
                x='x',
                y='y',
                size = 'size' if parameters.size_variable else None, # Size by variable or uniform
                color='group' if parameters.color_variable else None, # Color by group or none
                marginal_x=parameters.marginal_x,
                marginal_y=parameters.marginal_y,
                trendline=trendline_mapping.get(parameters.trendline), # Add a trendline
                title = f"{parameters.y_variable} vs {parameters.x_variable}"
            )

            plot_html_path = os.path.abspath(os.path.join("temp", f"{plot_name}.html"))
            plot_png_path = os.path.abspath(os.path.join("temp", f"{plot_name}.png"))
            os.makedirs("temp", exist_ok=True)
            fig.write_html(plot_html_path)
            # (Optional PNG export)

            return plot_png_path, plot_html_path

        # Add other chart types here (e.g., scatter plot, etc.)
        return None, None