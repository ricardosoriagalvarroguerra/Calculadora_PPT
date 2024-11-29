import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
import plotly.express as px
import os

# Función para calcular el total para Misiones VPO y VPD
def calculate_total_misiones(row):
    return round(
        (row['Cantidad de Funcionarios'] * row['Costo de Pasaje']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Alojamiento']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Per-diem y Otros']) +
        (row['Cantidad de Funcionarios'] * row['Movilidad'])
    )

# Función para calcular el total para Consultorías VPO y VPD
def calculate_total_consultorias(row):
    return round(row['Nº'] * row['Monto mensual'] * row['cantidad meses'])

# Función para cargar datos con persistencia
def load_data(sheet_name, main_page, view, dpp_page):
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_file = f"{cache_dir}/{main_page}_{view}_DPP2025.csv"
    
    if dpp_page == "DPP 2025":
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file)
        else:
            try:
                df = pd.read_excel('BDD_Ajuste.xlsx', sheet_name=sheet_name)
                # Calcular 'Total' si no existe o es cero
                if 'Total' not in df.columns or df['Total'].sum() == 0:
                    if view == "Misiones":
                        df['Total'] = df.apply(calculate_total_misiones, axis=1)
                    elif view == "Consultorías":
                        df['Total'] = df.apply(calculate_total_consultorias, axis=1)
                df.to_csv(cache_file, index=False)
            except FileNotFoundError:
                st.error(f"No se encontró el archivo 'BDD_Ajuste.xlsx'. Asegúrate de que está en el directorio correcto.")
                st.stop()
            except Exception as e:
                st.error(f"Error al leer el archivo Excel: {e}")
                st.stop()
    else:
        try:
            df = pd.read_excel('BDD_Ajuste.xlsx', sheet_name=sheet_name)
        except FileNotFoundError:
            st.error(f"No se encontró el archivo 'BDD_Ajuste.xlsx'. Asegúrate de que está en el directorio correcto.")
            st.stop()
        except Exception as e:
            st.error(f"Error al leer el archivo Excel: {e}")
            st.stop()
    
    return df, cache_file

# Función para guardar datos en cache
def save_data(df, cache_file):
    df.to_csv(cache_file, index=False)

# Configuración de la página
st.set_page_config(page_title="Presupuesto", layout="wide")

