import dash
import dash_bootstrap_components as dbc
import os
from dash import html, dcc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, "pages")

# Initialize Dash
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),

    # Navigation Bar
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dcc.Link("Monitoring Sites Belgium 🇧🇪", href="/", className="nav-link")),
            dbc.NavItem(dcc.Link("Water Composition In Europe 🇪🇺", href="/water_composition_europe", className="nav-link")),
            dbc.NavItem(dcc.Link("Water Exploitation And Bathing Water Quality In Europe 🇪🇺", href="/water_usage_and_bwquality", className="nav-link")),
            dbc.NavItem(dcc.Link("Water Composition Worldwide 🌍", href="/timelapseWaterComposition", className="nav-link")),
            dbc.NavItem(dcc.Link("Water Usage Worldwide 🌍", href="/timelapseWaterUsage", className="nav-link"))
        ],
        brand=html.Img(src='/assets/logo.png', height="40px", style={'filter': 'invert(50%) sepia(100%) saturate(500%) hue-rotate(180deg)'}),
        brand_href="/",
        color="primary",
        dark=True
    ),

    dash.page_container,

    # Footer
    html.Footer([
        html.P("© 2025 AquaData. All rights reserved.", className="copyright"),
        html.P("G1A : DEPAEPE Noé, FLAMENT Franklin, JOSEPHY Thomas, TOM Mikael", className="copyright"),
        html.Hr(style={'border': '0.5px solid lightgray'}),  # Separation line
        html.Div([
            html.P("Data Sources:", className="footer-title"),
            html.P([
                "This project uses data from ",
                html.A("GEMStat", href="https://gemstat.org", target="_blank", className="footer-link"),
                " as well as ",
                html.A("European Environment Agency (EEA)", href="https://www.eea.europa.eu/", target="_blank", className="footer-link"),
                " and ",
                html.A("AQUASTAT", href="https://data.apps.fao.org/aquastat/?lang=en", target="_blank", className="footer-link")
            ], className="footer-text"),
        ], className="footer-info")
    ], className="footer")
])


# Run the server
if __name__ == "__main__":
    app.run(debug=True)
