import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
import plotly.express as px

# Función para calcular el total para Misiones
def calculate_total_misiones(row):
    return (
        (row['Cantidad de Funcionarios'] * row['Costo de Pasaje']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Alojamiento']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Per-diem y Otros']) +
        (row['Cantidad de Funcionarios'] * row['Movilidad'])
    )

# Función para calcular el total para Consultorías
def calculate_total_consultorias(row):
    return row['Nº'] * row['Monto mensual'] * row['cantidad meses']

# Configuración de la página
st.set_page_config(page_title="VPO", layout="wide")

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
st.title("VPO")

# Sidebar para selección de vista y página
st.sidebar.title("Navegación")
view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"))

if view == "Misiones":
    page = st.sidebar.selectbox("Selecciona una página:", ("Resumen Original", "DPP 2025"))
    
    # Ruta al archivo Excel
    file_path = 'BDD_Ajuste.xlsx'  # Asegúrate de que este archivo está en el mismo directorio o proporciona la ruta completa
    
    # Cargar los datos para Misiones
    try:
        df_misiones = pd.read_excel(file_path, sheet_name='Original_VPO')
    except FileNotFoundError:
        st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
        st.stop()
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        st.stop()
    
    # Verificar que la columna 'Objetivo' exista
    if 'Objetivo' not in df_misiones.columns:
        st.error("La columna 'Objetivo' no existe en el archivo Excel. Asegúrate de que está presente y contiene valores 'R' y 'E'.")
        st.stop()
    
    # Limpiar y convertir las columnas numéricas
    numeric_columns_misiones = [
        'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
        'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total'
    ]
    
    for col in numeric_columns_misiones:
        if col in df_misiones.columns:
            df_misiones[col] = df_misiones[col].astype(str).str.replace(',', '').str.strip()
            df_misiones[col] = pd.to_numeric(df_misiones[col], errors='coerce').fillna(0)
        else:
            st.error(f"La columna '{col}' no existe en el archivo Excel.")
            st.stop()
    
    # Verificar que la columna 'Objetivo' contiene solo 'R' y 'E' o NaN
    valid_objetivos = ['R', 'E']
    if not df_misiones['Objetivo'].dropna().isin(valid_objetivos).all():
        st.warning("La columna 'Objetivo' contiene valores distintos a 'R' y 'E'. Estos valores serán ignorados en el gráfico de Objetivo.")
    
    # Calcular la columna 'Total' inicialmente si no está presente
    if 'Total' not in df_misiones.columns or df_misiones['Total'].sum() == 0:
        df_misiones['Total'] = df_misiones.apply(calculate_total_misiones, axis=1)
    
    # Definir la paleta de colores para Objetivo
    objetivo_color_mapping_misiones = {
        'E': '#a4161a',
        'R': '#d3d3d3'
    }
    
    # Definir la paleta de colores para Países
    pais_color_mapping_misiones = {
        'Argentina': '#457b9d',
        'Bolivia': '#3a5a40',
        'Brasil': '#ffb703',
        'Paraguay': '#d62828',
        'Uruguay': '#1d3557'
    }
    
    # Página Resumen Original para Misiones
    if page == "Resumen Original":
        st.header("Resumen Original")
        
        # Resumen por país
        summary_by_country = df_misiones.groupby('País')['Total'].sum().reset_index()
        
        # Resumen por Objetivo R y E (excluyendo NaN y otros valores)
        summary_by_obj = df_misiones[df_misiones['Objetivo'].isin(['R', 'E'])].groupby('Objetivo')['Total'].sum().reset_index()
        
        # Crear los dos gráficos de dona
        col1, col2 = st.columns(2)
        
        # Gráfico de Dona de Montos Totales por País
        fig1 = px.pie(
            summary_by_country,
            names='País',
            values='Total',
            hole=0.4,
            title="Montos Totales por País",
            color='País',
            color_discrete_map=pais_color_mapping_misiones
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
            margin=dict(t=60, b=20, l=150, r=20),  # Aumentar margen izquierdo para la leyenda
            height=300  # Tamaño reducido
        )
        col1.plotly_chart(fig1, use_container_width=True)
        
        # Gráfico de Dona por Objetivo R y E
        fig2 = px.pie(
            summary_by_obj,
            names='Objetivo',
            values='Total',
            hole=0.4,
            title="Distribución por Objetivo R y E",
            color='Objetivo',
            color_discrete_map=objetivo_color_mapping_misiones
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
            margin=dict(t=60, b=20, l=150, r=20),  # Aumentar margen izquierdo para la leyenda
            height=300  # Tamaño reducido
        )
        col2.plotly_chart(fig2, use_container_width=True)
        
        # Visualizar tabla completa con formato, solo formatear 'Total'
        st.subheader("Tabla Completa")
        st.dataframe(
            df_misiones.style.format({"Total": "{:,.2f}"}),
            height=400
        )
    
    # Página DPP 2025 para Misiones
    elif page == "DPP 2025":
        st.header("DPP 2025")
        
        # Mostrar el monto total deseado (fijo)
        desired_total_misiones = 434707.0
        st.subheader(f"Monto Total Deseado: {desired_total_misiones:,.2f} USD")
        
        st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")
        
        # Configuración de AgGrid para edición
        gb = GridOptionsBuilder.from_dataframe(df_misiones)
        gb.configure_default_column(editable=True, groupable=True)
        
        # Configurar la columna 'Total' para que se calcule dinámicamente en el lado del cliente
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                return Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Costo de Pasaje']) +
                       Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Días']) * Number(params.data['Alojamiento']) +
                       Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Días']) * Number(params.data['Per-diem y Otros']) +
                       Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Movilidad']);
            }
        """), type=["numericColumn"], valueFormatter="x.toLocaleString()")
        
        # Personalizar el aspecto de la tabla
        gb.configure_grid_options(domLayout='normal')
        grid_options = gb.build()
        
        # Mostrar tabla editable
        grid_response = AgGrid(
            df_misiones,
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED,
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=False,
            height=400,
            width='100%',
            enable_enterprise_modules=False,
            allow_unsafe_jscode=True,
            theme='alpine'  # Puedes probar otros temas como 'streamlit', 'balham', etc.
        )
        
        # Datos editados
        edited_df_misiones = pd.DataFrame(grid_response['data'])
        
        # Verificar si 'País' y 'Objetivo' están presentes
        if 'País' not in edited_df_misiones.columns:
            st.error("La columna 'País' está ausente en los datos editados.")
            st.stop()
        if 'Objetivo' not in edited_df_misiones.columns:
            st.error("La columna 'Objetivo' está ausente en los datos editados.")
            st.stop()
        
        # Limpiar y convertir las columnas numéricas en 'edited_df_misiones'
        for col in numeric_columns_misiones:
            if col in edited_df_misiones.columns:
                # Eliminar comas y espacios en blanco
                edited_df_misiones[col] = edited_df_misiones[col].astype(str).str.replace(',', '').str.strip()
                # Convertir a numérico
                edited_df_misiones[col] = pd.to_numeric(edited_df_misiones[col], errors='coerce').fillna(0)
            else:
                st.error(f"La columna '{col}' no existe en los datos editados.")
                st.stop()
        
        # Verificar que la columna 'Objetivo' contiene solo 'R' y 'E' o NaN
        if not edited_df_misiones['Objetivo'].dropna().isin(['R', 'E']).all():
            st.warning("La columna 'Objetivo' contiene valores distintos a 'R' y 'E'. Estos valores serán ignorados en los gráficos.")
        
        # Recalcular la columna 'Total' con los datos editados
        edited_df_misiones['Total'] = edited_df_misiones.apply(calculate_total_misiones, axis=1)
        
        # Mostrar el nuevo monto total general y la diferencia
        total_sum_misiones = edited_df_misiones['Total'].sum()
        difference_misiones = desired_total_misiones - total_sum_misiones
        
        # Mostrar las métricas de manera destacada
        col1, col2 = st.columns(2)
        col1.metric("Nuevo Monto Total General (USD)", f"{total_sum_misiones:,.2f}")
        col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference_misiones:,.2f}")
        
        # Resumen por país y Objetivo (actualizado)
        summary_by_country_edited_misiones = edited_df_misiones.groupby('País')['Total'].sum().reset_index()
        summary_by_obj_edited_misiones = edited_df_misiones[edited_df_misiones['Objetivo'].isin(['R', 'E'])].groupby('Objetivo')['Total'].sum().reset_index()
        
        # Crear los dos gráficos de dona actualizados
        col3, col4 = st.columns(2)
        
        # Gráfico de Dona de Montos Totales por País (Actualizado)
        fig3 = px.pie(
            summary_by_country_edited_misiones,
            names='País',
            values='Total',
            hole=0.4,
            title="Montos Totales por País (Actualizado)",
            color='País',
            color_discrete_map=pais_color_mapping_misiones
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
            margin=dict(t=60, b=20, l=150, r=20),  # Aumentar margen izquierdo para la leyenda
            height=300  # Tamaño reducido
        )
        col3.plotly_chart(fig3, use_container_width=True)
        
        # Gráfico de Dona por Objetivo R y E (Actualizado)
        fig4 = px.pie(
            summary_by_obj_edited_misiones,
            names='Objetivo',
            values='Total',
            hole=0.4,
            title="Distribución por Objetivo R y E (Actualizado)",
            color='Objetivo',
            color_discrete_map=objetivo_color_mapping_misiones
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
            margin=dict(t=60, b=20, l=150, r=20),  # Aumentar margen izquierdo para la leyenda
            height=300  # Tamaño reducido
        )
        col4.plotly_chart(fig4, use_container_width=True)
        
        # Descargar la tabla modificada
        st.subheader("Descargar Tabla Modificada")
        csv = edited_df_misiones.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_misiones.csv", mime="text/csv")

elif view == "Consultorías":
    page = st.sidebar.selectbox("Selecciona una página:", ("Resumen Original", "DPP 2025"))
    
    # Ruta al archivo Excel
    file_path = 'BDD_Ajuste.xlsx'  # Asegúrate de que este archivo está en el mismo directorio o proporciona la ruta completa
    
    # Cargar los datos para Consultorías
    try:
        df_consultorias = pd.read_excel(file_path, sheet_name='Consultores_VPO')
    except FileNotFoundError:
        st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
        st.stop()
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        st.stop()
    
    # Verificar que la columna 'Objetivo' exista
    if 'Objetivo' not in df_consultorias.columns:
        st.error("La columna 'Objetivo' no existe en el archivo Excel. Asegúrate de que está presente y contiene valores 'R' y 'E'.")
        st.stop()
    
    # Limpiar y convertir las columnas numéricas
    numeric_columns_consultorias = [
        'Nº', 'Monto mensual', 'cantidad meses', 'Total'
    ]
    
    for col in numeric_columns_consultorias:
        if col in df_consultorias.columns:
            df_consultorias[col] = df_consultorias[col].astype(str).str.replace(',', '').str.strip()
            df_consultorias[col] = pd.to_numeric(df_consultorias[col], errors='coerce').fillna(0)
        else:
            st.error(f"La columna '{col}' no existe en el archivo Excel.")
            st.stop()
    
    # Verificar que la columna 'Objetivo' contiene solo 'R' y 'E' o NaN
    valid_objetivos = ['R', 'E']
    if not df_consultorias['Objetivo'].dropna().isin(valid_objetivos).all():
        st.warning("La columna 'Objetivo' contiene valores distintos a 'R' y 'E'. Estos valores serán ignorados en los gráficos.")
    
    # Calcular la columna 'Total' inicialmente si no está presente
    if 'Total' not in df_consultorias.columns or df_consultorias['Total'].sum() == 0:
        df_consultorias['Total'] = df_consultorias.apply(calculate_total_consultorias, axis=1)
    
    # Definir la paleta de colores para Objetivo
    objetivo_color_mapping_consultorias = {
        'E': '#a4161a',
        'R': '#d3d3d3'
    }
    
    # Definir la paleta de colores para Tipo con colores específicos
    tipo_color_mapping = {
        'Nuevas Operaciones': '#14213d',
        'Adm. Cartera': '#fca311'
    }
    
    # Página Resumen Original para Consultorías
    if page == "Resumen Original":
        st.header("Resumen Original - Consultorías")
        
        # Resumen por Objetivo
        summary_by_obj_consultorias = df_consultorias[df_consultorias['Objetivo'].isin(['R', 'E'])].groupby('Objetivo')['Total'].sum().reset_index()
        
        # Resumen por Tipo
        summary_by_tipo = df_consultorias.groupby('tipo')['Total'].sum().reset_index()
        
        # Crear los dos gráficos de dona
        col1, col2 = st.columns(2)
        
        # Gráfico de Dona por Objetivo R y E
        fig1 = px.pie(
            summary_by_obj_consultorias,
            names='Objetivo',
            values='Total',
            hole=0.4,
            title="Distribución por Objetivo R y E",
            color='Objetivo',
            color_discrete_map=objetivo_color_mapping_consultorias
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
            margin=dict(t=60, b=20, l=150, r=20),  # Aumentar margen izquierdo para la leyenda
            height=300  # Tamaño reducido
        )
        col1.plotly_chart(fig1, use_container_width=True)
        
        # Gráfico de Dona por Tipo con Colores Específicos
        fig2 = px.pie(
            summary_by_tipo,
            names='tipo',
            values='Total',
            hole=0.4,
            title="Distribución por Tipo",
            color='tipo',
            color_discrete_map=tipo_color_mapping
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
            margin=dict(t=60, b=20, l=150, r=20),  # Aumentar margen izquierdo para la leyenda
            height=300  # Tamaño reducido
        )
        col2.plotly_chart(fig2, use_container_width=True)
        
        # Visualizar tabla completa con formato, solo formatear 'Total'
        st.subheader("Tabla Completa - Consultorías")
        st.dataframe(
            df_consultorias.style.format({"Total": "{:,.2f}"}),
            height=400
        )
    
    # Página DPP 2025 para Consultorías
    elif page == "DPP 2025":
        st.header("DPP 2025 - Consultorías")
        
        # Mostrar el monto total deseado (fijo)
        desired_total_consultorias = 469700.0
        st.subheader(f"Monto Total Deseado: {desired_total_consultorias:,.2f} USD")
        
        st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")
        
        # Configuración de AgGrid para edición
        gb = GridOptionsBuilder.from_dataframe(df_consultorias)
        gb.configure_default_column(editable=True, groupable=True)
        
        # Configurar la columna 'Total' para que se calcule dinámicamente en el lado del cliente
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                return Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses']);
            }
        """), type=["numericColumn"], valueFormatter="x.toLocaleString()")
        
        # Personalizar el aspecto de la tabla
        gb.configure_grid_options(domLayout='normal')
        grid_options = gb.build()
        
        # Mostrar tabla editable
        grid_response = AgGrid(
            df_consultorias,
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED,
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=False,
            height=400,
            width='100%',
            enable_enterprise_modules=False,
            allow_unsafe_jscode=True,
            theme='alpine'  # Puedes probar otros temas como 'streamlit', 'balham', etc.
        )
        
        # Datos editados
        edited_df_consultorias = pd.DataFrame(grid_response['data'])
        
        # Verificar si 'Cargo', 'Objetivo' y 'tipo' están presentes
        required_columns = ['Cargo', 'Objetivo', 'tipo']
        for col in required_columns:
            if col not in edited_df_consultorias.columns:
                st.error(f"La columna '{col}' está ausente en los datos editados.")
                st.stop()
        
        # Limpiar y convertir las columnas numéricas en 'edited_df_consultorias'
        for col in numeric_columns_consultorias:
            if col in edited_df_consultorias.columns:
                # Eliminar comas y espacios en blanco
                edited_df_consultorias[col] = edited_df_consultorias[col].astype(str).str.replace(',', '').str.strip()
                # Convertir a numérico
                edited_df_consultorias[col] = pd.to_numeric(edited_df_consultorias[col], errors='coerce').fillna(0)
            else:
                st.error(f"La columna '{col}' no existe en los datos editados.")
                st.stop()
        
        # Verificar que la columna 'Objetivo' contiene solo 'R' y 'E' o NaN
        if not edited_df_consultorias['Objetivo'].dropna().isin(['R', 'E']).all():
            st.warning("La columna 'Objetivo' contiene valores distintos a 'R' y 'E'. Estos valores serán ignorados en los gráficos.")
        
        # Recalcular la columna 'Total' con los datos editados
        edited_df_consultorias['Total'] = edited_df_consultorias.apply(calculate_total_consultorias, axis=1)
        
        # Mostrar el nuevo monto total general y la diferencia
        total_sum_consultorias = edited_df_consultorias['Total'].sum()
        difference_consultorias = desired_total_consultorias - total_sum_consultorias
        
        # Mostrar las métricas de manera destacada
        col1, col2 = st.columns(2)
        col1.metric("Nuevo Monto Total General (USD)", f"{total_sum_consultorias:,.2f}")
        col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference_consultorias:,.2f}")
        
        # Resumen por Objetivo y Tipo (actualizado)
        summary_by_obj_edited_consultorias = edited_df_consultorias[edited_df_consultorias['Objetivo'].isin(['R', 'E'])].groupby('Objetivo')['Total'].sum().reset_index()
        summary_by_tipo_edited = edited_df_consultorias.groupby('tipo')['Total'].sum().reset_index()
        
        # Crear los dos gráficos de dona actualizados
        col3, col4 = st.columns(2)
        
        # Gráfico de Dona por Objetivo R y E (Actualizado)
        fig3 = px.pie(
            summary_by_obj_edited_consultorias,
            names='Objetivo',
            values='Total',
            hole=0.4,
            title="Distribución por Objetivo R y E (Actualizado)",
            color='Objetivo',
            color_discrete_map=objetivo_color_mapping_consultorias
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
            margin=dict(t=60, b=20, l=150, r=20),  # Aumentar margen izquierdo para la leyenda
            height=300  # Tamaño reducido
        )
        col3.plotly_chart(fig3, use_container_width=True)
        
        # Gráfico de Dona por Tipo (Actualizado) con Colores Específicos
        fig4 = px.pie(
            summary_by_tipo_edited,
            names='tipo',
            values='Total',
            hole=0.4,
            title="Distribución por Tipo (Actualizado)",
            color='tipo',
            color_discrete_map=tipo_color_mapping
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
            margin=dict(t=60, b=20, l=150, r=20),  # Aumentar margen izquierdo para la leyenda
            height=300  # Tamaño reducido
        )
        col4.plotly_chart(fig4, use_container_width=True)
        
        # Descargar la tabla modificada
        st.subheader("Descargar Tabla Modificada")
        csv = edited_df_consultorias.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_consultorias.csv", mime="text/csv")
