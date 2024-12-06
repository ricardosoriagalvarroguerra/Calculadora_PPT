import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
from mitosheet.streamlit.v1 import spreadsheet  # Importar Mito
import plotly.express as px
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

# Función para crear el consolidado con Mito
def handle_consolidado_page():
    st.header("Consolidado - Edición Interactiva con Mito")
    st.write("Puedes editar la tabla Consolidado de manera interactiva utilizando la funcionalidad de Mito.")

    # Ruta del archivo y hoja de Excel
    file_path = "BDD_Ajuste.xlsx"
    sheet_name = "Consolidado"

    try:
        # Cargar los datos desde el archivo Excel
        consolidado_df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"No se pudo cargar la hoja '{sheet_name}' del archivo '{file_path}'. Error: {e}")
        return

    # Mostrar la tabla interactiva con Mito
    st.subheader("Edición de datos")
    final_dfs, code = spreadsheet(consolidado_df)

    # Mostrar las tablas finales después de la edición
    st.subheader("Tablas finales después de la edición")
    st.write(final_dfs)

    # Mostrar el código generado automáticamente por Mito
    st.subheader("Código generado por Mito")
    st.code(code)

    # Botón para descargar los datos editados
    st.subheader("Descargar los datos modificados")
    if "Sheet1" in final_dfs:
        edited_df = final_dfs["Sheet1"]
        csv = edited_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name="consolidado_modificado.csv",
            mime="text/csv",
        )
    else:
        st.write("No se detectaron cambios en los datos.")

# Función principal
def main():
    # Sidebar para navegación
    st.sidebar.title("Navegación")
    main_page = st.sidebar.selectbox("Selecciona una página principal:", ("VPO", "VPD", "VPE", "VPF", "PRE", "Coordinación", "Consolidado"))
    st.title(main_page)

    # Definir los montos deseados para cada sección
    deseados = {
        "VPO": {
            "Misiones": 434707.0,
            "Consultorías": 547700.0
        },
        "VPD": {
            "Misiones": 168000.0,
            "Consultorías": 130000.0
        },
        "VPE": {
            "Misiones": 28000.0,
            "Consultorías": 179400.0
        },
        "VPF": {
            "Misiones": 138600.0,
            "Consultorías": 170000.0
        },
        "PRE": {
            "Misiones": 0.0,
            "Consultorías": 0.0
        }
    }

    # Calcular los montos deseados para PRE sumando los Totales de "Requerimiento del área"
    file_path = 'BDD_Ajuste.xlsx'
    try:
        # Calcular para Misiones PRE
        df_pre_misiones = pd.read_excel(file_path, sheet_name='Misiones_PRE')
        total_pre_misiones = df_pre_misiones['Total'].sum()
        deseados["PRE"]["Misiones"] = total_pre_misiones
    except Exception as e:
        st.warning(f"No se pudo leer la hoja 'Misiones_PRE' para establecer el monto DPP2025 de Misiones de PRE: {e}")
        deseados["PRE"]["Misiones"] = 0.0

    try:
        # Calcular para Consultorías PRE
        df_pre_consultorias = pd.read_excel(file_path, sheet_name='Consultores_PRE')
        total_pre_consultorias = df_pre_consultorias['Total'].sum()
        deseados["PRE"]["Consultorías"] = total_pre_consultorias
    except Exception as e:
        st.warning(f"No se pudo leer la hoja 'Consultores_PRE' para establecer el monto DPP2025 de Consultorías de PRE: {e}")
        deseados["PRE"]["Consultorías"] = 0.0

    # Manejo de cada página principal
    if main_page == "Consolidado":
        handle_consolidado_page()
    else:
        st.write(f"Página {main_page} aún no implementada. Selecciona Consolidado para probar Mito.")

if __name__ == "__main__":
    main()
