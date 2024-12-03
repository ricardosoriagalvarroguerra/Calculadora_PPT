import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
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
                row[f"{tipo} - Ajuste"] = ajuste
                row[f"{tipo} - Deseado"] = deseado
            else:
                deseado = deseados[unidad][tipo]
                row[f"{tipo} - Actual"] = 0
                row[f"{tipo} - Ajuste"] = deseado
                row[f"{tipo} - Deseado"] = deseado
            if tipo == 'Misiones':
                data_misiones.append(row)
            else:
                data_consultorias.append(row)

    consolidado_misiones_df = pd.DataFrame(data_misiones)
    consolidado_consultorias_df = pd.DataFrame(data_consultorias)

    def highlight_zero(val):
        color = 'background-color: #90ee90' if val == 0 else ''
        return color

    styled_misiones_df = consolidado_misiones_df.style.applymap(highlight_zero, subset=[f"Misiones - Ajuste"])
    styled_misiones_df = styled_misiones_df.format(
        "{:,.0f}", 
        subset=[
            "Misiones - Actual",
            "Misiones - Ajuste",
            "Misiones - Deseado"
        ]
    )

    styled_consultorias_df = consolidado_consultorias_df.style.applymap(highlight_zero, subset=[f"Consultorías - Ajuste"])
    styled_consultorias_df = styled_consultorias_df.format(
        "{:,.0f}", 
        subset=[
            "Consultorías - Actual",
            "Consultorías - Ajuste",
            "Consultorías - Deseado"
        ]
    )

    st.subheader("Misiones")
    st.dataframe(styled_misiones_df)

    st.subheader("Consultorías")
    st.dataframe(styled_consultorias_df)

# Función auxiliar para crear gráficos de dona
def crear_dona(df, nombres, valores, titulo, color_map, hole=0.5, height=300, margin_l=50):
    fig = px.pie(
        df,
        names=nombres,
        values=valores,
        hole=hole,
        title=titulo,
        color=nombres,
        color_discrete_map=color_map
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=-0.1
        ),
        margin=dict(t=60, b=20, l=margin_l, r=20),
        height=height
    )
    return fig

# Función principal
def main():
    # Sidebar para navegación
    st.sidebar.title("Navegación")
    main_page = st.sidebar.selectbox("Selecciona una página principal:", ("VPO", "VPD", "VPE", "VPF", "PRE", "Consolidado"))
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
            "Misiones": 28200.0,
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

    # Manejo de cada página principal
    if main_page == "VPO":
        handle_vpo_page(deseados)
    elif main_page == "VPD":
        handle_vpd_page(deseados)
    elif main_page == "VPE":
        handle_vpe_page(deseados)  # Integración de VPE
    elif main_page == "VPF":
        handle_vpf_page(deseados)
    elif main_page == "PRE":
        st.header("PRE - Página en Desarrollo")
        st.write("Aquí puedes agregar las funcionalidades específicas para PRE.")
    elif main_page == "Consolidado":
        create_consolidado(deseados)

# Función para manejar la página de VPO
def handle_vpo_page(deseados):
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPO_view")
    if view == "Misiones":
        process_misiones_page("VPO", "Misiones", "DPP 2025", deseados, use_objetivo=True)
    elif view == "Consultorías":
        st.header("VPO - Consultorías: Página en Desarrollo")
        st.write("Funcionalidades específicas para Consultorías VPO.")

# Función para manejar la página de VPD
def handle_vpd_page(deseados):
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPD_view")
    if view == "Misiones":
        process_misiones_page("VPD", "Misiones", "DPP 2025", deseados, use_objetivo=False)
    elif view == "Consultorías":
        process_consultorias_page("VPD", "Consultorías", "DPP 2025", deseados)

# Función para manejar la página de VPE
def handle_vpe_page(deseados):
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPE_view")
    if view == "Misiones":
        process_misiones_page("VPE", "Misiones", "DPP 2025", deseados, use_objetivo=False)
    elif view == "Consultorías":
        process_consultorias_page("VPE", "Consultorías", "DPP 2025", deseados)

# Función para manejar la página de VPF
def handle_vpf_page(deseados):
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPF_view")
    if view == "Misiones":
        process_misiones_page("VPF", "Misiones", "DPP 2025", deseados, use_objetivo=False)
    elif view == "Consultorías":
        process_consultorias_page("VPF", "Consultorías", "DPP 2025", deseados)

# Funciones para procesar y mostrar datos de Misiones y Consultorías
def process_misiones_page(unit, tipo, page, deseados, use_objetivo):
    st.header(f"{unit} - Misiones")
    st.write("Funcionalidades completas para Misiones.")

def process_consultorias_page(unit, tipo, page, deseados):
    st.header(f"{unit} - Consultorías")
    st.write("Funcionalidades completas para Consultorías.")

if __name__ == "__main__":
    main()
