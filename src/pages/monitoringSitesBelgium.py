import dash
from dash import html, dcc, callback, Output, Input, State, no_update
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import json
import os

dash.register_page(__name__, path="/", title="Monitoring Sites Belgium")  # Page name for app.py

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))  
JSON_DIR = os.path.join(BASE_DIR, "json")
EEAR_DIR = os.path.join(JSON_DIR, "EEA_JSON")

def load_json(file_path):
    """Load JSON file and return as DataFrame"""
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.DataFrame(data)
    else:
        print(f"Warning: {file_path} not found or empty. Using fallback DataFrame.")
        return pd.DataFrame()

df = load_json(os.path.join(JSON_DIR, "EEA_JSON", "belgium_composition.json"))
df_composition = load_json(os.path.join(JSON_DIR, "EEA_JSON", "BEandEU_water_composition.json"))
df_bathing_wei = load_json(os.path.join(EEAR_DIR, "BathingWaterQuality_BE_EU.json"))
df_waterEI_wei = load_json(os.path.join(EEAR_DIR, "WaterExploitationIndex_BE_EU.json"))


if not df.empty and all(col in df.columns for col in ["lat", "lon", "monitoringSiteName"]):
    fig_map = px.scatter_map(
        df,
        lat="lat",
        lon="lon",
        hover_name="monitoringSiteName",
        custom_data=["monitoringSiteName", "waterBodyName", "observedData"],
        zoom=7,
        map_style="light")
    fig_map.update_traces(marker=dict(size=10))
    fig_map.update_layout(
        paper_bgcolor="#b3caf5",
        plot_bgcolor="#b3caf5",
        clickmode="event+select",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )
else:
    fig_map = px.scatter_map(title="No data available.")

# Graphe of the chemical composition of water in Belgium and Europe
if not df_composition.empty:
    df_composition_melted = df_composition.melt(
        id_vars=["observedPropertyDeterminandLabel"],
        value_vars=["avgResultMeanValue_2010_2023", "eu_averageMeanValue"],
        var_name="Region",
        value_name="Concentration"
    )
    df_composition_melted["Region"] = df_composition_melted["Region"].replace({
    "avgResultMeanValue_2010_2023": "Belgium (2010-2023)",
    "eu_averageMeanValue": "EU Average (2010-2023)"
})

    fig_graphBEandEU = px.bar(
        df_composition_melted,
        x="observedPropertyDeterminandLabel",
        y="Concentration",
        color="Region",
        barmode="group",
        title="Chimical composition of water in Belgium and Europe ",
        labels={"observedPropertyDeterminandLabel": "Chimical compound", "Concentration": "Mean concentration", "Region": "Country"},
    )
    fig_graphBEandEU.update_layout(
        paper_bgcolor="#b3caf5",
        plot_bgcolor="#b3caf5"
    )
    fig_graphBEandEU.update_yaxes(type="log", title="Mean concentration (log scale)")

else:
    fig_graphBEandEU = px.bar(title="Aucune donnée disponible pour la composition de l'eau.")


# Graphic on the evolution of bathing water quality and water exploitation index
if not df_bathing_wei.empty:
    fig_graphBathin_WE = px.line(
        df_bathing_wei,
        x="time",
        y="obs_value",
        line_dash="geo_label",
        title="Evolution of bathing water quality and water exploitation index",
        labels={"obs_value": "Observed value", "time": "Year", "geo_label": "Country"},
    )
    fig_graphBathin_WE.update_layout(
        paper_bgcolor="#b3caf5",
        plot_bgcolor="#b3caf5"
    )
else:
    fig_graphBathin_WE = px.line(title="Aucune donnée disponible pour l'évolution de la qualité de l'eau.")

