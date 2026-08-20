import dash
import pycountry
from dash import html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import os
import numpy as np

dash.register_page(__name__, path="/timelapseWaterComposition", title="Water Composition Worldwide")  # Page name for app.py

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
JSON_DIR = os.path.join(BASE_DIR, "json")
JSON_UN_DIR = os.path.join(JSON_DIR, "UN_JSON")

# List of parameters to show
PARAMS_TO_KEEP = {
    "Copper.json", "Nickel.json", "pH.json", "Lead.json", "Zinc.json", "Cadmium.json", "Temperature.json",
    "Chloride.json", "Mercury.json", "Other_Nitrogen.json", "Chromium.json", "Calcium.json",
    "Arsenic.json", "Oxidized_Nitrogen.json", "Potassium.json", "Magnesium.json", "Sodium.json", "Phosphorus.json",
    "Dissolved_Gas.json"
}

json_files = {}
if os.path.exists(JSON_UN_DIR):
    for filename in os.listdir(JSON_UN_DIR):
        if filename.endswith(".json") and filename in PARAMS_TO_KEEP:
            param_name = filename.replace(".json", "")
            json_files[param_name] = os.path.join(JSON_UN_DIR, filename)

# Default Dataset
default_param = list(json_files.keys())[0] if json_files else None

# Extract available Year Bins
df = pd.read_json(json_files[default_param]) if default_param and os.path.exists(json_files[default_param]) else pd.DataFrame(columns=["ISO3", "Year_Bin", "Value"])
available_year_bins = sorted(df["Year_Bin"].dropna().unique().tolist()) if not df.empty else []

# Descriptions for each parameter
PARAMETER_DESCRIPTIONS = {
    "Copper": "🔹An essential trace element, but high concentrations from industrial waste and mining can be toxic to aquatic life and humans.",
    "Nickel": "🔹A metal found in water due to industrial activities and natural sources; excessive exposure can be harmful to ecosystems and human health.",
    "pH": "🔹Determines water acidity or alkalinity, crucial for chemical stability and aquatic life. Extreme pH can lead to toxic metal dissolution.",
    "Lead": "🔹A toxic heavy metal from industrial pollution and old pipes. Even at low levels, it can cause severe health issues, especially in children.",
    "Zinc": "🔹A trace metal needed in small amounts but can become toxic due to industrial discharges, affecting aquatic organisms and water quality.",
    "Cadmium": "🔹A toxic heavy metal from mining and industrial waste. It accumulates in organisms, causing kidney damage and other health risks.",
    "Temperature": "🔹Water temperature affects oxygen levels, chemical reactions, and aquatic life. Rising temperatures can lead to ecosystem imbalances.",
    "Chloride": "🔹Common in seawater and road salts, excessive chloride levels can make freshwater unsuitable for drinking and harm aquatic organisms.",
    "Mercury": "🔹A hazardous metal from industrial pollution. It accumulates in the food chain, posing neurological risks to humans and wildlife.",
    "Other_Nitrogen": "🔹Includes various nitrogen compounds affecting water quality. High levels contribute to eutrophication and oxygen depletion.",
    "Chromium": "🔹A metal used in industry, with some forms being highly toxic and carcinogenic. It contaminates water through industrial waste.",
    "Water": "🔹A fundamental resource for life, its quality is crucial for human health, agriculture, and ecosystems.",
    "Calcium": "🔹An essential mineral for water hardness, affecting plumbing and aquatic organisms. Found naturally in groundwater.",
    "Arsenic": "🔹A toxic element from natural and industrial sources. Long-term exposure in drinking water is linked to serious health risks.",
    "Oxidized_Nitrogen": "🔹Includes nitrates and nitrites, often from fertilizers. Excess levels can contaminate drinking water and harm ecosystems.",
    "Potassium": "🔹A vital nutrient in water but can reach high levels due to agricultural runoff, affecting drinking water and aquatic life.",
    "Magnesium": "🔹A natural component of water, influencing hardness. It is essential for biological functions but excessive levels can impact taste.",
    "Sodium": "🔹Affects water salinity, with high concentrations from seawater intrusion and industrial waste, impacting drinking water quality.",
    "Phosphorus": "🔹Excess phosphorus from fertilizers and sewage leads to algal blooms, depleting oxygen and harming aquatic ecosystems.",
    "Dissolved_Gas": "🔹Includes oxygen and other gases essential for aquatic life. Changes in levels indicate pollution and ecosystem health."
}


def iso3_to_country(iso3):
    """Convert ISO3 country code to country name."""
    try:
        return pycountry.countries.get(alpha_3=iso3).name
    except AttributeError:
        return iso3

