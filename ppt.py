import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
import plotly.express as px
from streamlit_mito import mitosheet
import os

# Funciones de cálculo con fórmulas corregidas
def calculate_total_misiones(row):
    return round(
        (row['Costo de Pasaje'] + (row['Alojamiento'] + row['Per-diem y Otros'] + row['Movilidad']) * row['Días']) * row['Cantidad de Funcionarios']
    )

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

# Función para guardar datos en cache
def save_to_cache(df, unidad, tipo):
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_file = f"{cache_dir}/{unidad}_{tipo}_DPP2025.csv"
    df.to_csv(cache_file, index=False)

# Función para crear el consolidado dividido en Misiones y Consultorías
def create_consolidado(deseados):
    st.header("")
    cache_dir = 'cache'
    unidades = ['VPO', 'VPD', 'VPE', 'VPF', 'PRE']
    tipos = ['Misiones', 'Consultorías']

    data_misiones = []
    data_consultorias = []

    for unidad in unidades:
        for tipo in tipos:
            row = {'Unidad Organizacional': unidad}
            cache_file = f"{cache_dir}/{unidad}_{tipo}_DPP2025.csv"
            if os.path.exists(cache_file):
                df = pd.read_csv(cache_file)
                actual = df['Total'].sum()
                deseado = deseados[unidad][tipo]
                ajuste = deseado - actual
                row[f"{tipo} - Actual"] = actual
                row[f"{tipo} - Monto DPP 2025"] = deseado
                row[f"{tipo} - Ajuste"] = ajuste
            else:
                deseado = deseados[unidad][tipo]
                row[f"{tipo} - Actual"] = 0
                row[f"{tipo} - Monto DPP 2025"] = deseado
                row[f"{tipo} - Ajuste"] = deseado
            if tipo == 'Misiones':
                data_misiones.append(row)
            else:
                data_consultorias.append(row)

    consolidado_misiones_df = pd.DataFrame(data_misiones)
    consolidado_consultorias_df = pd.DataFrame(data_consultorias)

    def highlight_zero(val):
        color = 'background-color: #90ee90' if val == 0 else ''
        return color

    # Solo incluimos "Actual", "Monto DPP 2025" y "Ajuste" para Misiones
    consolidado_misiones_display = consolidado_misiones_df[['Unidad Organizacional', "Misiones - Actual", "Misiones - Monto DPP 2025", "Misiones - Ajuste"]]
    styled_misiones_df = consolidado_misiones_display.style.applymap(highlight_zero, subset=["Misiones - Ajuste"])
    styled_misiones_df = styled_misiones_df.format(
        "{:,.0f}", 
        subset=[
            "Misiones - Actual",
            "Misiones - Monto DPP 2025",
            "Misiones - Ajuste"
        ]
    )

    # Solo incluimos "Actual", "Monto DPP 2025" y "Ajuste" para Consultorías
    consolidado_consultorias_display = consolidado_consultorias_df[['Unidad Organizacional', "Consultorías - Actual", "Consultorías - Monto DPP 2025", "Consultorías - Ajuste"]]
    styled_consultorias_df = consolidado_consultorias_display.style.applymap(highlight_zero, subset=["Consultorías - Ajuste"])
    styled_consultorias_df = styled_consultorias_df.format(
        "{:,.0f}", 
        subset=[
            "Consultorías - Actual",
            "Consultorías - Monto DPP 2025",
            "Consultorías - Ajuste"
        ]
    )

    st.subheader("Misiones")
    st.dataframe(styled_misiones_df)

    st.subheader("Consultorías")
    st.dataframe(styled_consultorias_df)

# Página "Consolidado" modificada con Mito
def handle_consolidado_page():
    st.header("Consolidado - Tabla Interactiva")
    st.write("Edita la tabla interactiva utilizando Mito y guarda los cambios.")

    # Cargar datos de la hoja Consolidado
    file_path = "BDD_Ajuste.xlsx"
    sheet_name = "Consolidado"
    try:
        consolidado_df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"No se pudo cargar la hoja '{sheet_name}' del archivo '{file_path}'. Error: {e}")
        return

    # Mostrar la tabla interactiva con Mito
    edited_df = mitosheet(consolidado_df, key="mito_consolidado")

    # Botón para descargar el archivo editado
    st.write("Descarga los cambios realizados en la tabla:")
    csv = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name="tabla_consolidado_editada.csv",
        mime="text/csv",
    )

# Función principal
def main():
    # Sidebar para navegación
    st.sidebar.title("Navegación")
    main_page = st.sidebar.selectbox("Selecciona una página principal:", ("VPO", "VPD", "VPE", "VPF", "PRE", "Coordinación", "Consolidado"))
    st.title(main_page)

    # Definir los montos deseados para cada sección
    deseados = {
        "VPO": {"Misiones": 434707.0, "Consultorías": 547700.0},
        "VPD": {"Misiones": 168000.0, "Consultorías": 130000.0},
        "VPE": {"Misiones": 28000.0, "Consultorías": 179400.0},
        "VPF": {"Misiones": 138600.0, "Consultorías": 170000.0},
        "PRE": {"Misiones": 0.0, "Consultorías": 0.0},
    }

    # Cálculo dinámico de los montos deseados para PRE
    file_path = 'BDD_Ajuste.xlsx'
    try:
        df_pre_misiones = pd.read_excel(file_path, sheet_name='Misiones_PRE')
        deseados["PRE"]["Misiones"] = df_pre_misiones['Total'].sum()
    except Exception as e:
        st.warning(f"No se pudo leer la hoja 'Misiones_PRE': {e}")

    try:
        df_pre_consultorias = pd.read_excel(file_path, sheet_name='Consultores_PRE')
        deseados["PRE"]["Consultorías"] = df_pre_consultorias['Total'].sum()
    except Exception as e:
        st.warning(f"No se pudo leer la hoja 'Consultores_PRE': {e}")

    # Manejo de las páginas
    if main_page == "VPO":
        st.write("Página VPO - en desarrollo.")
    elif main_page == "VPD":
        st.write("Página VPD - en desarrollo.")
    elif main_page == "VPE":
        st.write("Página VPE - en desarrollo.")
    elif main_page == "VPF":
        st.write("Página VPF - en desarrollo.")
    elif main_page == "PRE":
        st.write("Página PRE - en desarrollo.")
    elif main_page == "Coordinación":
        create_consolidado(deseados)
    elif main_page == "Consolidado":
        handle_consolidado_page()

if __name__ == "__main__":
    main()