# Final layout of the page
layout = html.Div([
    html.H2("🇧🇪 Monitoring Sites In Belgium", style={
        'textAlign': 'center', 'color': '#ffffff', 'textShadow': '2px 2px 4px #000',
        'fontSize': '32px', 'fontWeight': 'bold', 'padding': '20px 0',
        'backgroundImage': 'url(\"/assets/water.jpeg\")', 'backgroundSize': 'cover',
        'backgroundPosition': 'center', 'backgroundRepeat': 'no-repeat'
    }),

    html.H3("📍 Map of the monitoring sites where the data has been collected", style={
        'textAlign': 'center', 'color': '#091540', 'fontSize': '28px',
        'fontWeight': 'bold', 'marginTop': '30px', 'textShadow': '1px 1px 3px rgba(0,0,0,0.2)',
    }),

    html.Div([
        dcc.Graph(id="map", figure=fig_map, style={'height': '90vh', 'width': '90%'}, config={"scrollZoom": True})
    ], style={'display': 'flex', 'justifyContent': 'center', 'width': '100%'}),

    html.Hr(style={'border': '2px solid #091540', 'width': '80%', 'margin': '40px auto'}),

    html.H3("📊 Analysis of Water Quality and It's Compounds in Belgium", style={
        'textAlign': 'center', 'color': '#091540', 'fontSize': '28px',
        'fontWeight': 'bold', 'marginTop': '5px', 'marginBottom': '30px', 'textShadow': '1px 1px 3px rgba(0,0,0,0.2)',
    }),

    html.H3("🧪 Chemical composition of water in Belgium and Europe", style={
        'textAlign': 'center', 'color': '#091540', 'fontSize': '24px', 'fontWeight': 'bold',
    }),
    html.Div([
        dcc.Graph(id="composition-graph", figure=fig_graphBEandEU, style={'height': '70vh', 'width': '90%'})
    ], style={'display': 'flex', 'justifyContent': 'center', 'width': '100%'}),

    html.Hr(style={'border': '2px solid #091540', 'width': '80%', 'margin': '40px auto'}),
    
    html.H3("📊 Bathing water quality and Water Exploitation Index", style={
        'textAlign': 'center', 'color': '#091540', 'fontSize': '24px', 'fontWeight': 'bold',
    }),
    html.Div([
        dcc.Dropdown(
            id="bathing-wei-dropdown",
            options=[
                {"label": "Bathing Water Quality", "value": "bathing"},
                {"label": "Water Exploitation Index", "value": "wei"},
            ],
            value="bathing",
            clearable=False,
            style={'width': '50%', 'margin': 'auto'}
        )
    ], style={'marginBottom': '20px'}),


    html.Div(id="bathing-type-container", style={'textAlign': 'center', 'marginTop': '20px'}),
    
    html.Div([
        dcc.Graph(id="bathing-wei-graph", figure=fig_graphBathin_WE, style={'height': '70vh', 'width': '90%'})
    ], style={'display': 'flex', 'justifyContent': 'center', 'width': '100%'}),
    
    html.Div(id="wei-description", style={
    'textAlign': 'justify', 'width': '80%', 'margin': '30px auto',
    'backgroundColor': '#f2f2f2', 'padding': '20px', 'borderRadius': '10px',
    'boxShadow': '2px 2px 5px rgba(0,0,0,0.1)', 'color': '#091540'
    }),


    dcc.Store(id="stored-click-data", data=None),
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody(id="modal-body"),
        dbc.ModalFooter(dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0))
    ], id="data-modal", is_open=False),
])

@callback(
    Output("data-modal", "is_open"),
    Output("modal-title", "children"),
    Output("modal-body", "children"),
    Input("map", "clickData"),
    Input("close-modal", "n_clicks"),
    State("data-modal", "is_open"),
)

