import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
import plotly.express as px

# Función para calcular el total para Misiones VPO y VPD
def calculate_total_misiones(row):
    return (
        (row['Cantidad de Funcionarios'] * row['Costo de Pasaje']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Alojamiento']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Per-diem y Otros']) +
        (row['Cantidad de Funcionarios'] * row['Movilidad'])
    )

# Función para calcular el total para Consultorías VPO y VPD
def calculate_total_consultorias(row):
    return row['Nº'] * row['Monto mensual'] * row['cantidad meses']

# Configuración de la página
st.set_page_config(page_title="FONPLATA", layout="wide")

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

# Título de la aplicación
st.title("VPO y VPD")

# Sidebar para selección de página principal, vista y subpágina
st.sidebar.title("Navegación")
main_page = st.sidebar.selectbox("Selecciona una página principal:", ("VPO", "VPD"))

# Función para manejar cada página principal
def handle_page(main_page):
    if main_page == "VPO":
        # Seleccionar Vista: Misiones o Consultorías
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPO_view")
        
        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Resumen Original", "DPP 2025"), key="VPO_Misiones_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Original_VPO'
            
            # Cargar datos
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except FileNotFoundError:
                st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                st.stop()
            except Exception as e:
                st.error(f"Error al leer el archivo Excel: {e}")
                st.stop()
            
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
            
            # Página Resumen Original para Misiones VPO
            if page == "Resumen Original":
                st.header("VPO - Misiones: Resumen Original")
                
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
                
                # Mostrar tabla completa sin decimales
                st.subheader("Tabla Completa - Misiones VPO")
                st.dataframe(df.style.format({"Total": "{:,.0f}"}), height=400)
            
            # Página DPP 2025 para Misiones VPO
            elif page == "DPP 2025":
                st.header("VPO - Misiones: DPP 2025")
                
                # Monto Total Deseado
                desired_total = 434707.0
                st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")
                
                st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")
                
                # Configuración de AgGrid para edición
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True, groupable=True)
                
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
                """), type=["numericColumn"], valueFormatter="Math.round(x).toLocaleString()")
                
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
                
                # Recalcular 'Total' si es necesario
                edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1).round(0)
                
                # Calcular métricas sin decimales
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
                
                # Descargar tabla modificada
                st.subheader("Descargar Tabla Modificada - Misiones VPO")
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_misiones_vpo.csv", mime="text/csv")
        
        elif view == "Consultorías":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Resumen Original", "DPP 2025"), key="VPO_Consultorias_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Consultores_VPO'
            
            # Cargar datos
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except FileNotFoundError:
                st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                st.stop()
            except Exception as e:
                st.error(f"Error al leer el archivo Excel: {e}")
                st.stop()
            
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
            
            # Página Resumen Original para Consultorías VPO
            if page == "Resumen Original":
                st.header("VPO - Consultorías: Resumen Original")
                
                # Mostrar tabla completa sin decimales
                st.subheader("Tabla Completa - Consultorías VPO")
                st.dataframe(df.style.format({"Total": "{:,.0f}"}), height=400)
            
            # Página DPP 2025 para Consultorías VPO
            elif page == "DPP 2025":
                st.header("VPO - Consultorías: DPP 2025")
                
                # Monto Total Deseado
                desired_total = 150000.0
                st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")
                
                st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")
                
                # Configuración de AgGrid para edición
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True, groupable=True)
                
                # Configurar la columna 'Total' para cálculo dinámico sin decimales
                gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                    function(params) {
                        return Math.round(Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses']));
                    }
                """), type=["numericColumn"], valueFormatter="Math.round(x).toLocaleString()")
                
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
                essential_cols = ['Cargo', 'Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in essential_cols:
                    if col not in edited_df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()
                
                # Limpiar y convertir columnas numéricas
                for col in numeric_columns:
                    edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                
                # Recalcular 'Total'
                edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1).round(0)
                
                # Calcular métricas sin decimales
                total_sum = edited_df['Total'].sum()
                difference = desired_total - total_sum
                
                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")
                
                # Descargar tabla modificada
                st.subheader("Descargar Tabla Modificada - Consultorías VPO")
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_consultorias_vpo.csv", mime="text/csv")
    
    elif main_page == "VPD":
        # Seleccionar Vista: Misiones o Consultorías
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPD_view")
        
        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Resumen Original", "DPP 2025"), key="VPD_Misiones_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Misiones_VPD'
    
            # Cargar datos
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except FileNotFoundError:
                st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                st.stop()
            except Exception as e:
                st.error(f"Error al leer el archivo Excel: {e}")
                st.stop()
    
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
    
            # Página Resumen Original para Misiones VPD
            if page == "Resumen Original":
                st.header("VPD - Misiones: Resumen Original")
    
                # Mostrar tabla completa sin decimales
                st.subheader("Tabla Completa - Misiones VPD")
                st.dataframe(df.style.format({"Total": "{:,.0f}"}), height=400)
    
            # Página DPP 2025 para Misiones VPD
            elif page == "DPP 2025":
                st.header("VPD - Misiones: DPP 2025")
    
                # Monto Total Deseado
                desired_total = 168000.0
                st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")
    
                st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")
    
                # Configuración de AgGrid para edición
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True, groupable=True)
    
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
                """), type=["numericColumn"], valueFormatter="Math.round(x).toLocaleString()")
    
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
                essential_cols = ['País', 'Operación', 'VPD/AREA', 'Cantidad de Funcionarios', 'Días', 
                                  'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in essential_cols:
                    if col not in edited_df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()
    
                # Limpiar y convertir columnas numéricas
                for col in numeric_columns:
                    edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    
                # Recalcular 'Total'
                edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1).round(0)
    
                # Calcular métricas sin decimales
                total_sum = edited_df['Total'].sum()
                difference = desired_total - total_sum
    
                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")
    
                # Descargar tabla modificada
                st.subheader("Descargar Tabla Modificada - Misiones VPD")
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_misiones_vpd.csv", mime="text/csv")
        
        elif view == "Consultorías":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Resumen Original", "DPP 2025"), key="VPD_Consultorias_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Consultores_VPD'
    
            # Cargar datos
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except FileNotFoundError:
                st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                st.stop()
            except Exception as e:
                st.error(f"Error al leer el archivo Excel: {e}")
                st.stop()
    
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
    
            # Definir paleta de colores para VPD/AREA
            vpd_area_unique = df['VPD/AREA'].unique()
            # Asignar colores únicos a cada VPD/AREA
            vpd_area_color_map = {area: px.colors.qualitative.Pastel[i % len(px.colors.qualitative.Pastel)] for i, area in enumerate(vpd_area_unique)}
    
            # Página Resumen Original para Consultorías VPD
            if page == "Resumen Original":
                st.header("VPD - Consultorías: Resumen Original")
                
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
                st.dataframe(df.style.format({"Total": "{:,.0f}"}), height=400)
    
            # Página DPP 2025 para Consultorías VPD
            elif page == "DPP 2025":
                st.header("VPD - Consultorías: DPP 2025")
    
                # Monto Total Deseado
                desired_total = 130000.0
                st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")
    
                st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")
    
                # Configuración de AgGrid para edición
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True, groupable=True)
    
                # Configurar la columna 'Total' para cálculo dinámico sin decimales
                gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                    function(params) {
                        return Math.round(Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses']));
                    }
                """), type=["numericColumn"], valueFormatter="Math.round(x).toLocaleString()")
    
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
                edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1).round(0)
    
                # Calcular métricas sin decimales
                total_sum = edited_df['Total'].sum()
                difference = desired_total - total_sum
    
                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")
    
                # Mostrar tabla completa sin decimales
                st.subheader("Tabla Completa - Consultorías VPD")
                st.dataframe(edited_df.style.format({"Total": "{:,.0f}"}), height=400)
    
                # Descargar tabla modificada
                st.subheader("Descargar Tabla Modificada - Consultorías VPD")
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_consultorias_vpd.csv", mime="text/csv")

# Ejecutar la función según la selección
handle_page(main_page)
