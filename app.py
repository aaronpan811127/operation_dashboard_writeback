import os
import dash
from dash import dcc, html, Input, Output, State, callback_context
from dash import dash_table
import dash_bootstrap_components as dbc
from urllib.parse import urlparse, parse_qs
from datetime import date,datetime
from utils import combine_datetime
from models import get_incident_data, write_incident
import pandas as pd

# Ensure environment variable is set correctly
assert os.getenv('DATABRICKS_WAREHOUSE_ID'), "DATABRICKS_WAREHOUSE_ID must be set in app.yaml."
assert os.getenv('SERVICENOW_URL'), "SERVICENOW_URL must be set in app.yaml."
DATABRICKS_WAREHOUSE_ID = os.getenv('DATABRICKS_WAREHOUSE_ID')
SERVICENOW_URL = os.getenv('SERVICENOW_URL')

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),   
    # Modal for incident details
    dbc.Modal(
        [
            dbc.ModalHeader("Please assign incident to the following job execution",close_button=False),
            dbc.ModalBody([
                html.Label("Valid pipeline_id and execution_id must be provided as url parameters",id="warning",style={'color': 'red'},hidden=True),               
                html.Label("Pipeline ID"),
                dcc.Input(id="pipeline_id", type="text", disabled=True),
                html.Label("Pipeline Name"),
                dcc.Input(id="pipeline_name", type="text", disabled=True),
                html.Label("Execution ID"),
                dcc.Input(id="execution_id", type="text", disabled=True),                                                                             
                html.Label("Incident ID"),
                dcc.Input(id="incident_id", type="text"),
                html.A(id="incident_link",target="_blank",style={'word-wrap': 'break-word'}),                   
                html.Label("Assigned To"),
                dcc.Input(id="assigned_to", type="text"),
                html.Label("Incident Status"),                
                dbc.Select(['Open', 'Closed'], 'Open', id="incident_status"),                 
                html.Label("Comments"),
                dcc.Textarea(id="incident_comments", style={"width": "100%"}),             
                html.Label("Assigned Timestamp"),
                html.Div([                 
                    dcc.DatePickerSingle(
                        id="assigned_date",
                        display_format="DD/MM/YYYY",  # Australian date format
                        style={"width": "70%"}  # Ensure the picker is wide enough
                    ),
                    dcc.Input(
                        id="assigned_time", 
                        type="text", 
                        placeholder="HH:MM:SS", 
                        value="00:00:00",
                        style={"width": "30%", "margin-left": "10px"}
                    )
                ], style={"display": "flex", "align-items": "center"}),
            ], className="modal-body"),
            dbc.ModalFooter([
                # Loading status spinner           
                dcc.Loading(
                    id="loading-output",
                    children=[html.Div(id="loading-incident")],
                    type="default",
                    fullscreen=False,
                ),                 
                # Loading status spinner           
                dcc.Loading(
                    id="loading-save-incident",
                    children=[html.Div(id="saving-incident")],
                    type="default",
                    fullscreen=False,
                ),
                dbc.Button("Save", id="save_button", color="primary")
            ])
        ],
        id="incident_modal",
        is_open=True,
        backdrop="static",
        keyboard=False
    )  
    ]
)

@app.callback(
    [Output("warning", "hidden"),
     Output("pipeline_id", "value"),
     Output("pipeline_name", "value"),
     Output("execution_id", "value"),     
     Output("incident_id", "value"),
     Output("incident_status", "value"),       
     Output("incident_comments", "value"),
     Output("assigned_date", "date"),
     Output("assigned_time", "value"),
     Output("assigned_to", "value"),
     Output("incident_link", "href"),
     Output("incident_link", "children"),
     Output("loading-incident", "children")],
    [Input('url', 'search')]
)
def get_incident(search):
    # Process the URL parameters here
    params = parse_qs(search[1:])
    pipeline_id = params.get('pipeline_id', [''])[0]
    execution_id = params.get('execution_id', [''])[0]

    incident_data = get_incident_data(
        pipeline_id=pipeline_id,execution_id=execution_id,warehouse_id=DATABRICKS_WAREHOUSE_ID
    )
    print(incident_data)

    if incident_data.empty:
        return (
            False,
            None,
            None,
            None,
            None,
            None,      
            None,
            None,
            None,
            None,
            None,
            None,
            None
        )

    row = incident_data.iloc[0]
    assigned_date = row["assigned_timestamp"].date() if pd.notna(row["assigned_timestamp"]) else date.today()
    current_time = datetime.now().strftime("%H:%M:%S")
    assigned_time = row["assigned_timestamp"].time() if pd.notna(row["assigned_timestamp"]) else current_time

    return (
        True,
        row["pipeline_id"],
        row["pipeline_name"],
        row["execution_id"],
        row["incident_id"],
        row["incident_status"] if row["incident_status"] is not None else 'Open',      
        row["incident_comments"],
        assigned_date,
        assigned_time,
        row["assigned_to"],
        SERVICENOW_URL+row["incident_id"] if row["incident_id"] is not None else None,
        'Incident URL' if row["incident_id"] is not None else None,                
        None
    )

@app.callback(
    [Output("incident_modal", "is_open"),
     Output("incident_link", "href",allow_duplicate=True),
     Output("incident_link", "children",allow_duplicate=True),
     Output("saving-incident", "children")],
    [Input("save_button", "n_clicks")],
    [State("pipeline_id", "value"),
     State("incident_id", "value"),
     State("incident_status", "value"),       
     State("incident_comments", "value"),
     State("assigned_to", "value"),
     State("assigned_date", "date"),
     State("assigned_time", "value"),
     State("execution_id", "value")],
    prevent_initial_call=True
)
def save_incident_data(save_clicks, pipeline_id, incident_id, incident_status, incident_comments, assigned_to, assigned_date, assigned_time,
                       execution_id): 
    if save_clicks and pipeline_id:
        assigned_timestamp = combine_datetime(assigned_date, assigned_time)
        data = []

        row = (
            pipeline_id,
            execution_id,
            incident_id if incident_id is not None else '',
            incident_status if incident_status is not None else 'Open',            
            incident_comments if incident_comments is not None else '',
            assigned_to if assigned_to is not None else '',
            str(assigned_timestamp) if assigned_timestamp is not None else ''
        )
        data.append(row)
        columns = "pipeline_id,execution_id,incident_id,incident_status,incident_comments,assigned_to,assigned_timestamp"
        write_incident(data=data,columns=columns,warehouse_id=DATABRICKS_WAREHOUSE_ID)

        incident_link = SERVICENOW_URL+incident_id if incident_id is not None else None

        return (True,incident_link,'Incident URL',html.H6("Data saved successfully!"))

if __name__ == "__main__":
    app.run(debug=False)