def update_modal(clickData, close_clicks, is_open):
    """Update the modal with information about the clicked monitoring site."""
    if close_clicks and is_open:
        return False, None, None

    if clickData and "points" in clickData:
        site_info = clickData["points"][0]["customdata"]
        site_name, water_body, observed_data = site_info

        if not observed_data or len(observed_data) == 0:
            modal_body = html.Div([
                html.P(f"📍 Monitoring Site: {site_name}"),
                html.P(f"🌊 Water Body: {water_body}"),
                html.P("🚫 No observed data available for this site."),
            ])
        else:
            modal_body = html.Div([
                html.P(f"📍 Monitoring Site: {site_name}"),
                html.P(f"🌊 Water Body: {water_body}"),
                html.Hr(),
                html.P("🧪 Observed Properties:"),
                html.Ul([html.Li(f"{entry['observedPropertyDeterminandLabel']}: {entry['averageObservedValue']}: {entry.get('resultUom', '')}") for entry in observed_data]),
            ])

        return True, f"Details for {site_name}", modal_body

    return is_open, None, None


@callback(
    Output("bathing-wei-graph", "figure"),
    Input("bathing-wei-dropdown", "value"),
    Input("bathing-type-selector", "value"),
    prevent_initial_call=True,
)
def update_bathing_wei_graph(selected_option, bathing_type):
    if selected_option == "bathing":
       # If the bathing type is not selected, return no_update (or if the user goes to quick)
        if bathing_type is None:
            return no_update

        if df_bathing_wei.empty:
            return px.line(title="No data available.")

        df_selected = df_bathing_wei[df_bathing_wei["dimension"] == bathing_type]
        title = "Evolution of Bathing Water Quality"

    else:
        df_selected = df_waterEI_wei
        title = "Evolution of Water Exploitation Index"

    if df_selected.empty:
        return px.line(title="No data available.")

    fig = px.line(
        df_selected,
        x="time",
        y="obs_value",
        color="geo_label",
        title=title,
        labels={"obs_value": "Observed value", "time": "Year", "geo_label": "Country"},
    )
    fig.update_layout(
        paper_bgcolor="#b3caf5",
        plot_bgcolor="#b3caf5"
    )
    return fig


@callback(
    Output("bathing-type-container", "children"),
    Input("bathing-wei-dropdown", "value"),
)
def show_bathing_type_selector(selected_option):
    """Show the radio buttons for Coastal/Inland only if "Bathing Water Quality" is selected."""
    if selected_option == "bathing":
        return dcc.RadioItems(
            id="bathing-type-selector",
            options=[
                {"label": "Coastal", "value": "CST_EXC"},
                {"label": "Inland", "value": "INL_EXC"},
            ],
            value="CST_EXC",
            labelStyle={"display": "inline-block", "marginRight": "10px"},
        )
    return ""  # Hide the radio buttons if "Water Exploitation Index" is selected

@callback(
    Output("wei-description", "children"),
    Input("bathing-wei-dropdown", "value")
)
def update_wei_description(selected_option):
    """Update the description based on the selected option."""
    if selected_option == "wei":
        return html.P("""
            As per the EEA : The Water Exploitation Index Plus (WEI+) provides a measure of total water consumption as a percentage 
            of the renewable freshwater resources available for a given territory and period. It quantifies how much 
            water is abstracted and how much water is returned to the environment by economic sectors before or after use. 
            The difference between water abstractions and water returns is regarded as ‘water consumption’. 
            In the absence of Europe-wide agreed formal targets, values above 20% are generally considered to be a sign 
            of water scarcity, while values equal or greater than 40% indicate situations of severe water scarcity, 
            meaning the use of freshwater resources is unsustainable.
        """)
    elif selected_option == "bathing":
        return html.P("""
            As per the EEA : This is the metadata that refers to data showing the number and proportion of coastal and inland bathing waters 
            with excellent quality. The indicator (under development) is based on microbiological parameters 
            (Intestinal enterococci and Escherichia coli). The Bathing Water Directive requires Member States to identify 
            and assess the quality of all inland and marine bathing waters and to classify these waters as ‘poor’, 
            ‘sufficient’, ‘good’ or ‘excellent’.
        """)
