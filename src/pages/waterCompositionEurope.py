import dash
from dash import callback, Input, Output
import plotly.express as px
import pandas as pd
import os
import numpy as np
import pycountry
from dash import html
from dash import dcc

# European Limit (see report for details)
THRESHOLDS = {
    "Ammonium" : 5,
    "BOD5": 10,
    "Cadmium and its compounds" : 1.5,
    "Mercury and its compounds" : 0.07,
    "Nickel and its compounds" :  34,
    "Lead and its compounds" : 14,

}

# Select pollutants to display
filtered_pollutants = [
    "Ammonium",
    "BOD5",
    "Cadmium and its compounds",
    "Mercury and its compounds",
    "Nickel and its compounds",
    "Lead and its compounds",
]

# Descriptions for pollutants
POLLUTANT_DESCRIPTIONS = {
    "Ammonium": "🔹A key nitrogen compound in water, ammonium originates from agricultural runoff, sewage, and industrial waste. High concentrations indicate pollution and can be toxic to aquatic life by reducing oxygen availability and altering pH levels. (mg/L)",
    "BOD5": "🔹Biochemical Oxygen Demand (BOD5) measures the amount of oxygen required by microorganisms to break down organic matter in water. High BOD5 levels indicate pollution from sewage, agricultural runoff, and industrial waste, leading to oxygen depletion and harm to aquatic ecosystems. (mg/L)",
    "Cadmium and its compounds": "🔹A toxic heavy metal released from mining, industrial processes, and fertilizers. Even in small amounts, cadmium bioaccumulates in aquatic organisms, posing severe risks to human health, including kidney damage and cancer.(µg/L)",
    "Mercury and its compounds": "🔹A dangerous pollutant released from industrial processes, mining, and coal combustion. Mercury bioaccumulates in fish and seafood, posing severe health risks to humans, including neurological damage and developmental issues in children. Its persistence in ecosystems makes it a long-term threat. (µg/L)",
    "Nickel and its compounds": "🔹A metal found in water due to industrial discharges, mining, and atmospheric deposition. High nickel levels can be toxic to aquatic life and pose risks to human health, including allergic reactions and organ damage. (µg/L)",
    "Lead and its compounds": "🔹A highly toxic heavy metal that accumulates in the human body, causing neurological disorders, especially in children. It primarily originates from old plumbing systems and industrial pollution. Even at low concentrations, lead exposure is harmful, making its presence in water a serious health concern. (µg/L)",
}


dash.register_page(__name__, path="/water_composition_europe", title="Water Composition in Europe") # Page name for app.py

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
JSON_DIR = os.path.join(BASE_DIR, "json")

# Load the JSON file
json_file_composition = os.path.join(JSON_DIR, "EEA_JSON", "water_composition_europe.json")

if os.path.exists(json_file_composition):
    df_grouped = pd.read_json(json_file_composition)
else:
    df_grouped = pd.DataFrame(columns=["countryCode", "observedPropertyDeterminandLabel", "resultMeanValue", "resultUom"])

# Extract unique determinands
available_determinands = df_grouped[
    "observedPropertyDeterminandLabel"].unique().tolist() if not df_grouped.empty else []


def iso3_to_country(iso3):
    """Convert ISO3 country code to country name."""
    try:
        if iso3 == 'XKX': # Kosovo's ISO3 code is not in pycountry
            return 'Kosovo'
        country = pycountry.countries.get(alpha_3=iso3)
        return country.name if country else iso3
    except AttributeError:
        return iso3


