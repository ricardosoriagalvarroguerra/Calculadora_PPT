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
            "Misiones": 0.0,         # Se actualizarán dinámicamente
            "Consultorías": 0.0      # Se actualizarán dinámicamente
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
    if main_page == "VPO":
        handle_vpo_page(deseados)
    elif main_page == "VPD":
        handle_vpd_page(deseados)
    elif main_page == "VPE":
        handle_vpe_page(deseados)
    elif main_page == "VPF":
        handle_vpf_page(deseados)
    elif main_page == "PRE":
        handle_pre_page(deseados)
    elif main_page == "Coordinación":
        create_consolidado(deseados)
    elif main_page == "Consolidado":
        handle_consolidado_page()

# Funciones específicas para cada unidad
def handle_vpo_page(deseados):
    # Seleccionar Vista
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPO_view")

    if view == "Misiones":
        page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPO_Misiones_page")
        process_misiones_page("VPO", "Misiones", page, deseados, use_objetivo=True)
    elif view == "Consultorías":
        page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPO_Consultorias_page")
        process_consultorias_page("VPO", "Consultorías", page, deseados)

def handle_vpd_page(deseados):
    # Seleccionar Vista
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPD_view")

    if view == "Misiones":
        page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPD_Misiones_page")
        process_misiones_page("VPD", "Misiones", page, deseados, use_objetivo=False)
    elif view == "Consultorías":
        page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPD_Consultorias_page")
        process_consultorias_page("VPD", "Consultorías", page, deseados)

def handle_vpf_page(deseados):
    # Seleccionar Vista
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPF_view")

    if view == "Misiones":
        page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPF_Misiones_page")
        process_misiones_page("VPF", "Misiones", page, deseados, use_objetivo=False)
    elif view == "Consultorías":
        page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPF_Consultorias_page")
        process_consultorias_page("VPF", "Consultorías", page, deseados)

def handle_pre_page(deseados):
    # Seleccionar Vista
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="PRE_view")

    if view == "Misiones":
        page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="PRE_Misiones_page")
        process_misiones_page("PRE", "Misiones", page, deseados, use_objetivo=False)
    elif view == "Consultorías":
        page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="PRE_Consultorias_page")
        process_consultorias_page("PRE", "Consultorías", page, deseados)

