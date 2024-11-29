import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode, GridUpdateMode
import plotly.express as px
import os  # Importación necesaria para manejar archivos y directorios

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

# Función para guardar datos en cache
def save_to_cache(df, unidad, tipo):
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_file = f"{cache_dir}/{unidad}_{tipo}_DPP2025.csv"
    df.to_csv(cache_file, index=False)

# Función para crear el consolidado dividido en Misiones y Consultorías
def create_consolidado(deseados):
    st.header("Consolidado")
    cache_dir = 'cache'
    unidades = ['VPO', 'VPD']
    tipos = ['Misiones', 'Consultorías']
    
    # Inicializar listas para almacenar los datos de Misiones y Consultorías
    data_misiones = []
    data_consultorias = []
    
    for unidad in unidades:
        # Datos para Misiones
        row_misiones = {'Unidad Organizacional': unidad}
        tipo = 'Misiones'
        cache_file = f"{cache_dir}/{unidad}_{tipo}_DPP2025.csv"
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file)
            actual = df['Total'].sum()
            deseado = deseados[unidad][tipo]
            ajuste = deseado - actual
            row_misiones[f"{tipo} - Actual"] = actual
            row_misiones[f"{tipo} - Ajuste"] = ajuste
            row_misiones[f"{tipo} - Deseado"] = deseado
        else:
            # Si no hay datos, asumimos que el actual es 0
            deseado = deseados[unidad][tipo]
            row_misiones[f"{tipo} - Actual"] = 0
            row_misiones[f"{tipo} - Ajuste"] = deseado
            row_misiones[f"{tipo} - Deseado"] = deseado
        data_misiones.append(row_misiones)
        
        # Datos para Consultorías
        row_consultorias = {'Unidad Organizacional': unidad}
        tipo = 'Consultorías'
        cache_file = f"{cache_dir}/{unidad}_{tipo}_DPP2025.csv"
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file)
            actual = df['Total'].sum()
            deseado = deseados[unidad][tipo]
            ajuste = deseado - actual
            row_consultorias[f"{tipo} - Actual"] = actual
            row_consultorias[f"{tipo} - Ajuste"] = ajuste
            row_consultorias[f"{tipo} - Deseado"] = deseado
        else:
            # Si no hay datos, asumimos que el actual es 0
            deseado = deseados[unidad][tipo]
            row_consultorias[f"{tipo} - Actual"] = 0
            row_consultorias[f"{tipo} - Ajuste"] = deseado
            row_consultorias[f"{tipo} - Deseado"] = deseado
        data_consultorias.append(row_consultorias)
    
    # Crear DataFrames separados
    consolidado_misiones_df = pd.DataFrame(data_misiones)
    consolidado_consultorias_df = pd.DataFrame(data_consultorias)
    
    # Aplicar formato y estilo
    def highlight_zero(val):
        color = 'background-color: #90ee90' if val == 0 else ''
        return color
    
    # Formatear y estilizar la tabla de Misiones
    styled_misiones_df = consolidado_misiones_df.style.applymap(highlight_zero, subset=["Misiones - Ajuste"])
    styled_misiones_df = styled_misiones_df.format(
        "{:,.0f}", 
        subset=[
            "Misiones - Actual",
            "Misiones - Ajuste",
            "Misiones - Deseado"
        ]
    )
    
    # Formatear y estilizar la tabla de Consultorías
    styled_consultorias_df = consolidado_consultorias_df.style.applymap(highlight_zero, subset=["Consultorías - Ajuste"])
    styled_consultorias_df = styled_consultorias_df.format(
        "{:,.0f}", 
        subset=[
            "Consultorías - Actual",
            "Consultorías - Ajuste",
            "Consultorías - Deseado"
        ]
    )
    
    # Mostrar las tablas por separado
    st.subheader("Consolidado - Misiones")
    st.dataframe(styled_misiones_df)
    
    st.subheader("Consolidado - Consultorías")
    st.dataframe(styled_consultorias_df)