def layout():
    return html.Div([
        html.H2("🇪🇺 Water Composition Across Europe", style={
        'textAlign': 'center',
        'color': '#ffffff',
        'fontSize': '32px',
        'fontWeight': 'bold',
        'textShadow': '2px 2px 4px #000',
        'fontFamily': 'Arial, sans-serif',
        'backgroundImage': 'url("/assets/water.jpeg")',
        'backgroundSize': 'cover',
        'backgroundPosition': 'center',
        'backgroundRepeat': 'no-repeat',
        'padding': '20px',
    }),

    html.Div([
        html.Label("Select Pollutant:", className="label-style",
               style={
                   'font-size': '16px',
                   'font-weight': 'bold',
                   'margin-right': '10px',
                   'white-space': 'nowrap'
               }),

    dcc.Dropdown(
        id="determinand-selector",
        options=[{"label": det, "value": det} for det in available_determinands if det in filtered_pollutants],
        value=filtered_pollutants[0] if filtered_pollutants else None,
        clearable=False,
        className="custom-dropdown",
        style={
            'width': '100%',
            'min-width': '200px',
            'flex-grow': '1'
        }
    )
], style={
    'display': 'flex',
    'align-items': 'center',
    'gap': '10px',
    'width': '30%',
    'padding': '10px',
    'border-radius': '8px',
    'background-color': '#b3caf5',
    'box-shadow': '2px 2px 10px rgba(0,0,0,0.1)'
}),
        # Indicator Description Section
        html.Div(id="pollutant-description", className="description-box", style={
            'marginBottom': '20px',
            'fontSize': '16px',
            'padding': '10px'
        }),

        dcc.Checklist(
            id="log-toggle",
            options=[{"label": "Log Scale", "value": "log"}],
            value=["log"],
            inline=True,
            className='custom-log-toggle',
        ),

        dcc.Checklist(
            id="compare-checklist",
            options=[{"label": "Compare with EU Water Framework Directive Thresholds", "value": "compare"}],
            value=[],
            inline=True,
            className='custom-log-toggle',
        ),


        dcc.Graph(id="map-europe-water-composition", style={'height': '70vh'}),

        html.Hr(style={
        'border': '3px solid black',
        'margin': '50px auto'
        }),


        html.H3("Top European Countries with the Highest Concentrations",
        style={
            'textAlign': 'center',
            'font-size': '24px',
            'font-weight': 'bold',
            'margin-top': '20px',
            'margin-bottom': '15px',
        }),
        dcc.Slider(
            id="top-n-slider",
            min=3,
            max=20,
            step=1,
            value=10,
            marks={i: str(i) for i in range(3, 21, 1)},
            tooltip={"placement": "bottom", "always_visible": True},
            className="custom-slider"
        ),

        dcc.Graph(id="top-n-bar-chart", style={'height': '50vh'})
    ])

@callback(
    Output("pollutant-description", "children"),
    Input("determinand-selector", "value")
)
def update_description(selected_variable):
    """Update the description of the selected pollutant."""
    if selected_variable in POLLUTANT_DESCRIPTIONS:
        return POLLUTANT_DESCRIPTIONS[selected_variable]
    return "Select an indicator to see its description."