# Estilo personalizado para la aplicación
st.markdown("""
<style>
    .main {
        background-color: #ffffff;
    }
    .stButton>button {
        color: white;
        background-color: #4CAF50;
    }
    .stNumberInput>div>input {
        background-color: #f0f2f6;
    }
    .stDataFrame div, .stDataFrame th, .stDataFrame td {
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar para selección de página principal, vista y subpágina
st.sidebar.title("Navegación")
main_page = st.sidebar.selectbox("Selecciona una página principal:", ("VPO", "VPD", "Consolidado"))

# Título dinámico de la aplicación
st.title(main_page)

# Función para manejar cada página principal
def handle_page(main_page):
    # Definir las Deseados para cada sección
    deseados = {
        "VPO": {
            "Misiones": {
                "Deseado": 434707
            },
            "Consultorías": {
                "Deseado": 150000
            }
        },
        "VPD": {
            "Misiones": {
                "Deseado": 168000
            },
            "Consultorías": {
                "Deseado": 130000
            }
        }
    }

    if main_page in ["VPO", "VPD"]:
        # Seleccionar Vista: Misiones o Consultorías
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key=f"{main_page}_view")
        
        # Seleccionar Subpágina
        page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key=f"{main_page}_{view}_page")
        
        # Definir el nombre de la hoja de Excel según la página principal y vista
        sheet_mapping = {
            ("VPO", "Misiones"): "Original_VPO",
            ("VPO", "Consultorías"): "Consultores_VPO",
            ("VPD", "Misiones"): "Misiones_VPD",
            ("VPD", "Consultorías"): "Consultores_VPD"
        }
        
        sheet_name = sheet_mapping.get((main_page, view))
        
        # Cargar datos y obtener el cache_file
        df, cache_file = load_data(sheet_name, main_page, view, page)
        
        # Definir paletas de colores
        if main_page == "VPO":
            if view == "Misiones":
                # Definir paleta de colores para Objetivo
                objetivo_color_map = {
                    'E': '#a4161a',
                    'R': '#d3d3d3'
                }
                
                # Definir paleta de colores para Países
                pais_color_map = {
                    'Argentina': '#457b9d',
                    'Bolivia': '#3a5a40',
                    'Brasil': '#ffb703',
                    'Paraguay': '#d62828',
                    'Uruguay': '#1d3557'
                }
            elif view == "Consultorías":
                # Definir paleta de colores para VPD/AREA
                vpd_area_unique = df['VPD/AREA'].unique()
                vpd_area_color_map = {area: px.colors.qualitative.Pastel[i % len(px.colors.qualitative.Pastel)] for i, area in enumerate(vpd_area_unique)}
        
        elif main_page == "VPD":
            if view == "Misiones":
                # Definir paleta de colores para Países
                pais_color_map = {
                    'Argentina': '#457b9d',
                    'Bolivia': '#3a5a40',
                    'Brasil': '#ffb703',
                    'Paraguay': '#d62828',
                    'Uruguay': '#1d3557'
                }
            elif view == "Consultorías":
                # Definir paleta de colores para VPD/AREA
                vpd_area_unique = df['VPD/AREA'].unique()
                vpd_area_color_map = {area: px.colors.qualitative.Pastel[i % len(px.colors.qualitative.Pastel)] for i, area in enumerate(vpd_area_unique)}

        if page == "Requerimiento del área":
            if view == "Misiones":
                st.header(f"{main_page} - Misiones: Requerimiento del área")
                
                # Resumen por País
                summary_country = df.groupby('País')['Total'].sum().reset_index()
                
                # Resumen por Objetivo R y E (solo para VPO)
                if main_page == "VPO":
                    summary_obj = df[df['Objetivo'].isin(['R', 'E'])].groupby('Objetivo')['Total'].sum().reset_index()
                
                # Crear gráficos de dona
                col1, col2 = st.columns(2)
                
                # Gráfico de Dona: Montos Totales por País
                fig1 = px.pie(
                    summary_country,
                    names='País',
                    values='Total',
                    hole=0.4,
                    title="Montos Totales por País",
                    color='País',
                    color_discrete_map=pais_color_map
                )
                fig1.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="left",
                        x=-0.1
                    ),
                    margin=dict(t=60, b=20, l=150, r=20),
                    height=300
                )
                col1.plotly_chart(fig1, use_container_width=True)
                
                # Gráfico de Dona: Distribución por Objetivo R y E (solo para VPO)
                if main_page == "VPO":
                    fig2 = px.pie(
                        summary_obj,
                        names='Objetivo',
                        values='Total',
                        hole=0.4,
                        title="Distribución por Objetivo R y E",
                        color='Objetivo',
                        color_discrete_map=objetivo_color_map
                    )
                    fig2.update_layout(
                        showlegend=True,
                        legend=dict(
                            orientation="v",
                            yanchor="top",
                            y=1,
                            xanchor="left",
                            x=-0.1
                        ),
                        margin=dict(t=60, b=20, l=150, r=20),
                        height=300
                    )
                    col2.plotly_chart(fig2, use_container_width=True)
                
                # Mostrar tabla completa con formato sin decimales en columnas específicas
                st.subheader(f"Tabla Completa - {main_page} Misiones")
                st.dataframe(
                    df.style.format({
                        "Cantidad de Funcionarios": "{:.0f}",
                        "Días": "{:.0f}",
                        "Costo de Pasaje": "{:,.0f}",
                        "Alojamiento": "{:,.0f}",
                        "Per-diem y Otros": "{:,.0f}",
                        "Movilidad": "{:,.0f}",
                        "Total": "{:,.0f}"
                    }),
                    height=400
                )
        
        elif page == "DPP 2025":
            if view == "Misiones":
                st.header(f"{main_page} - Misiones: DPP 2025")
                
                # Monto Total Deseado
                desired_total = deseados[main_page][view]["Deseado"]
                st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")
                
                st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")
                
                # Configuración de AgGrid para edición
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True, groupable=True)
                
                # Configurar columnas para mostrar sin decimales
                numeric_columns_aggrid = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                          'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in numeric_columns_aggrid:
                    gb.configure_column(
                        col,
                        type=['numericColumn'],
                        valueFormatter="Math.round(x).toLocaleString()"
                    )
                
                # Configurar la columna 'Total' para cálculo dinámico sin decimales
                gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                    function(params) {
                        return Math.round(
                            Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Costo de Pasaje']) +
                            Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Días']) * Number(params.data['Alojamiento']) +
                            Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Días']) * Number(params.data['Per-diem y Otros']) +
                            Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Movilidad'])
                        );
                    }
                """))
                
                # Personalizar apariencia de la tabla
                gb.configure_grid_options(domLayout='normal')
                grid_options = gb.build()
                
                # Mostrar tabla editable
                grid_response = AgGrid(
                    df,
                    gridOptions=grid_options,
                    data_return_mode=DataReturnMode.FILTERED,
                    update_mode='MODEL_CHANGED',
                    fit_columns_on_grid_load=False,
                    height=400,
                    width='100%',
                    enable_enterprise_modules=False,
                    allow_unsafe_jscode=True,
                    theme='alpine'
                )
                
                # Obtener datos editados
                edited_df = pd.DataFrame(grid_response['data'])
                
                # Verificar columnas esenciales
                essential_cols = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                  'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Objetivo', 'Total']
                for col in essential_cols:
                    if col not in edited_df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()
                
                # Limpiar y convertir columnas numéricas
                for col in numeric_columns:
                    edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                
                # Verificar valores en 'Objetivo'
                if 'Objetivo' in edited_df.columns and not edited_df['Objetivo'].dropna().isin(['R', 'E']).all():
                    st.warning("La columna 'Objetivo' contiene valores distintos a 'R' y 'E'. Estos valores serán ignorados en los gráficos de Objetivo.")
                
                # Recalcular 'Total'
                edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)
                
                # Calcular métricas
                total_sum = edited_df['Total'].sum()
                difference = desired_total - total_sum
                
                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")
                
                # Resumen por País y Objetivo
                summary_country = edited_df.groupby('País')['Total'].sum().reset_index()
                if 'Objetivo' in edited_df.columns:
                    summary_obj = edited_df[edited_df['Objetivo'].isin(['R', 'E'])].groupby('Objetivo')['Total'].sum().reset_index()
                else:
                    summary_obj = pd.DataFrame(columns=['Objetivo', 'Total'])
                
                # Crear gráficos de dona actualizados
                col3, col4 = st.columns(2)
                
                # Gráfico de Dona: Montos Totales por País (Actualizado)
                fig3 = px.pie(
                    summary_country,
                    names='País',
                    values='Total',
                    hole=0.4,
                    title="Montos Totales por País (Actualizado)",
                    color='País',
                    color_discrete_map=pais_color_map
                )
                fig3.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="left",
                        x=-0.1
                    ),
                    margin=dict(t=60, b=20, l=150, r=20),
                    height=300
                )
                col3.plotly_chart(fig3, use_container_width=True)
                
                # Gráfico de Dona: Distribución por Objetivo R y E (Actualizado)
                if not summary_obj.empty:
                    fig4 = px.pie(
                        summary_obj,
                        names='Objetivo',
                        values='Total',
                        hole=0.4,
                        title="Distribución por Objetivo R y E (Actualizado)",
                        color='Objetivo',
                        color_discrete_map=objetivo_color_map
                    )
                    fig4.update_layout(
                        showlegend=True,
                        legend=dict(
                            orientation="v",
                            yanchor="top",
                            y=1,
                            xanchor="left",
                            x=-0.1
                        ),
                        margin=dict(t=60, b=20, l=150, r=20),
                        height=300
                    )
                    col4.plotly_chart(fig4, use_container_width=True)
                
                # Descargar tabla modificada sin decimales
                st.subheader(f"Descargar Tabla Modificada - {main_page} Misiones")
                edited_df['Total'] = edited_df['Total'].round(0)
                save_data(edited_df, cache_file)
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{main_page}_misiones_dpp2025.csv", mime="text/csv")
            
            elif view == "Consultorías":
                st.header(f"{main_page} - Consultorías: DPP 2025")
                
                # Monto Total Deseado
                desired_total = deseados[main_page][view]["Deseado"]
                st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")
                
                st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")
                
                # Configuración de AgGrid para edición
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True, groupable=True)
                
                # Configurar columnas para mostrar sin decimales
                numeric_columns_aggrid = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in numeric_columns_aggrid:
                    gb.configure_column(
                        col,
                        type=['numericColumn'],
                        valueFormatter="Math.round(x).toLocaleString()"
                    )
                
                # Configurar la columna 'Total' para cálculo dinámico sin decimales
                gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                    function(params) {
                        return Math.round(Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses']));
                    }
                """))
                
                # Personalizar apariencia de la tabla
                gb.configure_grid_options(domLayout='normal')
                grid_options = gb.build()
                
                # Mostrar tabla editable
                grid_response = AgGrid(
                    df,
                    gridOptions=grid_options,
                    data_return_mode=DataReturnMode.FILTERED,
                    update_mode='MODEL_CHANGED',
                    fit_columns_on_grid_load=False,
                    height=400,
                    width='100%',
                    enable_enterprise_modules=False,
                    allow_unsafe_jscode=True,
                    theme='alpine'
                )
                
                # Obtener datos editados
                edited_df = pd.DataFrame(grid_response['data'])
                
                # Verificar columnas esenciales
                essential_cols = ['Cargo', 'VPD/AREA', 'Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in essential_cols:
                    if col not in edited_df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()
                
                # Limpiar y convertir columnas numéricas
                for col in numeric_columns:
                    edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                
                # Recalcular 'Total'
                edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)
                
                # Calcular métricas
                total_sum = edited_df['Total'].sum()
                difference = desired_total - total_sum
                
                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")
                
                # Descargar tabla modificada sin decimales
                st.subheader(f"Descargar Tabla Modificada - {main_page} Consultorías")
                edited_df['Total'] = edited_df['Total'].round(0)
                save_data(edited_df, cache_file)
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{main_page}_consultorias_dpp2025.csv", mime="text/csv")
    
    elif main_page == "Consolidado":
        # Función para crear la tabla Consolidado
        create_consolidado(deseados)

# Función para crear la tabla Consolidado
def create_consolidado(deseados):
    # Definir las Deseados para cada sección
    # ya definido como parámetro
    
    cache_dir = 'cache'
    # Cargar todas las tablas DPP 2025 desde cache
    tables = {}
    for main_page in ["VPO", "VPD"]:
        for view in ["Misiones", "Consultorías"]:
            cache_file = f"{cache_dir}/{main_page}_{view}_DPP2025.csv"
            if os.path.exists(cache_file):
                df = pd.read_csv(cache_file)
                actual = df['Total'].sum()
                ajust = deseados[main_page][view]['Deseado'] - actual
                tables[(main_page, view)] = {
                    "Actual": actual,
                    "Ajuste": ajust,
                    "Deseado": deseados[main_page][view]['Deseado']
                }
            else:
                # Si no hay datos en cache, intentar cargar desde Excel
                st.warning(f"No se encontró la cache para {main_page} - {view}. Asegúrate de que has editado y guardado los datos en DPP 2025.")
    
    # Crear DataFrame Consolidado
    consolidado_data = {
        "Unidad Organizacional": [],
        "Misiones de Servicio - Actual": [],
        "Misiones de Servicio - Ajuste": [],
        "Misiones de Servicio - Deseado": [],
        "Consultorías - Actual": [],
        "Consultorías - Ajuste": [],
        "Consultorías - Deseado": []
    }
    
    for main_page in ["VPO", "VPD"]:
        consolidado_data["Unidad Organizacional"].append(main_page)
        # Misiones
        if (main_page, "Misiones") in tables:
            consolidado_data["Misiones de Servicio - Actual"].append(tables[(main_page, "Misiones")]["Actual"])
            consolidado_data["Misiones de Servicio - Ajuste"].append(tables[(main_page, "Misiones")]["Ajuste"])
            consolidado_data["Misiones de Servicio - Deseado"].append(tables[(main_page, "Misiones")]["Deseado"])
        else:
            consolidado_data["Misiones de Servicio - Actual"].append(0)
            consolidado_data["Misiones de Servicio - Ajuste"].append(deseados[main_page]["Misiones"]["Deseado"])
            consolidado_data["Misiones de Servicio - Deseado"].append(deseados[main_page]["Misiones"]["Deseado"])
        
        # Consultorías
        if (main_page, "Consultorías") in tables:
            consolidado_data["Consultorías - Actual"].append(tables[(main_page, "Consultorías")]["Actual"])
            consolidado_data["Consultorías - Ajuste"].append(tables[(main_page, "Consultorías")]["Ajuste"])
            consolidado_data["Consultorías - Deseado"].append(tables[(main_page, "Consultorías")]["Deseado"])
        else:
            consolidado_data["Consultorías - Actual"].append(0)
            consolidado_data["Consultorías - Ajuste"].append(deseados[main_page]["Consultorías"]["Deseado"])
            consolidado_data["Consultorías - Deseado"].append(deseados[main_page]["Consultorías"]["Deseado"])
    
    consolidado_df = pd.DataFrame(consolidado_data)
    
    # Aplicar formateo condicional a Ajuste
    def highlight_zero(val):
        color = 'background-color: #90ee90' if val == 0 else ''
        return color
    
    # Crear el estilo
    styled_consolidado = consolidado_df.style.applymap(highlight_zero, subset=["Misiones de Servicio - Ajuste", "Consultorías - Ajuste"])
    
    # Formatear números sin decimales
    styled_consolidado = styled_consolidado.format({
        "Misiones de Servicio - Actual": "{:,.0f}",
        "Misiones de Servicio - Ajuste": "{:,.0f}",
        "Misiones de Servicio - Deseado": "{:,.0f}",
        "Consultorías - Actual": "{:,.0f}",
        "Consultorías - Ajuste": "{:,.0f}",
        "Consultorías - Deseado": "{:,.0f}"
    })
    
    st.header("Consolidado")
    st.dataframe(styled_consolidado, height=400)

# Ejecutar la función según la selección
handle_page(main_page)