# Page Layout
def layout():
    return html.Div([
        html.H2("🌍 Water Composition Worldwide", style={
            'textAlign': 'center', 
            'color': '#ffffff',
            'fontSize': '32px',
            'padding': '20px',
            'fontWeight': 'bold',
            'textShadow': '2px 2px 4px #000',
            'fontFamily': 'Arial, sans-serif',
            'backgroundImage': 'url("/assets/water.jpeg")',
            'backgroundSize': 'cover',
            'backgroundPosition': 'center',
            'backgroundRepeat': 'no-repeat',
            'width': '100%',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
        }),

        # Dropdown for parameter selection
        html.Div([
            html.Label("Select Parameter:", style={
                'fontSize': '16px',
                'fontWeight': 'bold',
                'marginRight': '10px',
                'whiteSpace': 'nowrap'
            }), 
            dcc.Dropdown(
                id="parameter-selector",
                options=[{"label": key, "value": key} for key in json_files.keys()],
                value=default_param,
                clearable=False,
                className="custom-dropdown",
                style={'width': '100%'}
            )
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'gap': '10px',
            'width': '30%',
            'padding': '10px',
            'borderRadius': '8px',
            'backgroundColor': '#b3caf5',
            'boxShadow': '2px 2px 10px rgba(0,0,0,0.1)'
        }),

        # Description box for selected parameter
        html.Div(id="parameter-description", className="description-box", style={
            'marginBottom': '20px', 
            'fontSize': '16px',
            'padding': '10px'
        }),

        # Dropdown for year bin selection
        html.Div([
            html.Label("Select Year Bin:", style={
                'fontSize': '16px',
                'fontWeight': 'bold',
                'marginRight': '25px',
                'whiteSpace': 'nowrap'
            }),
            dcc.Dropdown(
                id="year_bin_selector",
                options=[{"label": year_bin, "value": year_bin} for year_bin in available_year_bins],
                value=available_year_bins[0] if available_year_bins else None,
                clearable=False,
                className="custom-dropdown",
                style={'width': '100%'}
            )
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'gap': '10px',
            'width': '30%',
            'padding': '10px',
            'borderRadius': '8px',
            'backgroundColor': '#b3caf5',
            'boxShadow': '2px 2px 10px rgba(0,0,0,0.1)'
        }),

        dcc.Graph(id="water-quality-map", style={'height': '95vh'})
    ], style={"backgroundColor": "#b3caf5"})

# Callback to update the description box based on selected parameter
@callback(
    Output("parameter-description", "children"),
    Input("parameter-selector", "value")
)
def update_description(selected_param):
    """Update the description box based on the selected parameter."""
    return PARAMETER_DESCRIPTIONS.get(selected_param, "Pas de description disponible.")

# Callback to update year bins when parameter changes
@callback(
    Output("year_bin_selector", "options"),
    Output("year_bin_selector", "value"),
    Input("parameter-selector", "value")
)

def update_year_bins(selected_param):
    """Update the year bins based on the selected parameter."""
    if selected_param not in json_files:
        return [], None

    json_file = json_files[selected_param]

    if os.path.exists(json_file):
        df = pd.read_json(json_file)
        available_year_bins = sorted(df["Year_Bin"].dropna().astype(str).unique().tolist(), reverse=True)
    else:
        available_year_bins = []

    if not available_year_bins:
        return [], None

    return [{"label": year_bin, "value": year_bin} for year_bin in available_year_bins], available_year_bins[0]

# Callback to update the map based on selected parameter and year bin
@callback(
    Output("water-quality-map", "figure"),
    [Input("parameter-selector", "value"),
     Input("year_bin_selector", "value")]
)
def update_map(selected_param, selected_year_bin):
    """Update the map based on the selected parameter and year bin."""
    if selected_param not in json_files or selected_year_bin is None:
        return px.choropleth_mapbox()

    json_file = json_files[selected_param]

    if os.path.exists(json_file):
        df = pd.read_json(json_file)
    else:
        return px.choropleth_mapbox()

    df_filtered = df[df["Year_Bin"].astype(str) == str(selected_year_bin)]

    if df_filtered.empty:
        return px.choropleth_mapbox()

    df_filtered = df_filtered.dropna(subset=["ISO3"])
    df_filtered["Country"] = df_filtered["ISO3"].apply(iso3_to_country)
    df_filtered["Log_Value"] = df_filtered["Value"].apply(lambda x: np.log1p(x))
    unit_label = df_filtered["Unit"].iloc[0] if "Unit" in df_filtered.columns and not df_filtered["Unit"].isna().all() else ""
    fig = px.choropleth(df_filtered,
                        locations="Country",
                        locationmode="country names",
                        color="Log_Value",
                        color_continuous_scale="Viridis",
                        title=f"{selected_param} Concentration in {selected_year_bin}",
                        labels={"Log_Value": f"Log({selected_param} + 1) {unit_label}"})
    fig.update_geos(
        projection_type="orthographic",
        showcoastlines=True,
        coastlinecolor="Black",
        showland=True,
        landcolor="lightgray",
        showlakes=True,
        lakecolor="lightblue",
        showcountries=True,
        projection_rotation=dict(lon=15, lat=25),
        projection_scale=1,
        bgcolor="#b3caf5"
    )

    fig.update_layout(
        paper_bgcolor="#b3caf5"
    )

    return fig
