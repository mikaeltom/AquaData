import dash
import pycountry
from dash import html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import numpy as np
import os

dash.register_page(__name__, path="/timelapseWaterUsage", title="Water Usage Worldwide")  # Page name for app.py

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
JSON_DIR = os.path.join(BASE_DIR, "json")
JSON_AQUASTAT_DIR = os.path.join(JSON_DIR, "AQUASTAT_JSON")

json_original_path = os.path.join(JSON_AQUASTAT_DIR, "aquastat.json")
json_predictions_path = os.path.join(JSON_AQUASTAT_DIR, "aquastat_predictions.json")

# Load original data
df_original = pd.read_json(json_original_path) if os.path.exists(json_original_path) else pd.DataFrame(columns=["ISO3", "Year", "Value", "Variable"])

# Load predicted data
df_predictions = pd.read_json(json_predictions_path) if os.path.exists(json_predictions_path) else pd.DataFrame(columns=["ISO3", "Year", "Value", "Variable"])

# Combine both datasets
df = pd.concat([df_original, df_predictions], ignore_index=True)

# Ensure correct data types
df["Year"] = df["Year"].astype(int)
df["Value"] = df["Value"].astype(float)

# Extract available indicators and years
available_variables = df["Variable"].unique().tolist() if not df.empty else []
available_years = sorted(df["Year"].dropna().unique().astype(int)) if not df.empty else []


# Indicator descriptions
indicator_descriptions = {
    "Agricultural water withdrawal as % of total renewable water resources" : "🔹Measures the proportion of total renewable freshwater resources that is used for agricultural purposes. A higher percentage may indicate significant water dependency for agriculture, which could impact sustainability and water availability for other uses. [Unit : %]",
    "SDG 6.4.1. Industrial Water Use Efficiency": "🔹Measures how efficiently industries use water to produce goods and services. Higher efficiency means less waste, lower costs, and reduced environmental impact. Poor efficiency can lead to water scarcity, pollution, and increased operational expenses. [Unit : US$/m3]",
    "SDG 6.4.1. Irrigated Agriculture Water Use Efficiency": "🔹Evaluates how effectively water is used for irrigation in farming. Efficient irrigation ensures food production with minimal water loss. Poor efficiency can lead to water shortages, soil degradation, and food insecurity. [Unit : US$/m3]",
    "SDG 6.4.1. Services Water Use Efficiency": "🔹Assesses how much water is consumed in the service sector (hotels, offices, healthcare, etc.). Improved efficiency reduces demand on water resources, lowers utility costs, and minimizes environmental footprint. [Unit : US$/m3]",
    "SDG 6.4.1. Water Use Efficiency": "🔹A broad measure of how effectively water is used across various sectors, including agriculture, industry, and services. Higher efficiency helps combat water scarcity, supports sustainable development, and protects ecosystems. [Unit : US$/m3]",
    "SDG 6.4.2. Water Stress": "🔹Represents the percentage of total water withdrawal compared to renewable freshwater availability. High water stress indicates overuse, leading to droughts, ecosystem degradation, and conflicts over resources. Low stress levels suggest sustainable water management practices. [Unit : %]",
}

def iso3_to_country(iso3):
    """Convert ISO3 country code to country name."""
    try:
        return pycountry.countries.get(alpha_3=iso3).name
    except AttributeError:
        return iso3

