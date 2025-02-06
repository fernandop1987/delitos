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
df_merged2 = pd.read_csv("C:/Users/peton/Monitor_elecciones/data/df_merged2.csv")
df_municipio = pd.read_csv("C:/Users/peton/Monitor_elecciones/data/df_municipio.csv")
df_departamento = pd.read_csv("C:/Users/peton/Monitor_elecciones/data/df_departamento.csv")



############################################################################################################


# Crear la aplicación Dash
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout con Dropdown para partido y botones para cambiar entre niveles
app.layout = dbc.Container([
    # Título Principal
    dbc.Row([
        dbc.Col(html.H1("Monitor de Resultados Electorales en Uruguay", 
                        style={'textAlign': 'center', 'font-family':'Montserrat, sans-serif', 'fontSize': '32px', 'fontWeight': 'bold',
                               'margin-bottom': '20px'}), width=12)
    ]),

    # Subtítulo
    dbc.Row([
        dbc.Col(html.H2("Comparación de los resultados de las elecciones generales de octubre en Uruguay (2024 vs 2019) según partido político y zona geográfica", 
                        style={'textAlign': 'center', 'font-family':'Montserrat, sans-serif', 'fontSize': '16px',
                               'margin-bottom': '20px'}), width=12)
    ]),

    
    
    # Fila para el Dropdown y RadioItems
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='dropdown_partido',
            options=[{'label': partido, 'value': partido} for partido in df_merged2['Lema'].unique()],
            value='Partido Colorado',
            placeholder="Selecciona un partido"
        ), width=12)  # Ocupa toda la fila en mobile
    ], className="mb-3"),  # Margen inferior

    dbc.Row([
        dbc.Col(dcc.RadioItems(
            id='nivel_visualizacion',
            options=[
                {'label': 'Series', 'value': 'series'},
                {'label': 'Municipio', 'value': 'municipio'},
                {'label': 'Departamento', 'value': 'departamento'}
            ],
            value='series',
            inline=True,
            labelStyle={'display': 'inline-block', 'margin-right': '20px'},  # Espaciado entre opciones
            style={'margin-top': '10px'}
        ), width=12)
    ], className="mb-4"),
    
    # Agregamos dcc.Store para almacenar la selección
    dcc.Store(id='selected_data', storage_type='memory'),

    
    dbc.Row([
        dbc.Col(dcc.Graph(id='scatter_plot', style={'height': '550px'}), width=12)  
    ], className="mb-5"),  # Agregar espacio debajo del scatter plot
    
    
    # Espacio para texto explicativo
    dbc.Row([
        dbc.Col(html.P([
            "1. Los puntos se corresponden con el nivel de zona geográfica seleccionado (departamentos, municipios/localidades o series electorales).", html.Br(),
            "2. El tamaño de cada punto está asociado a la cantidad de votos emitidos en las elecciones generales de 2024 dentro de cada nivel de zona geográfica.", html.Br(),
            "3. Las zonas geográficas dentro del área roja son las que tuvieron peor desempeño frente a las elecciones de 2019 según el partido seleccionado,",
            " mientras que aquellas en la zona verde son las que mejoraron con respecto a las elecciones anteriores.", html.Br(),
            "4. No se muestran los puntos correspondientes a series electorales o municipios con menos de 1000 habilitados para votar, pero se incluyen en la agregación de departamentos.", html.Br(), html.Br(),
        html.A("Ver mapa y buscador de series electorales", href="https://tubular-narwhal-fc8def.netlify.app/images/mapa_series.html", target="_blank", style={'color': '#007BFF', 'textDecoration': 'none', 'fontWeight': 'bold'})
        ], style={'textAlign': 'left', 'fontSize': '14px', 'fontStyle': 'italic', 'margin-bottom': '15px'}), width=12)
    ], className="mb-3"),

    # Línea divisoria
    dbc.Row([
        dbc.Col(html.Hr(style={'border-top': '2px solid #ccc'}), width=12)
    ], className="mb-4"),
    
    
    dbc.Row([
        dbc.Col(html.H3(id='titulo_seleccion', style={'textAlign': 'center', 'font-family':'Montserrat, sans-serif', 'fontSize': '18px', 'marginTop': '20px'}), width=12)
    ], className="mb-3"),

    dbc.Row([
        dbc.Col(dcc.Graph(id='bar_chart_share'), width=12, lg=6),  # 100% en mobile, 50% en desktop
        dbc.Col(dcc.Graph(id='bar_chart_variation'), width=12, lg=6)
    ], className="mb-5"),
    
    
    # Fuentes de datos
    dbc.Row([
        dbc.Col(html.P(
            "Fuentes de datos: Corte Electoral del Uruguay.",
        style={'textAlign': 'left', 'fontSize': '14px', 'fontStyle': 'italic', 'margin-bottom': '15px'}), width=12)
    ], className="mb-3")
    
    
], fluid=True, style={'backgroundColor': '#FEF9E5', 'padding': '20px'}), # `fluid=True` permite que se ajuste a la pantalla




