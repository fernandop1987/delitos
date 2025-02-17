# Cargo las librerías necesarias
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc


############################################################################################################


#### Cargar los datos procesados
df_dep = pd.read_csv("data/df_dep.csv")
df_barrios = pd.read_csv("data/df_barrios.csv")
gdf_dep = gpd.read_file("data/gdf_dep.geojson")
gdf_mvd = gpd.read_file("data/gdf_mvd.geojson")


############################################################################################################



app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


# Crear las opciones del dropdown a partir de los valores únicos de 'Delito'
delitos_options = [{'label': delito, 'value': delito} for delito in pd.concat([df_dep['Delito'], df_barrios['Delito']]).unique()]


#mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"
#mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"


app.layout = dbc.Container([
    # Título y descripción
    dbc.Row([
        dbc.Col(html.H1("Monitor de Delitos en Uruguay",
                        style={'textAlign': 'center', 'font-family': 'Montserrat, sans-serif', 
                               'fontSize': '32px', 'fontWeight': 'bold', 'margin-bottom': '20px'}), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.P("Ratio de delitos por cada 100.000 habitantes según año, tipo de delito y ubicación geográfica (departamentos o barrios de Montevideo).",
                       style={'textAlign': 'center', 'font-family': 'Montserrat, sans-serif', 
                              'fontSize': '16px', 'margin-bottom': '20px'}), width=12)
    ]),

    # Selectores de año y tipo de delito
    dbc.Row([
        dbc.Col([
            html.Label("Selecciona el año:", style={'fontWeight': 'bold'}),
            dcc.Slider(id='slider_year',
                       min=df_dep['Año'].min(), max=df_dep['Año'].max(), step=1,
                       marks={year: str(year) for year in range(df_dep['Año'].min(), df_dep['Año'].max() + 1)},
                       value=df_dep['Año'].max())
        ], xs=12, sm=12, md=6, lg=6),  # Ocupa 12 columnas en xs y sm (mobile), 6 en dispositivos más grandes
        dbc.Col([
            html.Label("Selecciona el tipo de delito:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(id='dropdown_delito',
                         options=delitos_options,
                         value='RAPIÑA',  # Valor por defecto
                         placeholder="Selecciona un tipo de delito",
                         style={
                             'color': '#0F0F0F',  
                             'font-family': 'Montserrat, sans-serif'
                         }
            )
        ], xs=12, sm=12, md=6, lg=6)  # Mismo comportamiento
    ], className="mb-4"),



    # Botones para cambiar entre mapas
    dbc.Row([
        dbc.Col(dbc.ButtonGroup([
            dbc.Button("Uruguay", id='btn_uruguay', n_clicks=0,
                       style={'background-color': '#1E2A38',  # Fondo azul profundo
                          'border': '2px solid #DBD1D8',  # Borde turquesa
                          'color': '#DBD1D8',  # Texto gris claro
                          'font-family': 'Montserrat, sans-serif',
                          'font-weight': 'bold',
                          'padding': '8px 16px',
                          'border-radius': '6px',
                          'margin-right': '10px'}),
            dbc.Button("Montevideo", id='btn_montevideo', n_clicks=0,
                          style={'background-color': '#1E2A38',  # Fondo azul profundo
                              'border': '2px solid #DBD1D8',  # Borde turquesa
                              'color': '#DBD1D8',  # Texto gris claro
                              'font-family': 'Montserrat, sans-serif',
                              'font-weight': 'bold',
                              'padding': '8px 16px',
                              'border-radius': '6px'})
        ]), width=12, className="mb-4")
    ]),

    # Visualizaciones: mapa y gráfico de barras en la misma fila
    dbc.Row([
        dbc.Col(dcc.Graph(id='map_graph', style={'height': '500px'}, config={'scrollZoom':True}), width=12, lg=8, className="mb-3"),  # Mapa ocupa 8/12 del ancho en pantallas grandes
        dbc.Col(html.Div([
            dcc.Graph(id='bar_graph')  
        ], style={'height': '500px', 'overflowY': 'scroll'}), width=12, lg=4)  
    ], className="mb-5"),
    
    # Delitos sin clasificar  
    dbc.Row([
        dbc.Col(html.Div(id='dynamic_text', style={'textAlign': 'left', 'fontSize': '14px', 'margin-bottom': '15px'}), width=12)
    ]),
    
    # Espacio para texto explicativo
    dbc.Row([
        dbc.Col(html.P([
            "1. Se compara la cantidad de delitos por cada 100.000 habitantes según año, tipo de delito y zona geográfica.", html.Br(),
            "2. Datos generados a partir de los delitos registrados y reportados por el ministerio del interior, no se tienen en cuenta estimaciones de delitos no denunciados.", html.Br(),
            "3. Para el tipo de delito 'Homicidios' no existen registros específicos a nivel de barrios de Montevideo.", html.Br(),
            "Fuentes de datos: Ministerio del Interior, Instituto Nacional de Estadística (INE)."
        ], style={'textAlign': 'left', 'fontSize': '14px', 'fontStyle': 'italic', 'margin-bottom': '15px'}), width=12)
    ], className="mb-3")
   
    
], fluid=True, style={'backgroundColor': '#131A22', 'padding': '20px', 'color': '#DBD1D8'})