def handle_consolidado_page():
    st.header("Resumen por Unidad Organizacional")

    # Datos para la sección Gobernanza
    gobernanza_data = {
        "Departamento": ["Asamblea de gobernadores", "Directorio Ejecutivo", "Tribunal Administrativo"],
        "Monto (USD)": [97284, 263610, 50700]
    }

    gobernanza_df = pd.DataFrame(gobernanza_data)

    # Mostrar los ítems y el total dentro de la misma sección expandible
    with st.expander("Gobernanza"):
        for index, row in gobernanza_df.iterrows():
            st.markdown(f"**{row['Departamento']}:** {row['Monto (USD)']:,.0f} USD")
        st.markdown("---")  # Línea divisoria
        total_presupuesto_gobernanza = gobernanza_df['Monto (USD)'].sum()
        st.markdown(f"**Total Presupuesto Gobernanza:** {total_presupuesto_gobernanza:,.0f} USD")

    # Datos para la sección Presidencia Ejecutiva
    presidencia_ejecutiva_data = {
        "Concepto": [
            "Posiciones",
            "Misiones de Servicio",
            "Servicios Profesionales a Término",
            "Gasto en Personal",
            "Programa Comunicaciones",
            "Gastos Administrativos",
            "Gastos Totales"
        ],
        "Monto (USD)": [
            15,              # Posiciones (count)
            80168,           # Misiones de Servicio
            338372,          # Servicios Profesionales a Término
            2431332,         # Gasto en Personal
            408174,          # Programa Comunicaciones
            8500,            # Gastos Administrativos
            416674           # Gastos Totales
        ]
    }

    presidencia_ejecutiva_df = pd.DataFrame(presidencia_ejecutiva_data)

    # Mostrar los ítems y el total dentro de la misma sección expandible
    with st.expander("Presidencia Ejecutiva"):
        for index, row in presidencia_ejecutiva_df.iterrows():
            if row['Concepto'] == "Posiciones":
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']}")
            else:
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']:,.0f} USD")
        st.markdown("---")  # Línea divisoria
        # Calcular Total Presupuesto excluyendo "Gastos Totales" y "Posiciones"
        total_presupuesto_presidencia = presidencia_ejecutiva_df[
            ~presidencia_ejecutiva_df['Concepto'].isin(["Gastos Totales", "Posiciones"])
        ]['Monto (USD)'].sum()
        st.markdown(f"**Total Presupuesto Presidencia Ejecutiva:** {total_presupuesto_presidencia:,.0f} USD")

    # Datos para la sección Vicepresidencia Ejecutiva
    vicepresidencia_ejecutiva_data = {
        "Concepto": [
            "Posiciones",
            "Misiones de Servicio",
            "Servicios Profesionales a Término",
            "Gastos en Personal",
            "Programa de Comunicaciones",
            "Gastos Administrativos",
            "Gastos Totales"
        ],
        "Monto (USD)": [
            21,              # Posiciones (count)
            28244,           # Misiones de Servicio
            179466,          # Servicios Profesionales a Término
            2450804,         # Gastos en Personal
            5000,            # Programa de Comunicaciones
            1037395,         # Gastos Administrativos
            1042395          # Gastos Totales
        ]
    }

    vicepresidencia_ejecutiva_df = pd.DataFrame(vicepresidencia_ejecutiva_data)

    # Mostrar los ítems y el total dentro de la misma sección expandible
    with st.expander("Vicepresidencia Ejecutiva"):
        for index, row in vicepresidencia_ejecutiva_df.iterrows():
            if row['Concepto'] == "Posiciones":
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']}")
            else:
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']:,.0f} USD")
        st.markdown("---")  # Línea divisoria
        # Calcular Total Presupuesto excluyendo "Gastos Totales" y "Posiciones"
        total_presupuesto_vicepresidencia = vicepresidencia_ejecutiva_df[
            ~vicepresidencia_ejecutiva_df['Concepto'].isin(["Gastos Totales", "Posiciones"])
        ]['Monto (USD)'].sum()
        st.markdown(f"**Total Presupuesto Vicepresidencia Ejecutiva:** {total_presupuesto_vicepresidencia:,.0f} USD")

    # Datos para la sección Vicepresidencia de Desarrollo Estratégico
    vicepresidencia_de_desarrollo_estrategico_data = {
        "Concepto": [
            "Posiciones",
            "Misiones de Servicio",
            "Servicios Profesionales a Término",
            "Gastos en Personal",
            "Programa de Comunicaciones",
            "Total de Gastos"
        ],
        "Monto (USD)": [
            10,              # Posiciones (count)
            203960,          # Misiones de Servicio
            323160,          # Servicios Profesionales a Término
            1636433,         # Gastos en Personal
            13600,           # Programa de Comunicaciones
            677800           # Total de Gastos
        ]
    }

    vicepresidencia_de_desarrollo_estrategico_df = pd.DataFrame(vicepresidencia_de_desarrollo_estrategico_data)

    # Mostrar los ítems y el total dentro de la misma sección expandible
    with st.expander("Vicepresidencia de Desarrollo Estratégico"):
        for index, row in vicepresidencia_de_desarrollo_estrategico_df.iterrows():
            if row['Concepto'] == "Posiciones":
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']}")
            else:
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']:,.0f} USD")
        st.markdown("---")  # Línea divisoria
        # Mostrar Total Presupuesto fuera de la tabla
        total_presupuesto_de_desarrollo = 2177163  # Valor proporcionado por el usuario
        st.markdown(f"**Total Presupuesto Vicepresidencia de Desarrollo Estratégico:** {total_presupuesto_de_desarrollo:,.0f} USD")

    # Datos para la sección Vicepresidencia de Operaciones y Países
    vicepresidencia_operaciones_paises_data = {
        "Concepto": [
            "Posiciones",
            "Misiones de Servicio",
            "Servicios Profesionales a Término",
            "Gastos en Personal",
            "Programa de Comunicaciones",
            "Gastos Administrativos",
            "Total de Gastos"
        ],
        "Monto (USD)": [
            33,              # Posiciones (count)
            482865,          # Misiones de Servicio
            580860,          # Servicios Profesionales a Término
            4686208,         # Gastos en Personal
            62200,           # Programa de Comunicaciones
            615600,          # Gastos Administrativos
            677800           # Total de Gastos
        ]
    }

    vicepresidencia_operaciones_paises_df = pd.DataFrame(vicepresidencia_operaciones_paises_data)

    # Mostrar los ítems y el total dentro de la misma sección expandible
    with st.expander("Vicepresidencia de Operaciones y Países"):
        for index, row in vicepresidencia_operaciones_paises_df.iterrows():
            if row['Concepto'] == "Posiciones":
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']}")
            else:
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']:,.0f} USD")
        st.markdown("---")  # Línea divisoria
        # Mostrar Total Presupuesto fuera de la tabla
        total_presupuesto_operaciones_paises = 6862440  # Valor proporcionado por el usuario
        st.markdown(f"**Total Presupuesto Vicepresidencia de Operaciones y Países:** {total_presupuesto_operaciones_paises:,.0f} USD")

    # Datos para la sección Vicepresidencia de Finanzas
    vicepresidencia_finanzas_data = {
        "Concepto": [
            "Posiciones",
            "Misiones de Servicio",
            "Servicios Profesionales a Término",
            "Gastos en Personal",
            "Gastos Administrativos"
        ],
        "Monto (USD)": [
            17,              # Posiciones (count)
            179560,          # Misiones de Servicio
            258450,          # Servicios Profesionales a Término
            2329964,         # Gastos en Personal
            731500           # Gastos Administrativos
        ]
    }

    vicepresidencia_finanzas_df = pd.DataFrame(vicepresidencia_finanzas_data)

    # Mostrar los ítems y el total dentro de la misma sección expandible
    with st.expander("Vicepresidencia de Finanzas"):
        for index, row in vicepresidencia_finanzas_df.iterrows():
            if row['Concepto'] == "Posiciones":
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']}")
            else:
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']:,.0f} USD")
        st.markdown("---")  # Línea divisoria
        # Mostrar Total Presupuesto fuera de la tabla
        total_presupuesto_finanzas = 3499504  # Valor proporcionado por el usuario
        st.markdown(f"**Total Presupuesto Vicepresidencia de Finanzas:** {total_presupuesto_finanzas:,.0f} USD")

    # Datos para la sección Total Presupuestado 2025
    total_presupuestado_2025_data = {
        "Concepto": [
            "Posiciones",
            "Gobernanza Institucional",
            "Misiones de Servicio",
            "Servicios Profesionales a Término",
            "Gastos en Personal",
            "Programa de Comunicaciones",
            "Gastos Administrativos",
            "Total Gastos",
            "Total Presupuesto 2025"
        ],
        "Monto (USD)": [
            96,              # Posiciones (count)
            411594,          # Gobernanza Institucional
            974797,          # Misiones de Servicio
            1680318,         # Servicios Profesionales a Término
            13534751,        # Gastos en Personal
            489000,          # Programa de Comunicaciones
            2392995,         # Gastos Administrativos
            2881969,         # Total Gastos
            19483429         # Total Presupuesto 2025
        ]
    }

    total_presupuestado_2025_df = pd.DataFrame(total_presupuestado_2025_data)

    # Mostrar los ítems y el total dentro de la misma sección expandible
    with st.expander("Total Presupuestado 2025"):
        for index, row in total_presupuestado_2025_df.iterrows():
            if row['Concepto'] == "Posiciones":
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']}")
            elif row['Concepto'] == "Total Presupuesto 2025":
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']:,.0f} USD")
            else:
                st.markdown(f"**{row['Concepto']}:** {row['Monto (USD)']:,.0f} USD")
        st.markdown("---")  # Línea divisoria
        # Mostrar Total Presupuesto 2025 fuera de la tabla (ya incluido en la tabla)
        # Pero para mantener la consistencia, no es necesario duplicarlo
        # Puedes comentar o eliminar la siguiente línea si prefieres
        # total_presupuesto_2025 = 19483429  # Valor proporcionado por el usuario
        # st.markdown(f"**Total Presupuesto 2025:** {total_presupuesto_2025:,.0f} USD")

