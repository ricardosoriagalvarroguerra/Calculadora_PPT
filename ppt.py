import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
import plotly.express as px

# Función para calcular el total para Misiones VPD
def calculate_total_misiones(row):
    return (
        (row['Cantidad de Funcionarios'] * row['Costo de Pasaje']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Alojamiento']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Per-diem y Otros']) +
        (row['Cantidad de Funcionarios'] * row['Movilidad'])
    )

# Configuración de la página
st.set_page_config(page_title="VPD", layout="wide")

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
st.title("VPD")

# Sidebar para selección de vista y subpágina
st.sidebar.title("Navegación")
view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPD_view")

# Función para manejar la página de VPD
def handle_vpd_page():
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

            # Mostrar tabla completa
            st.subheader("Tabla Completa - Misiones VPD")
            st.dataframe(df.style.format({"Total": "{:,.2f}"}), height=400)

        # Página DPP 2025 para Misiones VPD
        elif page == "DPP 2025":
            st.header("VPD - Misiones: DPP 2025")

            # Monto Total Deseado
            desired_total = 168000.0
            st.subheader(f"Monto Total Deseado: {desired_total:,.2f} USD")

            st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")

            # Configuración de AgGrid para edición
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_default_column(editable=True, groupable=True)

            # Configurar la columna 'Total' para cálculo dinámico
            gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                function(params) {
                    return Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Costo de Pasaje']) +
                           Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Días']) * Number(params.data['Alojamiento']) +
                           Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Días']) * Number(params.data['Per-diem y Otros']) +
                           Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Movilidad']);
                }
            """), type=["numericColumn"], valueFormatter="x.toLocaleString()")

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
            edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)

            # Calcular métricas
            total_sum = edited_df['Total'].sum()
            difference = desired_total - total_sum

            # Mostrar métricas
            col1, col2 = st.columns(2)
            col1.metric("Monto Actual (USD)", f"{total_sum:,.2f}")
            col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.2f}")

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

            # Mostrar tabla completa
            st.subheader("Tabla Completa - Consultorías VPD")
            st.dataframe(df.style.format({"Total": "{:,.2f}"}), height=400)

        # Página DPP 2025 para Consultorías VPD
        elif page == "DPP 2025":
            st.header("VPD - Consultorías: DPP 2025")

            # Monto Total Deseado
            desired_total = 130000.0
            st.subheader(f"Monto Total Deseado: {desired_total:,.2f} USD")

            st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")

            # Configuración de AgGrid para edición
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_default_column(editable=True, groupable=True)

            # Configurar la columna 'Total' para cálculo dinámico
            gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                function(params) {
                    return Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses']);
                }
            """), type=["numericColumn"], valueFormatter="x.toLocaleString()")

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

            # Mostrar métricas
            col1, col2 = st.columns(2)
            col1.metric("Monto Actual (USD)", f"{total_sum:,.2f}")
            col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.2f}")

            # Mostrar tabla completa
            st.subheader("Tabla Completa - Consultorías VPD")
            st.dataframe(edited_df.style.format({"Total": "{:,.2f}"}), height=400)

            # Descargar tabla modificada
            st.subheader("Descargar Tabla Modificada - Consultorías VPD")
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_consultorias_vpd.csv", mime="text/csv")

# Funciones auxiliares para cálculos
def calculate_total_consultorias(row):
    return row['Nº'] * row['Monto mensual'] * row['cantidad meses']

# Ejecutar la función de VPD
handle_vpd_page()
