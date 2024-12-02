import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
import plotly.express as px
import os  # Importación necesaria para manejar archivos y directorios

# Definir las contraseñas directamente en el código
VPO_PASSWORD = "contraseña_vpo"  # Reemplaza con tu contraseña para VPO
VPD_PASSWORD = "contraseña_vpd"  # Reemplaza con tu contraseña para VPD

# Función para calcular el total para Misiones
def calculate_total_misiones(row):
    return round(
        (row['Cantidad de Funcionarios'] * row['Costo de Pasaje']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Alojamiento']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Per-diem y Otros']) +
        (row['Cantidad de Funcionarios'] * row['Movilidad'])
    )

# Función para calcular el total para Consultorías
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

# Sidebar para selección de página principal
st.sidebar.title("Navegación")
main_page = st.sidebar.selectbox("Selecciona una página principal:", ("VPO", "VPD", "VPF", "VPE", "PRE", "Consolidado"))

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
    st.header("Consolidado de Presupuestos")
    unidades = ['VPO', 'VPD', 'VPF', 'VPE', 'PRE']
    tipos = ['Misiones', 'Consultorías']

    data_misiones = []
    data_consultorias = []

    for unidad in unidades:
        for tipo in tipos:
            cache_file = f"cache/{unidad}_{tipo}_DPP2025.csv"
            row = {'Unidad Organizacional': unidad, 'Tipo': tipo}
            if os.path.exists(cache_file):
                df = pd.read_csv(cache_file)
                actual = df['Total'].sum()
                deseado = deseados[unidad][tipo]
                ajuste = deseado - actual
                row['Actual'] = actual
                row['Ajuste'] = ajuste
                row['Deseado'] = deseado
            else:
                row['Actual'] = 0
                row['Ajuste'] = deseados[unidad][tipo]
                row['Deseado'] = deseados[unidad][tipo]
            (data_misiones if tipo == 'Misiones' else data_consultorias).append(row)

    # Mostrar tablas
    st.subheader("Misiones")
    st.dataframe(pd.DataFrame(data_misiones).style.format("{:,.0f}", subset=['Actual', 'Ajuste', 'Deseado']))

    st.subheader("Consultorías")
    st.dataframe(pd.DataFrame(data_consultorias).style.format("{:,.0f}", subset=['Actual', 'Ajuste', 'Deseado']))

# Función para manejar las páginas VPO, VPD, VPF, VPE y PRE
def handle_main_page(main_page):
    deseados = {
        "VPO": {"Misiones": 434707.0, "Consultorías": 547700.0},
        "VPD": {"Misiones": 168000.0, "Consultorías": 130000.0},
        "VPF": {"Misiones": 138600.0, "Consultorías": 170000.0},
        "VPE": {"Misiones": 28200.0, "Consultorías": 179400.0},
        "PRE": {"Misiones": 80200.0, "Consultorías": 338400.0},
    }

    if main_page == "Consolidado":
        create_consolidado(deseados)
        return

    # Procesar cada unidad organizacional
    file_path = 'BDD_Ajuste.xlsx'
    views = ["Misiones", "Consultorías"]
    view = st.sidebar.selectbox("Selecciona una vista:", views, key=f"{main_page}_view")
    sheet_name = f"{view}_{main_page}"

    # Cargar y procesar datos
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Error al cargar la hoja '{sheet_name}': {e}")
        return

    if view == "Misiones":
        required_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
        for col in required_columns:
            if col not in df.columns:
                st.error(f"La columna '{col}' no existe en los datos.")
                return
        df['Total'] = df.apply(calculate_total_misiones, axis=1)
    else:
        required_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
        for col in required_columns:
            if col not in df.columns:
                st.error(f"La columna '{col}' no existe en los datos.")
                return
        df['Total'] = df.apply(calculate_total_consultorias, axis=1)

    # Mostrar tabla y métricas
    st.dataframe(df.style.format("{:,.0f}"))
    total_actual = df['Total'].sum()
    desired_total = deseados[main_page][view]
    difference = desired_total - total_actual
    st.metric("Monto Actual (USD)", f"{total_actual:,.0f}")
    st.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")

    # Guardar datos en caché
    save_to_cache(df, main_page, view)

# Manejar la página seleccionada
handle_main_page(main_page)