# Funciones específicas para cada unidad
def process_misiones_page(unit, tipo, page, deseados, use_objetivo):
    file_path = 'BDD_Ajuste.xlsx'
    sheet_name = f"Misiones_{unit}"
    cache_file = f'cache/{unit}_{tipo}_DPP2025.csv'
    cache_dir = 'cache'

    # Función para procesar el DataFrame
    def process_misiones_df(df, sheet_name, unit):
        if unit == "VPE":
            # Columnas específicas para VPE Misiones
            required_columns = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO']
        elif unit == "PRE":
            # Columnas específicas para PRE Misiones
            required_columns = ['País', 'Operación', 'PRE o VP', 'Cantidad de Funcionarios', 'Días',
                                'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total', 'Area imputacion']
        else:
            # Columnas para otras unidades
            required_columns = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                'Alojamiento', 'Per-diem y Otros', 'Movilidad']
            if use_objetivo:
                required_columns.append('Objetivo')

        for col in required_columns:
            if col not in df.columns:
                st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                st.stop()

        if unit == "VPE":
            # Para VPE, 'Suma de MONTO' ya está calculado
            df['Total'] = pd.to_numeric(df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
        elif unit == "PRE":
            # Para PRE, 'Total' ya está calculado
            df['Total'] = pd.to_numeric(df['Total'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
        else:
            # Para otras unidades, recalcular 'Total' si es necesario
            numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                               'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                else:
                    st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                    st.stop()

            if 'Total' not in df.columns or df['Total'].sum() == 0:
                df['Total'] = df.apply(calculate_total_misiones, axis=1)

        return df

    if page == "DPP 2025":
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file)
        else:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except Exception as e:
                st.error(f"Error al leer el archivo Excel: {e}")
                st.stop()
            df = process_misiones_df(df, sheet_name, unit)
    else:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            st.error(f"Error al leer el archivo Excel: {e}")
            st.stop()
        df = process_misiones_df(df, sheet_name, unit)

    if page == "Requerimiento del área":
        display_misiones_requerimiento(df, unit)
    elif page == "DPP 2025":
        desired_total = deseados[unit][tipo]
        edit_misiones_dpp(df, unit, desired_total, tipo, use_objetivo)

def process_consultorias_page(unit, tipo, page, deseados):
    file_path = 'BDD_Ajuste.xlsx'
    sheet_name = f"Consultores_{unit}"
    cache_file = f'cache/{unit}_{tipo}_DPP2025.csv'
    cache_dir = 'cache'

    # Función para procesar el DataFrame
    def process_consultorias_df(df, sheet_name, unit):
        if unit == "VPE":
            # Columnas específicas para VPE Consultorías
            required_columns = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO']
        elif unit == "PRE":
            # Columnas específicas para PRE Consultorías
            required_columns = ['Cargo', 'PRE/AREA', 'Nº', 'Monto mensual', 'cantidad meses', 'Total', 'Area imputacion']
        elif unit == "VPO":
            # Columnas específicas para VPO Consultorías
            required_columns = ['Cargo', 'Nº', 'Monto mensual', 'cantidad meses', 'Total', 'Observaciones', 'Objetivo', 'tipo']
        else:
            # Columnas para otras unidades
            required_columns = ['Cargo', f"{unit}/AREA", 'Nº', 'Monto mensual', 'cantidad meses', 'Total']

        for col in required_columns:
            if col not in df.columns:
                st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                st.stop()

        if unit == "VPE":
            # Para VPE, 'Suma de MONTO' ya está calculado
            df['Total'] = pd.to_numeric(df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
        elif unit == "PRE":
            # Para PRE, 'Total' ya está calculado
            df['Total'] = pd.to_numeric(df['Total'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
        elif unit == "VPO":
            # Para VPO Consultorías, 'Total' ya está calculado o debe ser recalculado
            if 'Total' not in df.columns or df['Total'].sum() == 0:
                df['Total'] = df.apply(calculate_total_consultorias, axis=1)
        else:
            # Para otras unidades, recalcular 'Total' si es necesario
            numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
                else:
                    st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                    st.stop()

            if 'Total' not in df.columns or df['Total'].sum() == 0:
                df['Total'] = df.apply(calculate_total_consultorias, axis=1)

        return df

    if page == "DPP 2025":
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file)
        else:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except Exception as e:
                st.error(f"Error al leer el archivo Excel: {e}")
                st.stop()
            df = process_consultorias_df(df, sheet_name, unit)
    else:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            st.error(f"Error al leer el archivo Excel: {e}")
            st.stop()
        df = process_consultorias_df(df, sheet_name, unit)

    if page == "Requerimiento del área":
        display_consultorias_requerimiento(df, unit)
    elif page == "DPP 2025":
        desired_total = deseados[unit][tipo]
        edit_consultorias_dpp(df, unit, desired_total, tipo)

# Funciones para mostrar y editar datos de Misiones y Consultorías
def display_misiones_requerimiento(df, unit):
    st.header(f"{unit} - Misiones: Requerimiento del área")
    st.subheader("Tabla Completa - Misiones")
    if unit == "VPE":
        st.dataframe(
            df.style.format({
                "ÍTEM PRESUPUESTO": "{}",
                "OFICINA": "{}",
                "UNID. ORG.": "{}",
                "ACCIONES": "{}",
                "CATEGORÍA": "{}",
                "SUBCATEGORÍA": "{}",
                "Suma de MONTO": "{:,.0f}",
                "Total": "{:,.0f}"
            }),
            height=400
        )
    elif unit == "PRE":
        st.dataframe(
            df.style.format({
                "País": "{}",
                "Operación": "{}",
                "PRE o VP": "{}",
                "Cantidad de Funcionarios": "{:.0f}",
                "Días": "{:.0f}",
                "Costo de Pasaje": "{:,.0f}",
                "Alojamiento": "{:,.0f}",
                "Per-diem y Otros": "{:,.0f}",
                "Movilidad": "{:,.0f}",
                "Total": "{:,.0f}",
                "Area imputacion": "{}"
            }),
            height=400
        )
    else:
        st.dataframe(
            df.style.format({
                "País": "{}",
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

def display_consultorias_requerimiento(df, unit):
    st.header(f"{unit} - Consultorías: Requerimiento del área")
    st.subheader("Tabla Completa - Consultorías")
    if unit == "VPE":
        st.dataframe(
            df.style.format({
                "ÍTEM PRESUPUESTO": "{}",
                "OFICINA": "{}",
                "UNID. ORG.": "{}",
                "ACCIONES": "{}",
                "CATEGORÍA": "{}",
                "SUBCATEGORÍA": "{}",
                "Suma de MONTO": "{:,.0f}",
                "Total": "{:,.0f}"
            }),
            height=400
        )
    elif unit == "PRE":
        st.dataframe(
            df.style.format({
                "Cargo": "{}",
                "PRE/AREA": "{}",
                "Nº": "{:.0f}",
                "Monto mensual": "{:,.0f}",
                "cantidad meses": "{:.0f}",
                "Total": "{:,.0f}",
                "Area imputacion": "{}"
            }),
            height=400
        )
    elif unit == "VPO":
        st.dataframe(
            df.style.format({
                "Cargo": "{}",
                "Nº": "{:.0f}",
                "Monto mensual": "{:,.0f}",
                "cantidad meses": "{:.0f}",
                "Total": "{:,.0f}",
                "Observaciones": "{}",
                "Objetivo": "{}",
                "tipo": "{}"
            }),
            height=400
        )
    else:
        st.dataframe(
            df.style.format({
                "Cargo": "{}",
                f"{unit}/AREA": "{}",
                "Nº": "{:.0f}",
                "Monto mensual": "{:,.0f}",
                "cantidad meses": "{:.0f}",
                "Total": "{:,.0f}"
            }),
            height=400
        )

def edit_misiones_dpp(df, unit, desired_total, tipo, use_objetivo):
    st.header(f"{unit} - Misiones: DPP 2025")
    st.subheader(f"Monto DPP 2025: {desired_total:,.0f} USD")
    st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto DPP 2025.")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, groupable=True)

    if unit == "VPE":
        # Configurar columnas para VPE Misiones
        editable_columns = ['Suma de MONTO']
        gb.configure_columns(editable_columns, editable=True, type=['numericColumn'], valueFormatter="Math.round(x).toLocaleString()")
        # 'Total' ya está calculado y no editable
    elif unit == "PRE":
        # Configurar columnas para PRE Misiones
        editable_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
        for col in editable_columns:
            gb.configure_column(
                col,
                editable=True,
                type=['numericColumn'],
                valueFormatter="Math.round(x).toLocaleString()"
            )
        # Recalcular 'Total'
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                return Math.round(
                    (Number(params.data['Costo de Pasaje']) + 
                    (Number(params.data['Alojamiento']) + Number(params.data['Per-diem y Otros']) + Number(params.data['Movilidad'])) * 
                    Number(params.data['Días'])) * 
                    Number(params.data['Cantidad de Funcionarios'])
                );
            }
        """))
    else:
        # Configurar columnas para otras unidades
        numeric_columns_aggrid = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                  'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
        for col in numeric_columns_aggrid:
            gb.configure_column(
                col,
                type=['numericColumn'],
                valueFormatter="Math.round(x).toLocaleString()"
            )

        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                return Math.round(
                    (Number(params.data['Costo de Pasaje']) + 
                    (Number(params.data['Alojamiento']) + Number(params.data['Per-diem y Otros']) + Number(params.data['Movilidad'])) * 
                    Number(params.data['Días'])) * 
                    Number(params.data['Cantidad de Funcionarios'])
                );
            }
        """))

    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()

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

    edited_df = pd.DataFrame(grid_response['data'])

    if unit == "VPE":
        # Validar columnas para VPE Misiones
        essential_cols = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO', 'Total']
    elif unit == "PRE":
        # Validar columnas para PRE Misiones
        essential_cols = ['País', 'Operación', 'PRE o VP', 'Cantidad de Funcionarios', 'Días',
                          'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total', 'Area imputacion']
    else:
        # Validar columnas para otras unidades
        essential_cols = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                          'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
        if use_objetivo:
            essential_cols.append('Objetivo')

    for col in essential_cols:
        if col not in edited_df.columns:
            st.error(f"La columna '{col}' está ausente en los datos editados.")
            st.stop()

    if unit == "VPE":
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Suma de MONTO']
        for col in numeric_columns:
            if col in edited_df.columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            else:
                st.error(f"La columna '{col}' está ausente en los datos editados.")
                st.stop()
        # Recalcular 'Total'
        edited_df['Total'] = edited_df.apply(lambda row: row['Suma de MONTO'], axis=1)
    elif unit == "PRE":
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
        for col in numeric_columns:
            if col in edited_df.columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            else:
                st.error(f"La columna '{col}' está ausente en los datos editados.")
                st.stop()
        # Recalcular 'Total'
        edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)
    else:
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                           'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
        for col in numeric_columns:
            edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

        edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)

    # Calcular la suma total y la diferencia con el monto DPP 2025
    total_sum = edited_df['Total'].sum()
    difference = desired_total - total_sum

    col1, col2 = st.columns(2)
    col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
    col2.metric("Diferencia con el Monto DPP 2025 (USD)", f"{difference:,.0f}")

    save_to_cache(edited_df, unit, tipo)

    st.subheader("Descargar Tabla Modificada")
    edited_df['Total'] = edited_df['Total'].round(0)
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")

def edit_consultorias_dpp(df, unit, desired_total, tipo):
    st.header(f"{unit} - Consultorías: DPP 2025")
    st.subheader(f"Monto DPP 2025: {desired_total:,.0f} USD")
    st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto DPP 2025.")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, groupable=True)

    if unit == "VPE":
        # Configurar columnas para VPE Consultorías
        editable_columns = ['Suma de MONTO']
        gb.configure_columns(editable_columns, editable=True, type=['numericColumn'], valueFormatter="Math.round(x).toLocaleString()")
        # 'Total' ya está calculado y no editable
    elif unit == "PRE":
        # Configurar columnas para PRE Consultorías
        editable_columns = ['Nº', 'Monto mensual', 'cantidad meses']
        for col in editable_columns:
            gb.configure_column(
                col,
                editable=True,
                type=['numericColumn'],
                valueFormatter="Math.round(x).toLocaleString()"
            )
        # Recalcular 'Total'
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                return Math.round(
                    Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses'])
                );
            }
        """))
    elif unit == "VPO":
        # Configurar columnas para VPO Consultorías
        editable_columns = ['Nº', 'Monto mensual', 'cantidad meses']
        for col in editable_columns:
            gb.configure_column(
                col,
                editable=True,
                type=['numericColumn'],
                valueFormatter="Math.round(x).toLocaleString()"
            )
        # Recalcular 'Total'
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                return Math.round(
                    Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses'])
                );
            }
        """))
    else:
        # Configurar columnas para otras unidades
        numeric_columns_aggrid = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
        for col in numeric_columns_aggrid:
            gb.configure_column(
                col,
                type=['numericColumn'],
                valueFormatter="Math.round(x).toLocaleString()"
            )

        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                return Math.round(
                    Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses'])
                );
            }
        """))

    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()

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

    edited_df = pd.DataFrame(grid_response['data'])

    if unit == "VPE":
        # Validar columnas para VPE Consultorías
        essential_cols = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO', 'Total']
    elif unit == "PRE":
        # Validar columnas para PRE Consultorías
        essential_cols = ['Cargo', 'PRE/AREA', 'Nº', 'Monto mensual', 'cantidad meses', 'Total', 'Area imputacion']
    elif unit == "VPO":
        # Validar columnas para VPO Consultorías
        essential_cols = ['Cargo', 'Nº', 'Monto mensual', 'cantidad meses', 'Total', 'Observaciones', 'Objetivo', 'tipo']
    else:
        # Validar columnas para otras unidades
        essential_cols = ['Cargo', f"{unit}/AREA", 'Nº', 'Monto mensual', 'cantidad meses', 'Total']

    for col in essential_cols:
        if col not in edited_df.columns:
            st.error(f"La columna '{col}' está ausente en los datos editados.")
            st.stop()

    if unit == "VPE":
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Suma de MONTO']
        for col in numeric_columns:
            if col in edited_df.columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            else:
                st.error(f"La columna '{col}' está ausente en los datos editados.")
                st.stop()
        # Recalcular 'Total'
        edited_df['Total'] = edited_df.apply(lambda row: row['Suma de MONTO'], axis=1)
    elif unit == "PRE":
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses']
        for col in numeric_columns:
            if col in edited_df.columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            else:
                st.error(f"La columna '{col}' está ausente en los datos editados.")
                st.stop()
        # Recalcular 'Total'
        edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)
    else:
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
        for col in numeric_columns:
            edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

        edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)

    # Calcular la suma total y la diferencia con el monto DPP 2025
    total_sum = edited_df['Total'].sum()
    difference = desired_total - total_sum

    col1, col2 = st.columns(2)
    col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
    col2.metric("Diferencia con el Monto DPP 2025 (USD)", f"{difference:,.0f}")

    save_to_cache(edited_df, unit, tipo)

    st.subheader("Descargar Tabla Modificada")
    edited_df['Total'] = edited_df['Total'].round(0)
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")

if __name__ == "__main__":
    main()
