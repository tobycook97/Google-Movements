import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
from datetime import date
import os
import sys
import webbrowser
from threading import Timer


##### Set TRUE to download fresh data, Set FALSE to use CSV already saved locally (you must have a CSV saved locally)


refresh = False

#Name of csv to look for, or name to save as
name = "Google Movements GB.csv"

# Set dtypes:

# dtype = {'country_region_code':'category',
# 	    'country_region':'string',
#         'sub_region_1':'string',
#         'sub_region_2':'string',
#         'metro_area':'category'
#         'iso_3166_2_code':	census_fips_code	place_id	date	retail_and_recreation_percent_change_from_baseline	grocery_and_pharmacy_percent_change_from_baseline	parks_percent_change_from_baseline	transit_stations_percent_change_from_baseline	workplaces_percent_change_from_baseline	residential_percent_change_from_baseline
# }

if refresh:
    # download data
    df = pd.read_csv("https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv", header=0,parse_dates=[8], low_memory=False)
    df = df[df['country_region_code']=='GB']
    df.to_csv(os.path.join(os.path.dirname(__file__),name),index=False)
else:
    # check for data in the current directory.
    try:
        df = pd.read_csv(os.path.join(os.path.dirname(__file__),name))
        
    except Exception as e:
        print(f'There is an error: {e} check CSV saved to the right file path. Or set refresh = True')
        sys.exit()

# Map regions to one of the four nations. This relies on regions_csv file. CSV should be saved in same folder as code 

region_mapping = pd.read_csv(os.path.join(os.path.dirname(__file__),'regions_csv.csv'))

df.sub_region_1 = df.sub_region_1.fillna('All')

df.sub_region_2 = df.sub_region_2.fillna('All')

# Using regions csv map the regions to the correct nation
df = df.merge(region_mapping,how='left',on=['sub_region_1'])


df.sub_region_1 = df.sub_region_1.fillna('All')
df.sub_region_2 = df.sub_region_2.fillna('All')

# force dates to be datetime
df['date'] = pd.to_datetime(df['date'])

region_options_1 = df["sub_region_1"].unique()
nation_options = df['Nation'].unique()

app = dash.Dash()


app.layout = html.Div([
    html.H2("Google Movement Data by Region"),
    html.Div(
        [
            dcc.Dropdown(
                id="Region_1_dropdown",
                options=[{
                    'label': Region_1,
                    'value': Region_1
                } for Region_1 in region_options_1],
                value='All'),
        ],
        style={'width': '25%',
               'display': 'inline-block'}),
    html.Div(
        [
            dcc.Dropdown(
                id="Region_2_dropdown",
                value='All'
                ),
        ],
        style={'width': '25%',
               'display': 'inline-block'}
               ),
    html.Div(
        [
            daq.BooleanSwitch(
                id="Rolling Average",
                on = True,
                label='7-day Rolling Average',
                labelPosition="right"
                ),
                html.Div(id='Rolling Average on/off')
                
        ],
        style={'width': '25%',
               'display': 'inline-block'}
               ),
            
    dcc.Graph(id='funnel-graph'),
])
@app.callback(
    dash.dependencies.Output('Region_2_dropdown', 'options'),
    [dash.dependencies.Input('Region_1_dropdown', 'value')]
)
def update_dropdown(Region_1):
    return [{'label': Region_2, 'value': Region_2} for Region_2 in df[df['sub_region_1']==Region_1]['sub_region_2'].unique()]

@app.callback(
    dash.dependencies.Output('funnel-graph', 'figure'),
    [dash.dependencies.Input('Region_1_dropdown', 'value'),
    dash.dependencies.Input('Region_2_dropdown', 'value'),
    dash.dependencies.Input('Rolling Average','on')])
def update_graph(Region_1,Region_2,on):
    
    df_plot = df[(df['sub_region_1'] == Region_1)&(df['sub_region_2'] == Region_2)]
    
    columns = ['retail_and_recreation_percent_change_from_baseline', 
    'grocery_and_pharmacy_percent_change_from_baseline', 
    'parks_percent_change_from_baseline', 
    'transit_stations_percent_change_from_baseline',
    'workplaces_percent_change_from_baseline', 
    'residential_percent_change_from_baseline'
    ]

    df_rolling = df_plot.copy()
    if on:
        #do rolling average if checkbox is selected
        
        df_rolling[columns] = df_plot[columns].rolling(window=7).mean()
    
    trace1 = go.Scatter(x=df_rolling.date, y=df_rolling['retail_and_recreation_percent_change_from_baseline'], name='Retail and Recreation')
    trace2 = go.Scatter(x=df_rolling.date, y=df_rolling['grocery_and_pharmacy_percent_change_from_baseline'], name='Grocery and Pharmacy')
    trace3 = go.Scatter(x=df_rolling.date, y=df_rolling['parks_percent_change_from_baseline'], name='Parks')
    trace4 = go.Scatter(x=df_rolling.date, y=df_rolling['transit_stations_percent_change_from_baseline'], name='Transit Stations')
    trace5 = go.Scatter(x=df_rolling.date, y=df_rolling['workplaces_percent_change_from_baseline'], name='Work')
    trace6 = go.Scatter(x=df_rolling.date, y=df_rolling['residential_percent_change_from_baseline'], name='Residential')
    if Region_1 == 'All':
        place = 'United Kingdom'
    else: 
        place = Region_1
    return {
    'data': [trace1, trace2, trace3, trace4,trace5,trace6],
    'layout':
    go.Layout(
        title='Google Movement Data for {}'.format(place))
}

# Open browser and set port:

port = 8050

def open_browser():
    webbrowser.open_new("http://localhost:{}".format(port))

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run_server(debug=False)