@callback(
    [Output("map-europe-water-composition", "figure"), Output("top-n-bar-chart", "figure")],
    [Input("determinand-selector", "value"), Input("log-toggle", "value"),
     Input("top-n-slider", "value"), Input("compare-checklist", "value")]
)
def update_graphs(selected_determinand, log_value, top_n, compare_mode):
    """Update the choropleth map and bar chart based on user input."""
    if selected_determinand is None or df_grouped.empty:
        return px.choropleth(), px.bar()

    df_filtered = df_grouped[df_grouped["observedPropertyDeterminandLabel"] == selected_determinand].copy()
    df_filtered = df_filtered[df_filtered["countryCode"] != "XKX"] # Exclude Kosovo because ISO3 code is not in pycountry
    df_filtered.loc[:, "log_resultMeanValue"] = np.log1p(df_filtered["resultMeanValue"])
    df_filtered.loc[:, "countryName"] = df_filtered["countryCode"].apply(iso3_to_country)
    unit = df_filtered["resultUom"].iloc[0] if not df_filtered["resultUom"].isnull().all() else ""

    use_log = "log" in log_value
    color_column = "log_resultMeanValue" if use_log else "resultMeanValue"
    color_label = f"Log Mean Value ({unit})" if use_log else f"Mean Value ({unit})"

    # Set the color scale based on the selected determinand
    if selected_determinand in THRESHOLDS:
        threshold = THRESHOLDS[selected_determinand]
    else :
        threshold = None

    threshold_text = f" (Threshold: {threshold:.2f})" if threshold is not None and "compare" in compare_mode else ""
    title_text = (
    f"Legal {selected_determinand} Concentration Across Europe ({unit}){threshold_text}"
    if "compare" in compare_mode
    else f"{selected_determinand} Concentration Across Europe ({unit})"
)

    if "compare" in compare_mode and selected_determinand in THRESHOLDS:
        threshold = THRESHOLDS[selected_determinand]
        df_filtered["Compliance with Legal Threshold"] = df_filtered["resultMeanValue"].apply(
            lambda x: "Within Legal Limit" if x <= threshold else "Exceeds Legal Limit")
                # Hack : ajouter une ligne fictive si tous les pays sont dans la même catégorie
        if df_filtered["Compliance with Legal Threshold"].nunique() == 1:
            dummy_row = pd.DataFrame([{
                "countryCode": "ZZZ",  # pays inexistant
                "Compliance with Legal Threshold": "Exceeds Legal Limit"
            }])
            df_filtered = pd.concat([df_filtered, dummy_row], ignore_index=True)
        fig_map = px.choropleth(df_filtered,
                                locations="countryCode",
                                locationmode="ISO-3",
                                color="Compliance with Legal Threshold",
                                color_discrete_map={"Within Legal Limit": "green", "Exceeds Legal Limit": "red"},
                                title=title_text,
                                hover_name="countryName")

    else:
        fig_map = px.choropleth(df_filtered,
                                locations="countryCode",
                                locationmode="ISO-3",
                                color=color_column,
                                color_continuous_scale="Plasma",
                                range_color=[df_filtered[color_column].min(), df_filtered[color_column].max()],
                                title=title_text,
                                labels={color_column: color_label},
                                hover_name="countryName")

    fig_map.update_geos(
        projection_type="natural earth",
        showcoastlines=True,
        coastlinecolor="black",
        showland=True,
        landcolor="white",
        showframe=False,
        center={"lat": 55, "lon": 10},
        projection_scale=4,
        fitbounds=False,
        bgcolor="#b3caf5"
    )

    fig_map.update_layout(
        title={'text': title_text, 'x': 0.5, 'y': 0.98, 'xanchor': 'center', 'yanchor': 'top'},
        paper_bgcolor="#b3caf5",
        plot_bgcolor="#b3caf5",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    df_top_n = df_filtered.nlargest(top_n, "resultMeanValue").sort_values(by="resultMeanValue", ascending=True)

    # Creation of the top n bar chart
    fig_bar = px.bar(df_top_n,
                     x="countryName",
                     y=color_column,
                     title=f"Top {top_n} Most Polluted Countries for {selected_determinand}",
                     labels={color_column: color_label, "countryName": "Country"},
                     color=color_column,
                     color_continuous_scale="Plasma")

    # Add threshold line if compare mode is active and threshold exists to the top n bar chart
    if "compare" in compare_mode and selected_determinand in THRESHOLDS:
        threshold_value = THRESHOLDS[selected_determinand]
        threshold_display_value = threshold_value

        if use_log:
            threshold_value = np.log1p(threshold_value)
            threshold_display_value = threshold_value

        fig_bar.add_shape(
            type="line",
            x0=-0.5,
            x1=len(df_top_n["countryName"]) - 0.5,
            y0=threshold_value,
            y1=threshold_value,
            line=dict(color="black", width=2, dash="dash"),
        )

        fig_bar.add_annotation(
            xref="paper",
            x=1.0,
            y=threshold_value,
            text=f"Threshold: {threshold_display_value:.3f} {unit}" + (" (log scale)" if use_log else ""),
            showarrow=False,
            yanchor="bottom",
            bgcolor="white",
            font=dict(color="black", size=12)
        )

    fig_bar.update_layout(
        paper_bgcolor="#b3caf5",
        plot_bgcolor="#b3caf5",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    return fig_map, fig_bar