# Callback ajustado para relacionar GeoJSON y dataframes correctamente
@app.callback(
    [Output('map_graph', 'figure'),
     Output('bar_graph', 'figure'),
     Output('dynamic_text', 'children')],  # Nueva salida para el texto dinámico
    [Input('slider_year', 'value'),
     Input('dropdown_delito', 'value'),
     Input('btn_uruguay', 'n_clicks'),
     Input('btn_montevideo', 'n_clicks')]
)
def update_visuals(selected_year, selected_delito, n_clicks_uruguay, n_clicks_montevideo):
    if n_clicks_montevideo > n_clicks_uruguay:
        filtered_df = df_barrios[(df_barrios['Año'] == selected_year) & (df_barrios['Delito'] == selected_delito)].sort_values(by='Ratio', ascending=True)
        filtered_df = filtered_df[filtered_df['Barrio'] != 'SIN CLASIFICAR']  # Excluir "SIN CLASIFICAR"
        geojson = gdf_mvd
        location_field = 'id_barrio'
        feature_key = 'properties.id_barrio'
        
        # Calcular el número de delitos en "SIN CLASIFICAR"
        sin_clasificar_count = df_barrios[(df_barrios['Año'] == selected_year) & 
                                          (df_barrios['Delito'] == selected_delito) & 
                                          (df_barrios['Barrio'] == 'SIN CLASIFICAR')]['Total delitos'].sum()
        final_text = f"Hubo además {sin_clasificar_count} delitos denunciados en barrios sin clasificar."
        
        
    else:
        filtered_df = df_dep[(df_dep['Año'] == selected_year) & (df_dep['Delito'] == selected_delito)].sort_values(by='Ratio', ascending=True)
        filtered_df = filtered_df[filtered_df['Departamento'] != 'Centros Carcelarios']  # Excluir "Centros Carcelarios"
        geojson = gdf_dep
        location_field = 'id_dep'
        feature_key = 'properties.id_dep'
        
        # Calcular el número de delitos en "Centros Carcelarios"
        if selected_delito == 'HOMICIDIO':
            centros_count = df_dep[(df_dep['Año'] == selected_year) & 
                                   (df_dep['Delito'] == 'HOMICIDIO') & 
                                   (df_dep['Departamento'] == 'Centros Carcelarios')]['Total delitos'].sum()
            final_text = f"Los centros carcelarios registraron {centros_count} homicidios."
        else:
            final_text = ""
        
    # Obtener el valor mínimo y máximo del Ratio para el tipo de delito seleccionado
    if n_clicks_montevideo > n_clicks_uruguay:
        ratio_min = df_barrios[df_barrios['Delito'] == selected_delito]['Ratio'].min()
        ratio_max = df_barrios[df_barrios['Delito'] == selected_delito]['Ratio'].max()
    else:
        ratio_min = df_dep[df_dep['Delito'] == selected_delito]['Ratio'].min()
        ratio_max = df_dep[df_dep['Delito'] == selected_delito]['Ratio'].max()



    # Crear el mapa con el GeoJSON vinculado correctamente
    map_fig = px.choropleth_mapbox(
        filtered_df,
        geojson=geojson,
        locations=location_field,
        featureidkey=feature_key,
        color='Ratio',
        color_continuous_scale=[
        [0, "#F2D261"],
        [0.25, "#FAAF18"],    
        [0.5, "#FF4816"],
        [0.75, "#CC2A26"], 
        [1, "#752D39"]  
        ],
        hover_name='Departamento' if location_field == 'id_dep' else 'Barrio',
        labels={'Ratio': 'Delitos cada 100K hab'},
        opacity=0.8
    )

    # Configuración de los tooltips
    map_fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "<b>Total delitos:</b> %{customdata[0]:,}<br>"  
            "<b>Delitos cada 100K hab:</b> %{customdata[1]:,.1f}<extra></extra>"
        ),
        customdata=filtered_df[['Total delitos', 'Ratio']].values 
    )


    # Configuración del layout del mapa
    map_fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",  
            center={"lat": -32.52, "lon": -55.77} if location_field == 'id_dep' else {"lat": -34.82, "lon": -56.2},  # Centro dinámico
            zoom=5.5 if location_field == 'id_dep' else 9.5  # Zoom dinámico
        ),
        paper_bgcolor="#1E2A38",
        plot_bgcolor="#1E2A38",
        coloraxis_cmin=ratio_min,  # Valor mínimo fijo
        coloraxis_cmax=ratio_max,   # Valor máximo fijo
        coloraxis_colorbar=dict(
            title=dict(text="Delitos<br>cada 100K/hab.", font=dict(family="Montserrat, sans-serif", size=14, color="#DBD1D8")),
            tickformat=",.0f",  # Formato de los ticks
            tickfont=dict(family="Montserrat, sans-serif", size=12, color="#DBD1D8"),
            thickness=10,  # Más angosta
            orientation='h',  # Barra horizontal
            x=0.50,  # Ajusta la posición horizontal (0 = izquierda, 1 = derecha)
            y=-0.15  # Ajusta la posición vertical (valores negativos mueven la barra hacia abajo)
        ),
        margin=dict(l=20, r=20, t=40, b=40),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Montserrat, sans-serif"
        )
    )

    
    
    # Gráfico de barras vertical 
    bar_fig = px.bar(
        filtered_df.sort_values(by='Ratio', ascending=True),
        x='Ratio',
        y='Departamento' if location_field == 'id_dep' else 'Barrio',
        orientation='h',
        color='Ratio',
        color_continuous_scale=[
        [0, "#F2D261"],
        [0.25, "#FAAF18"],    
        [0.5, "#FF4816"],
        [0.75, "#CC2A26"], 
        [1, "#752D39"] 
        ],
        text='Ratio'  # Mostrar los valores directamente en las barras  
    )
    bar_fig.update_traces(
        texttemplate='%{text:,.1f}',  # Separación de miles y un decimal
        hovertemplate=(
            "<b>Total delitos:</b> %{customdata[0]:,}<br>"  
            "<b>Delitos cada 100K hab:</b> %{x:,.1f}<extra></extra>"
        ),
        customdata=filtered_df[['Total delitos', 'Ratio']].values, 
        textfont=dict(family="Montserrat, sans-serif") 
    )
    
    num_categories = len(filtered_df['Departamento' if location_field == 'id_dep' else 'Barrio'].unique())
    height = max(40 * num_categories, 200)  # Altura mínima de 200px

    bar_fig.update_layout(
        showlegend=False,  # Quitar la leyenda
        coloraxis_showscale=False,  # Quitar la barra de colores
        coloraxis_cmin=ratio_min,
        coloraxis_cmax=ratio_max,
        title=dict(text= "Delitos cada 100K/hab.", x= 0.5,font=dict(family="Montserrat, sans-serif", size=14, color="#DBD1D8") 
        ),
        margin=dict(l=20, r=20, t=80, b=40),
        height=height,
        paper_bgcolor="#1E2A38",
        plot_bgcolor="#1E2A38",
        xaxis=dict(showgrid=False, showticklabels=False),  # Quitar etiquetas del eje X
        yaxis=dict(showgrid=False, showticklabels=True, tickfont=dict(family="Montserrat, sans-serif", size=10, color="#DBD1D8")),
        xaxis_title="",
        yaxis_title="",
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Montserrat, sans-serif")
    )
    
    
    return map_fig, bar_fig, final_text


# Render necesita esto
server = app.server  # ← ¡IMPORTANTE!

if __name__ == '__main__':
    app.run_server(debug=True)