@app.callback(
    Output('titulo_seleccion', 'children'),
    [Input('scatter_plot', 'clickData'),
     Input('nivel_visualizacion', 'value')]
)
def update_titulo_seleccion(click_data, nivel):
    if click_data:
        custom_data = click_data['points'][0]['customdata']
        clave = custom_data[0]  # Ajusta el índice según la estructura de customdata
        
        # Mapear el nivel seleccionado a un texto más claro
        niveles_dict = {
            'series': 'Serie',
            'municipio': 'Municipio',
            'departamento': 'Departamento'
        }
        nivel_texto = niveles_dict.get(nivel, 'Selección')
        return f"{nivel_texto}: {clave}"
    return "Haz clic en un punto para ver más detalles"




# Callback para actualizar el gráfico según el partido y nivel seleccionado
@app.callback(
    [Output('scatter_plot', 'figure'),
     Output('bar_chart_share', 'figure'),
     Output('bar_chart_variation', 'figure'),
     Output('selected_data', 'data')],
    [Input('dropdown_partido', 'value'),
     Input('nivel_visualizacion', 'value'),
     Input('scatter_plot', 'clickData')],
    [State('selected_data', 'data')]
)
def update_graph(partido, nivel, click_data, stored_data):
    
    
    # Colores para las barras según región
    color_regiones = {
    "Montevideo": "#EEA243", 
    "Canelones": "#C8CAC9",  
    "Interior": "#191923"  
}
  
    # Si hay un clic en mobile, usar el último valor almacenado
    if click_data:
        custom_data = click_data['points'][0]['customdata']
        clave = custom_data[0]
    else:
        clave = stored_data if stored_data else None    
    
    # 1. Filtrar el DataFrame por el partido seleccionado
    if nivel == 'series':
        filtered_df = df_merged2[(df_merged2['Lema'] == partido) & (df_merged2['Habilitados'] >= 1000)].copy()
        eje_x = "Series"
        titulo = f"{partido} según series electorales"
        
    elif nivel == 'municipio':
        filtered_df = df_municipio[(df_municipio['Lema'] == partido) & (df_municipio['Habilitados'] >= 1000)].copy()
        eje_x = "Municipio"
        titulo = f"{partido} según municipio"
        
    else:
        filtered_df = df_departamento[df_departamento['Lema'] == partido].copy()
        eje_x = "Departamento"
        titulo = f"{partido} según departamento"
        


    # Definir el orden y formato de los tooltips manualmente
    # Definir qué columnas incluir según el nivel seleccionado
    if nivel == "series":
        columnas_hover = [
            "Series", "Municipio", "Departamento",
            "CantidadVotos_2024", "CantidadVotos_2019", "DifVotos",
            "Share_2024", "Share_2019", "VariacionShare",
            "TotalVotos_2024", "TotalVotos_2019"
        ]
    
        hovertemplate = (
            "Serie: %{customdata[0]}<br>"
            "Municipio: %{customdata[1]}<br>"
            "Departamento: %{customdata[2]}<br>"
            "Votos 2024: %{customdata[3]:,}<br>"
            "Votos 2019: %{customdata[4]:,}<br>"
            "Diferencia de votos: %{customdata[5]:,}<br>"
            "% votos elecciones 2024: %{customdata[6]:.2%}<br>"
            "% votos elecciones 2019: %{customdata[7]:.2%}<br>"
            "Variación de % votos: %{customdata[8]:.2%}<br>"
            "Total votos 2024: %{customdata[9]:,}<br>"
            "Total votos 2019: %{customdata[10]:,}<br>"
            "<extra></extra>"
    )
    
    elif nivel == "municipio":
        columnas_hover = [
            "Municipio", "Departamento",
            "CantidadVotos_2024", "CantidadVotos_2019", "DifVotos",
            "Share_2024", "Share_2019", "VariacionShare",
            "TotalVotos_2024", "TotalVotos_2019"
        ]
    
        hovertemplate = (
            "Municipio: %{customdata[0]}<br>"
            "Departamento: %{customdata[1]}<br>"
            "Votos 2024: %{customdata[2]:,}<br>"
            "Votos 2019: %{customdata[3]:,}<br>"
            "Diferencia de votos: %{customdata[4]:,}<br>"
            "% votos elecciones 2024: %{customdata[5]:.2%}<br>"
            "% votos elecciones 2019: %{customdata[6]:.2%}<br>"
            "Variación de % votos: %{customdata[7]:.2%}<br>"
            "Total votos 2024: %{customdata[8]:,}<br>"
            "Total votos 2019: %{customdata[9]:,}<br>"
            "<extra></extra>"
    )
    
    else:  # Departamento
        columnas_hover = [
            "Departamento",
            "CantidadVotos_2024", "CantidadVotos_2019", "DifVotos",
            "Share_2024", "Share_2019", "VariacionShare",
            "TotalVotos_2024", "TotalVotos_2019"
        ]
    
        hovertemplate = (
            "Departamento: %{customdata[0]}<br>"
            "Votos 2024: %{customdata[1]:,}<br>"
            "Votos 2019: %{customdata[2]:,}<br>"
            "Diferencia de votos: %{customdata[3]:,}<br>"
            "% votos elecciones 2024: %{customdata[4]:.2%}<br>"
            "% votos elecciones 2019: %{customdata[5]:.2%}<br>"
            "Variación de % votos: %{customdata[6]:.2%}<br>"
            "Total votos 2024: %{customdata[7]:,}<br>"
            "Total votos 2019: %{customdata[8]:,}<br>"
            "<extra></extra>"
    )


    # Crear una columna categórica para asignar colores
    filtered_df['Region'] = filtered_df['Departamento'].apply(
        lambda x: 'Montevideo' if x == 'Montevideo' else ('Canelones' if x == 'Canelones' else 'Interior')
    )

    # Calcular rangos dinámicos del eje X
    x_min = filtered_df["VariacionShare"].min()
    x_max = filtered_df["VariacionShare"].max()


    # Crear el gráfico de dispersión
    scatter_fig = px.scatter(
        filtered_df,
        x="VariacionShare",
        y="Share_2024",
        color="Region",
        size="TotalVotos_2024",
        title=titulo,
        labels={
            "VariacionShare": "Variación (pp) vs 2019",
            "Share_2024": "% votos elecciones 2024",
            "Share_2019": "% votos elecciones 2019",
            eje_x: eje_x
        },
        template='plotly_white',
        color_discrete_map={
            "Montevideo": "#EEA243",
            "Canelones": "#C8CAC9",
            "Interior": "#191923"
        },
        custom_data=filtered_df[columnas_hover]  # Se asignan los datos personalizados
        
    )

    
    
    
    
    # Mejorar el diseño del gráfico
    scatter_fig.update_layout(
        title=dict(
            text=titulo,
            x=0.5,  # Centra el título
            font=dict(size=16, family="Montserrat, sans-serif", color="black", weight="bold"), # Cambia fuente
            y=0.98 # Ajusta el espacio entre el título y el gráfico
    ),
        font=dict(
            family="Montserrat, sans-serif",  # Fuente para todo el gráfico
            size=12,  # Tamaño de fuente predeterminado
            color="black"  # Color del texto
    ),
        xaxis_title="Variación (pp) vs 2019",
        yaxis_title="% votos elecciones 2024",
        xaxis_tickangle=45,
        xaxis=dict(gridcolor="rgba(200, 200, 200, 0.5)", gridwidth=0.5),  # Elimina la cuadrícula del eje X
        yaxis=dict(gridcolor="rgba(200, 200, 200, 0.5)", gridwidth=0.5),   # Elimina la cuadrícula del eje Y
        paper_bgcolor="#FEF9E5",  # Fondo externo del gráfico igual al fondo de la app
        plot_bgcolor="#FEF9E5",  # Fondo interno del gráfico igual al fondo de la app
        legend_title="Región",
        legend_orientation="h",
        legend_y=-0.3,
        margin=dict(l=20, r=20, t=40, b=40),  # Reducimos márgenes para mobile
        autosize=True,  # Hace que el gráfico se ajuste automáticamente
        clickmode='event+select',
        shapes=[
            # Fondo rojo claro para la región de pérdida
            dict(
                type="rect",
                xref="x", yref="paper",
                x0=x_min, x1=0,  # Dinámico: desde el mínimo hasta 0
                y0=0, y1=1,      # Cubrir toda la altura del gráfico
                fillcolor="#D63230",  # Rojo 
                layer="below",
                line_width=0
            ),
            # Fondo verde claro para la región de ganancia
            dict(
                type="rect",
                xref="x", yref="paper",
                x0=0, x1=x_max,  # Dinámico: desde 0 hasta el máximo
                y0=0, y1=1,      # Cubrir toda la altura del gráfico
                fillcolor="#0C7C59",  # Verde 
                layer="below",
                line_width=0
            )
        ]
    )

    # Ajustar el formato del eje Y a porcentaje y que sea automático
    scatter_fig.update_yaxes(
    tickformat=".0%"
    )

    # Ajustar el formato del eje X a porcentaje y que sea automático
    scatter_fig.update_xaxes(
    tickformat=".0%"
    )

    # Aplicar el template al gráfico de dispersión
    scatter_fig.update_traces(hovertemplate=hovertemplate)


    # Crear gráficos complementarios   
    if click_data:
        # Extraer el valor relevante desde customdata
        custom_data = click_data['points'][0]['customdata']
        clave = custom_data[0]  # Ajusta el índice si necesitas otro valor (ej. 1, 2)

        print(f"Clave seleccionada: {clave}")  # Depuración para asegurarte de que sea correcto

        # Filtrar el DataFrame según el nivel seleccionado
        if nivel == 'series':
            detalle_df = df_merged2[df_merged2['Series'] == clave].copy()
        elif nivel == 'municipio':
            detalle_df = df_municipio[df_municipio['Municipio'] == clave].copy()
        else:
            detalle_df = df_departamento[df_departamento['Departamento'] == clave].copy()
    else:
        detalle_df = pd.DataFrame()


    if not detalle_df.empty:
        # Ordenar el DataFrame de mayor a menor según Share_2024
        detalle_df = detalle_df.sort_values(by="Share_2024", ascending=True)
        # Crear una columna categórica para asignar colores
        detalle_df['Region'] = detalle_df['Departamento'].apply(
        lambda x: 'Montevideo' if x == 'Montevideo' else ('Canelones' if x == 'Canelones' else 'Interior')
    )
        region_seleccionada = detalle_df["Region"].iloc[0]  # Obtener la región del primer registro
        color_barras = color_regiones.get(region_seleccionada, "#191923")  # Default azul si no hay región
        bar_share = px.bar(
            detalle_df,
            x="Share_2024",
            y="Lema",
            orientation='h',
            template='plotly_white',
            labels={"Share_2024": "", "Lema": ""},
            text_auto='.1%',  # Muestra los valores como porcentaje sin decimales
            color_discrete_sequence=[color_barras]  # Color dinámico según región
        ).update_layout(xaxis=dict(showticklabels=False),
                        autosize=True,
                        paper_bgcolor="#FEF9E5",
                        plot_bgcolor="#FEF9E5",
                        margin=dict(l=20, r=20, t=40, b=40),  
                        font=dict(family="Montserrat, sans-serif", size=12, color="black"),
                        title=dict(
                            text="% votos por partido (2024)",
                            x=0.5,  # Centra el título
                            font=dict(size=16, family="Montserrat, sans-serif", color="black", weight="bold")  # Cambia fuente
    ))  # Ocultar valores del eje X
         
        
        bar_variation = px.bar(
            detalle_df,
            x="VariacionShare",
            y="Lema",
            orientation='h',
            template='plotly_white',
            labels={"VariacionShare": "", "Lema": ""},
            text_auto='.1%',  # Muestra los valores como porcentaje sin decimales
            color_discrete_sequence=[color_barras]  # Color dinámico según región 
        ).update_layout(xaxis=dict(showticklabels=False),
                        autosize=True,
                        paper_bgcolor="#FEF9E5",
                        plot_bgcolor="#FEF9E5",
                        margin=dict(l=20, r=20, t=40, b=40),
                        font=dict(family="Montserrat, sans-serif", size=12, color="black"),
                        title=dict(
                            text="Variación (pp) vs 2019",
                            x=0.5,  # Centra el título
                            font=dict(size=16, family="Montserrat, sans-serif", color="black", weight="bold")  # Cambia fuente
    ))  # Ocultar valores del eje X
    else:
        bar_share = px.bar(title="Sin datos seleccionados")
        bar_variation = px.bar(title="Sin datos seleccionados")
        

    return scatter_fig, bar_share, bar_variation, clave




# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)