def layout():
    return html.Div([
        html.Div([
            html.H2("🌍 Water Usage Timelapse", style={
                'textAlign': 'center',
                'color': '#ffffff',
                'fontSize': '32px',
                'fontWeight': 'bold',
                'textShadow': '2px 2px 4px #000',
                'padding': '20px',
                'fontFamily': 'Arial, sans-serif'
            })
        ], style={
            'backgroundImage': 'url("/assets/water.jpeg")',
            'backgroundSize': 'cover',
            'backgroundPosition': 'center',
            'backgroundRepeat': 'no-repeat',
            'width': '100%',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
        }),

        # Indicator Selection
        html.Div([
            html.Label("Select Indicator:", style={'fontSize': '16px', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id="variable-selector",
                options=[{"label": var, "value": var} for var in available_variables],
                value=available_variables[0] if available_variables else None,
                clearable=False,
                className="custom-dropdown",
                style={'width': '100%'}
            )
        ], style={'width': '60%', 'padding': '10px', 'backgroundColor': '#b3caf5'}),

        # Indicator Description Section
        html.Div(id="indicator-description", className="description-box", style={
            'marginBottom': '20px',
            'fontSize': '16px',
            'padding': '10px'
        }),

        # Year Selection
        html.Div([
            html.Label("Select Year:", style={'fontSize': '16px', 'fontWeight': 'bold'}),
            dcc.Slider(
                id="year_slider_water_usage",
                min=min(available_years) if available_years else 2000,
                max=max(available_years) if available_years else 2030,
                marks={int(year): str(year) for year in available_years},
                step=None,
                value=min(available_years) if available_years else 2000,
                tooltip={"placement": "bottom", "always_visible": True},
                className="custom-slider"
            )
        ], style={'width': '80%', 'padding': '10px', 'backgroundColor': '#b3caf5'}),

        # Log Scale Toggle
        dcc.Checklist(
            id="log-toggle",
            options=[{"label": "Log Scale", "value": "log"}],
            value=["log"],
            inline=True,
            className='custom-log-toggle',
        ),

        # Map Display
        dcc.Graph(id="water-usage-map", style={'height': '90vh', 'width': '100%'})
    ], style={"backgroundColor": "#b3caf5"})


# Callback to update the indicator description
@callback(
    Output("indicator-description", "children"),
    Input("variable-selector", "value")
)

def update_description(selected_variable):
    """Update the description based on the selected indicator."""
    if selected_variable in indicator_descriptions:
        return indicator_descriptions[selected_variable]
    return "Select an indicator to see its description."

# Callback to update the year options based on selected indicator
@callback(
    Output("year_slider_water_usage", "min"),
    Output("year_slider_water_usage", "max"),
    Output("year_slider_water_usage", "marks"),
    Output("year_slider_water_usage", "value"),
    Input("variable-selector", "value")
)

def update_year_options(selected_variable):
    """Update the year slider based on the selected indicator."""
    if selected_variable is None or df.empty:
        return 2000, 2030, {}, 2000

    df_filtered = df[df["Variable"] == selected_variable]
    predicted_years = [2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]
    available_years = sorted(set(df_filtered["Year"].dropna().astype(int)).union(predicted_years))

    if not available_years:
        return 2000, 2030, {}, 2000

    return int(min(available_years)), int(max(available_years)), {int(year): str(year) for year in available_years}, int(min(available_years))


# Callback to update the map based on selected indicator and year
@callback(
    Output("water-usage-map", "figure"),
    Input("variable-selector", "value"),
    Input("year_slider_water_usage", "value"),
    Input("log-toggle", "value")
)

def update_map(selected_variable, selected_year, log_toggle):
    """Update the choropleth map based on selected indicator and year."""
    if selected_variable is None or selected_year is None:
        return px.choropleth()  # Return an empty map

    df_filtered = df[(df["Variable"] == selected_variable) & (df["Year"] == selected_year)]

    if df_filtered.empty:
        return px.choropleth()  # Empty map if no data

    df_filtered = df_filtered.dropna(subset=["ISO3"])
    df_filtered["Country"] = df_filtered["ISO3"].apply(iso3_to_country)

    if "log" in log_toggle:
        df_filtered["Value"] = df_filtered["Value"].apply(lambda x: np.random.uniform(0.001, 0.01) if x < 0 else x) # Avoiding error values
        df_filtered["Value"] = np.log1p(df_filtered["Value"])

    df["Value"] = df["Value"].apply(lambda x: np.random.uniform(0.001, 0.01) if x < 0 else x)

    fig = px.choropleth(df_filtered,
                        locations="Country",
                        locationmode="country names",
                        color="Value",
                        color_continuous_scale="Viridis",
                        title=f"{selected_variable} ({selected_year})")

    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=800,
        paper_bgcolor="#b3caf5",
    )

    fig.update_geos(
        projection_type="natural earth",
        showcoastlines=True,
        coastlinecolor="Black",
        showland=True,
        landcolor="lightgray",
        showlakes=True,
        lakecolor="lightblue",
        showcountries=True,
        projection_scale=1.2,
        bgcolor="#b3caf5"
    )

    return fig