# Función para manejar cada página principal
def handle_page(main_page):
    # Definir los montos deseados para cada sección
    deseados = {
        "VPO": {
            "Misiones": 434707.0,
            "Consultorías": 150000.0
        },
        "VPD": {
            "Misiones": 168000.0,
            "Consultorías": 130000.0
        }
    }

    if main_page == "VPO":
        # Seleccionar Vista: Misiones o Consultorías
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPO_view")
        
        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPO_Misiones_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Original_VPO'
            cache_file = 'cache/VPO_Misiones_DPP2025.csv'
            cache_dir = 'cache'

            # Función para procesar el DataFrame de VPO Misiones
            def process_vpo_misiones_df(df, sheet_name):
                # Verificar columnas
                required_columns = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                    'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Objetivo']
                for col in required_columns:
                    if col not in df.columns:
                        st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                        st.stop()
                
                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                   'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                    else:
                        st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                        st.stop()
                
                # Verificar valores en 'Objetivo'
                valid_objetivos = ['R', 'E']
                if 'Objetivo' in df.columns and not df['Objetivo'].dropna().isin(valid_objetivos).all():
                    st.warning("La columna 'Objetivo' contiene valores distintos a 'R' y 'E'. Estos valores serán ignorados en los gráficos de Objetivo.")
                
                # Calcular 'Total' si es necesario
                if 'Total' not in df.columns or df['Total'].sum() == 0:
                    df['Total'] = df.apply(calculate_total_misiones, axis=1)
                
                return df

            # Definir una clave única para el estado de la sesión
            session_key = "VPO_Misiones_DPP2025"

            # Cargar datos y gestionar el estado de la sesión
            if page == "DPP 2025":
                if session_key not in st.session_state:
                    # Cargar datos desde cache si existe
                    if os.path.exists(cache_file):
                        df = pd.read_csv(cache_file)
                    else:
                        # Cargar datos desde Excel
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name)
                        except FileNotFoundError:
                            st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                            st.stop()
                        except Exception as e:
                            st.error(f"Error al leer el archivo Excel: {e}")
                            st.stop()
                        
                        # Procesar datos
                        df = process_vpo_misiones_df(df, sheet_name)
                    
                    # Asignar al estado de la sesión
                    st.session_state[session_key] = df
                else:
                    df = st.session_state[session_key]
            else:
                if session_key not in st.session_state:
                    # Cargar datos desde Excel
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                    except FileNotFoundError:
                        st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                        st.stop()
                    except Exception as e:
                        st.error(f"Error al leer el archivo Excel: {e}")
                        st.stop()
                    
                    # Procesar datos
                    df = process_vpo_misiones_df(df, sheet_name)
                    
                    # Asignar al estado de la sesión
                    st.session_state[session_key] = df
                else:
                    df = st.session_state[session_key]
            
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
            
            # Página Requerimiento del área para Misiones VPO
            if page == "Requerimiento del área":
                st.header("VPO - Misiones: Requerimiento del área")
                
                # Resumen por País
                summary_country = df.groupby('País')['Total'].sum().reset_index()
                
                # Resumen por Objetivo R y E
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
                
                # Gráfico de Dona: Distribución por Objetivo R y E
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
                st.subheader("Tabla Completa - Misiones VPO")
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
            
            # Página DPP 2025 para Misiones VPO
            elif page == "DPP 2025":
                st.header("VPO - Misiones: DPP 2025")
                
                # Monto Total Deseado
                desired_total = deseados["VPO"]["Misiones"]
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
                    data_return_mode=DataReturnMode.AS_INPUT,
                    update_mode=GridUpdateMode.VALUE_CHANGED,
                    fit_columns_on_grid_load=False,
                    height=400,
                    width='100%',
                    enable_enterprise_modules=False,
                    allow_unsafe_jscode=True,
                    theme='alpine'
                )
                
                # Obtener datos editados
                if grid_response['data'] is not None:
                    edited_df = pd.DataFrame(grid_response['data'])
                    # Actualizar el estado de la sesión con los datos editados
                    st.session_state[session_key] = edited_df
                    df = edited_df
                else:
                    df = st.session_state[session_key]
                
                # Verificar columnas esenciales
                essential_cols = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                  'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Objetivo', 'Total']
                for col in essential_cols:
                    if col not in df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()
                
                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                   'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                
                # Verificar valores en 'Objetivo'
                if 'Objetivo' in df.columns and not df['Objetivo'].dropna().isin(['R', 'E']).all():
                    st.warning("La columna 'Objetivo' contiene valores distintos a 'R' y 'E'. Estos valores serán ignorados en los gráficos de Objetivo.")
                
                # Recalcular 'Total' si es necesario
                df['Total'] = df.apply(calculate_total_misiones, axis=1)
                
                # Calcular métricas sin decimales
                total_sum = df['Total'].sum()
                difference = desired_total - total_sum
                
                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")
                
                # Resumen por País y Objetivo
                summary_country = df.groupby('País')['Total'].sum().reset_index()
                if 'Objetivo' in df.columns:
                    summary_obj = df[df['Objetivo'].isin(['R', 'E'])].groupby('Objetivo')['Total'].sum().reset_index()
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
                
                # Guardar datos editados en cache
                save_to_cache(df, 'VPO', 'Misiones')
                
                # Descargar tabla modificada sin decimales
                st.subheader("Descargar Tabla Modificada - Misiones VPO")
                df['Total'] = df['Total'].round(0)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_misiones_vpo.csv", mime="text/csv")

        elif view == "Consultorías":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPO_Consultorias_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Consultores_VPO'
            cache_file = 'cache/VPO_Consultorías_DPP2025.csv'
            cache_dir = 'cache'

            # Función para procesar el DataFrame de VPO Consultorías
            def process_vpo_consultorias_df(df, sheet_name):
                # Verificar columnas
                required_columns = ['Cargo', 'Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in required_columns:
                    if col not in df.columns:
                        st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                        st.stop()
                
                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                    else:
                        st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                        st.stop()
                
                # Calcular 'Total' si es necesario
                if 'Total' not in df.columns or df['Total'].sum() == 0:
                    df['Total'] = df.apply(calculate_total_consultorias, axis=1)
                
                return df

            # Definir una clave única para el estado de la sesión
            session_key = "VPO_Consultorias_DPP2025"

            # Cargar datos y gestionar el estado de la sesión
            if page == "DPP 2025":
                if session_key not in st.session_state:
                    # Cargar datos desde cache si existe
                    if os.path.exists(cache_file):
                        df = pd.read_csv(cache_file)
                    else:
                        # Cargar datos desde Excel
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name)
                        except FileNotFoundError:
                            st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                            st.stop()
                        except Exception as e:
                            st.error(f"Error al leer el archivo Excel: {e}")
                            st.stop()
                        
                        # Procesar datos
                        df = process_vpo_consultorias_df(df, sheet_name)
                    
                    # Asignar al estado de la sesión
                    st.session_state[session_key] = df
                else:
                    df = st.session_state[session_key]
            else:
                if session_key not in st.session_state:
                    # Cargar datos desde Excel
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                    except FileNotFoundError:
                        st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                        st.stop()
                    except Exception as e:
                        st.error(f"Error al leer el archivo Excel: {e}")
                        st.stop()
                    
                    # Procesar datos
                    df = process_vpo_consultorias_df(df, sheet_name)
                    
                    # Asignar al estado de la sesión
                    st.session_state[session_key] = df
                else:
                    df = st.session_state[session_key]
            
            # Página Requerimiento del área para Consultorías VPO
            if page == "Requerimiento del área":
                st.header("VPO - Consultorías: Requerimiento del área")
                
                # Mostrar tabla completa sin decimales
                st.subheader("Tabla Completa - Consultorías VPO")
                st.dataframe(
                    df.style.format({
                        "Nº": "{:.0f}",
                        "Monto mensual": "{:,.0f}",
                        "cantidad meses": "{:.0f}",
                        "Total": "{:,.0f}"
                    }),
                    height=400
                )
            
            # Página DPP 2025 para Consultorías VPO
            elif page == "DPP 2025":
                st.header("VPO - Consultorías: DPP 2025")
                
                # Monto Total Deseado
                desired_total = deseados["VPO"]["Consultorías"]
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
                    data_return_mode=DataReturnMode.AS_INPUT,
                    update_mode=GridUpdateMode.VALUE_CHANGED,
                    fit_columns_on_grid_load=False,
                    height=400,
                    width='100%',
                    enable_enterprise_modules=False,
                    allow_unsafe_jscode=True,
                    theme='alpine'
                )
                
                # Obtener datos editados
                if grid_response['data'] is not None:
                    edited_df = pd.DataFrame(grid_response['data'])
                    # Actualizar el estado de la sesión con los datos editados
                    st.session_state[session_key] = edited_df
                    df = edited_df
                else:
                    df = st.session_state[session_key]
                
                # Verificar columnas esenciales
                essential_cols = ['Cargo', 'Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in essential_cols:
                    if col not in df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()
                
                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                
                # Recalcular 'Total'
                df['Total'] = df.apply(calculate_total_consultorias, axis=1)
                
                # Calcular métricas sin decimales
                total_sum = df['Total'].sum()
                difference = desired_total - total_sum
                
                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")
                
                # Guardar datos editados en cache
                save_to_cache(df, 'VPO', 'Consultorías')
                
                # Descargar tabla modificada sin decimales
                st.subheader("Descargar Tabla Modificada - Consultorías VPO")
                df['Total'] = df['Total'].round(0)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_consultorias_vpo.csv", mime="text/csv")

    elif main_page == "VPD":
        # Seleccionar Vista: Misiones o Consultorías
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPD_view")
        
        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPD_Misiones_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Misiones_VPD'
            cache_file = 'cache/VPD_Misiones_DPP2025.csv'
            cache_dir = 'cache'

            # Función para procesar el DataFrame de VPD Misiones
            def process_vpd_misiones_df(df, sheet_name):
                # Verificar columnas
                required_columns = ['País', 'Operación', 'VPD/AREA', 'Cantidad de Funcionarios', 'Días', 
                                    'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in required_columns:
                    if col not in df.columns:
                        st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                        st.stop()
                
                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                   'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                    else:
                        st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                        st.stop()
                
                # Calcular 'Total' si es necesario
                if 'Total' not in df.columns or df['Total'].sum() == 0:
                    df['Total'] = df.apply(calculate_total_misiones, axis=1)
                
                return df

            # Definir una clave única para el estado de la sesión
            session_key = "VPD_Misiones_DPP2025"

            # Cargar datos y gestionar el estado de la sesión
            if page == "DPP 2025":
                if session_key not in st.session_state:
                    # Cargar datos desde cache si existe
                    if os.path.exists(cache_file):
                        df = pd.read_csv(cache_file)
                    else:
                        # Cargar datos desde Excel
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name)
                        except FileNotFoundError:
                            st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                            st.stop()
                        except Exception as e:
                            st.error(f"Error al leer el archivo Excel: {e}")
                            st.stop()
                        
                        # Procesar datos
                        df = process_vpd_misiones_df(df, sheet_name)
                    
                    # Asignar al estado de la sesión
                    st.session_state[session_key] = df
                else:
                    df = st.session_state[session_key]
            else:
                if session_key not in st.session_state:
                    # Cargar datos desde Excel
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                    except FileNotFoundError:
                        st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                        st.stop()
                    except Exception as e:
                        st.error(f"Error al leer el archivo Excel: {e}")
                        st.stop()
                    
                    # Procesar datos
                    df = process_vpd_misiones_df(df, sheet_name)
                    
                    # Asignar al estado de la sesión
                    st.session_state[session_key] = df
                else:
                    df = st.session_state[session_key]
            
            # Página Requerimiento del área para Misiones VPD
            if page == "Requerimiento del área":
                st.header("VPD - Misiones: Requerimiento del área")
    
                # Mostrar tabla completa sin decimales
                st.subheader("Tabla Completa - Misiones VPD")
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
    
            # Página DPP 2025 para Misiones VPD
            elif page == "DPP 2025":
                st.header("VPD - Misiones: DPP 2025")
    
                # Monto Total Deseado
                desired_total = deseados["VPD"]["Misiones"]
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
                    data_return_mode=DataReturnMode.AS_INPUT,
                    update_mode=GridUpdateMode.VALUE_CHANGED,
                    fit_columns_on_grid_load=False,
                    height=400,
                    width='100%',
                    enable_enterprise_modules=False,
                    allow_unsafe_jscode=True,
                    theme='alpine'
                )
    
                # Obtener datos editados
                if grid_response['data'] is not None:
                    edited_df = pd.DataFrame(grid_response['data'])
                    # Actualizar el estado de la sesión con los datos editados
                    st.session_state[session_key] = edited_df
                    df = edited_df
                else:
                    df = st.session_state[session_key]
    
                # Verificar columnas esenciales
                essential_cols = ['País', 'Operación', 'VPD/AREA', 'Cantidad de Funcionarios', 'Días', 
                                  'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in essential_cols:
                    if col not in df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()
    
                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                   'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    
                # Recalcular 'Total'
                df['Total'] = df.apply(calculate_total_misiones, axis=1)
    
                # Calcular métricas sin decimales
                total_sum = df['Total'].sum()
                difference = desired_total - total_sum
    
                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")
    
                # Guardar datos editados en cache
                save_to_cache(df, 'VPD', 'Misiones')
    
                # Descargar tabla modificada sin decimales
                st.subheader("Descargar Tabla Modificada - Misiones VPD")
                df['Total'] = df['Total'].round(0)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_misiones_vpd.csv", mime="text/csv")
        
        elif view == "Consultorías":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPD_Consultorias_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Consultores_VPD'
            cache_file = 'cache/VPD_Consultorías_DPP2025.csv'
            cache_dir = 'cache'

            # Función para procesar el DataFrame de VPD Consultorías
            def process_vpd_consultorias_df(df, sheet_name):
                # Verificar columnas
                required_columns = ['Cargo', 'VPD/AREA', 'Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in required_columns:
                    if col not in df.columns:
                        st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                        st.stop()
                
                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                    else:
                        st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                        st.stop()
                
                # Calcular 'Total' si es necesario
                if 'Total' not in df.columns or df['Total'].sum() == 0:
                    df['Total'] = df.apply(calculate_total_consultorias, axis=1)
                
                return df

            # Definir una clave única para el estado de la sesión
            session_key = "VPD_Consultorias_DPP2025"

            # Cargar datos y gestionar el estado de la sesión
            if page == "DPP 2025":
                if session_key not in st.session_state:
                    # Cargar datos desde cache si existe
                    if os.path.exists(cache_file):
                        df = pd.read_csv(cache_file)
                    else:
                        # Cargar datos desde Excel
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name)
                        except FileNotFoundError:
                            st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                            st.stop()
                        except Exception as e:
                            st.error(f"Error al leer el archivo Excel: {e}")
                            st.stop()
                        
                        # Procesar datos
                        df = process_vpd_consultorias_df(df, sheet_name)
                    
                    # Asignar al estado de la sesión
                    st.session_state[session_key] = df
                else:
                    df = st.session_state[session_key]
            else:
                if session_key not in st.session_state:
                    # Cargar datos desde Excel
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                    except FileNotFoundError:
                        st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                        st.stop()
                    except Exception as e:
                        st.error(f"Error al leer el archivo Excel: {e}")
                        st.stop()
                    
                    # Procesar datos
                    df = process_vpd_consultorias_df(df, sheet_name)
                    
                    # Asignar al estado de la sesión
                    st.session_state[session_key] = df
                else:
                    df = st.session_state[session_key]
            
            # Definir paleta de colores para VPD/AREA
            vpd_area_unique = df['VPD/AREA'].unique()
            # Asignar colores únicos a cada VPD/AREA
            vpd_area_color_map = {area: px.colors.qualitative.Pastel[i % len(px.colors.qualitative.Pastel)] for i, area in enumerate(vpd_area_unique)}
    
            # Página Requerimiento del área para Consultorías VPD
            if page == "Requerimiento del área":
                st.header("VPD - Consultorías: Requerimiento del área")
                
                # Resumen por VPD/AREA
                summary_vpd_area = df.groupby('VPD/AREA')['Total'].sum().reset_index()
                
                # Crear gráfico de dona por VPD/AREA
                col1, _ = st.columns(2)
                
                # Gráfico de Dona: Distribución por VPD/AREA
                fig1 = px.pie(
                    summary_vpd_area,
                    names='VPD/AREA',
                    values='Total',
                    hole=0.4,
                    title="Distribución por VPD/AREA",
                    color='VPD/AREA',
                    color_discrete_map=vpd_area_color_map
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
                
                # Mostrar tabla completa sin decimales
                st.subheader("Tabla Completa - Consultorías VPD")
                st.dataframe(
                    df.style.format({
                        "Nº": "{:.0f}",
                        "Monto mensual": "{:,.0f}",
                        "cantidad meses": "{:.0f}",
                        "Total": "{:,.0f}"
                    }),
                    height=400
                )
    
            # Página DPP 2025 para Consultorías VPD
            elif page == "DPP 2025":
                st.header("VPD - Consultorías: DPP 2025")
    
                # Monto Total Deseado
                desired_total = deseados["VPD"]["Consultorías"]
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
                    data_return_mode=DataReturnMode.AS_INPUT,
                    update_mode=GridUpdateMode.VALUE_CHANGED,
                    fit_columns_on_grid_load=False,
                    height=400,
                    width='100%',
                    enable_enterprise_modules=False,
                    allow_unsafe_jscode=True,
                    theme='alpine'
                )
    
                # Obtener datos editados
                if grid_response['data'] is not None:
                    edited_df = pd.DataFrame(grid_response['data'])
                    # Actualizar el estado de la sesión con los datos editados
                    st.session_state[session_key] = edited_df
                    df = edited_df
                else:
                    df = st.session_state[session_key]
    
                # Verificar columnas esenciales
                essential_cols = ['Cargo', 'VPD/AREA', 'Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in essential_cols:
                    if col not in df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()
    
                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    
                # Recalcular 'Total'
                df['Total'] = df.apply(calculate_total_consultorias, axis=1)
    
                # Calcular métricas sin decimales
                total_sum = df['Total'].sum()
                difference = desired_total - total_sum
    
                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")
    
                # Guardar datos editados en cache
                save_to_cache(df, 'VPD', 'Consultorías')
    
                # Mostrar tabla completa sin decimales
                st.subheader("Tabla Completa - Consultorías VPD")
                st.dataframe(
                    df.style.format({
                        "Nº": "{:.0f}",
                        "Monto mensual": "{:,.0f}",
                        "cantidad meses": "{:.0f}",
                        "Total": "{:,.0f}"
                    }),
                    height=400
                )
    
                # Descargar tabla modificada sin decimales
                st.subheader("Descargar Tabla Modificada - Consultorías VPD")
                df['Total'] = df['Total'].round(0)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_consultorias_vpd.csv", mime="text/csv")

    elif main_page == "Consolidado":
        create_consolidado(deseados)

# Ejecutar la función según la selección
handle_page(main_page)
