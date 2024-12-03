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

# Función de cálculo para VPE y PRE (Total = Suma de MONTO)
def calculate_total_vpe_pre(row):
    return round(row['Suma de MONTO'])

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
        st.warning(f"No se pudo leer la hoja 'Misiones_PRE' para establecer el monto deseado de Misiones de PRE: {e}")
        deseados["PRE"]["Misiones"] = 0.0

    try:
        # Calcular para Consultorías PRE
        df_pre_consultorias = pd.read_excel(file_path, sheet_name='Consultores_PRE')
        total_pre_consultorias = df_pre_consultorias['Total'].sum()
        deseados["PRE"]["Consultorías"] = total_pre_consultorias
    except Exception as e:
        st.warning(f"No se pudo leer la hoja 'Consultores_PRE' para establecer el monto deseado de Consultorías de PRE: {e}")
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
    elif main_page == "Consolidado":
        create_consolidado(deseados)

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

# Funciones para procesar Misiones y Consultorías
def process_misiones_page(unit, tipo, page, deseados, use_objetivo):
    file_path = 'BDD_Ajuste.xlsx'
    sheet_name = f"Misiones_{unit}"
    cache_file = f'cache/{unit}_{tipo}_DPP2025.csv'
    cache_dir = 'cache'

    # Función para procesar el DataFrame
    def process_misiones_df(df, sheet_name, unit):
        if unit == "VPE" or unit == "PRE":
            # Columnas específicas para VPE y PRE
            required_columns = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO']
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

        if unit == "VPE" or unit == "PRE":
            # Solo convertir 'Suma de MONTO' a numérico
            df['Suma de MONTO'] = pd.to_numeric(df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            df['Total'] = df['Suma de MONTO']
        else:
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
        if unit == "VPE" or unit == "PRE":
            # Columnas específicas para VPE y PRE
            required_columns = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO']
        else:
            # Columnas para otras unidades
            required_columns = ['Cargo', f"{unit}/AREA", 'Nº', 'Monto mensual', 'cantidad meses', 'Total']
        
        for col in required_columns:
            if col not in df.columns:
                st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                st.stop()

        if unit == "VPE" or unit == "PRE":
            # Solo convertir 'Suma de MONTO' a numérico
            df['Suma de MONTO'] = pd.to_numeric(df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            df['Total'] = df['Suma de MONTO']
        else:
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
    if unit == "VPE" or unit == "PRE":
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
    else:
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

def display_consultorias_requerimiento(df, unit):
    st.header(f"{unit} - Consultorías: Requerimiento del área")
    st.subheader("Tabla Completa - Consultorías")
    if unit == "VPE" or unit == "PRE":
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
    else:
        st.dataframe(
            df.style.format({
                "Nº": "{:.0f}",
                "Monto mensual": "{:,.0f}",
                "cantidad meses": "{:.0f}",
                "Total": "{:,.0f}"
            }),
            height=400
        )

def edit_misiones_dpp(df, unit, desired_total, tipo, use_objetivo):
    st.header(f"{unit} - Misiones: DPP 2025")
    st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")
    st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, groupable=True)

    if unit == "VPE" or unit == "PRE":
        # Configurar columnas para VPE y PRE Misiones
        editable_columns = ['Suma de MONTO']
        gb.configure_columns(editable_columns, editable=True, type=['numericColumn'], valueFormatter="Math.round(x).toLocaleString()")
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                return Math.round(params.data['Suma de MONTO']);
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

    if unit == "VPE" or unit == "PRE":
        # Validar columnas para VPE y PRE Misiones
        essential_cols = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO', 'Total']
    else:
        # Validar columnas para otras unidades
        essential_cols = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                          'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
        if use_objetivo:
            essential_cols.append('Objetivo')

    for col in essential_cols:
        if col not in edited_df.columns:
            st.error(f"La columna '{col}' está ausente en los datos editados.")
            st.stop()

    if unit == "VPE" or unit == "PRE":
        # Convertir 'Suma de MONTO' a numérico
        edited_df['Suma de MONTO'] = pd.to_numeric(edited_df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
        edited_df['Total'] = edited_df.apply(calculate_total_vpe_pre, axis=1)
    else:
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                           'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
        for col in numeric_columns:
            edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

        edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)

    total_sum = edited_df['Total'].sum()
    difference = desired_total - total_sum

    col1, col2 = st.columns(2)
    col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
    col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")

    save_to_cache(edited_df, unit, tipo)

    st.subheader("Descargar Tabla Modificada")
    edited_df['Total'] = edited_df['Total'].round(0)
    if unit == "VPE" or unit == "PRE":
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")
    else:
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")

def edit_consultorias_dpp(df, unit, desired_total, tipo):
    st.header(f"{unit} - Consultorías: DPP 2025")
    st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")
    st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, groupable=True)

    if unit == "VPE" or unit == "PRE":
        # Configurar columnas para VPE y PRE Consultorías
        editable_columns = ['Suma de MONTO']
        gb.configure_columns(editable_columns, editable=True, type=['numericColumn'], valueFormatter="Math.round(x).toLocaleString()")
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                return Math.round(params.data['Suma de MONTO']);
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
                    Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses']) * 1.6
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

    if unit == "VPE" or unit == "PRE":
        # Validar columnas para VPE y PRE Consultorías
        essential_cols = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO', 'Total']
    else:
        # Validar columnas para otras unidades
        essential_cols = ['Cargo', f"{unit}/AREA", 'Nº', 'Monto mensual', 'cantidad meses', 'Total']

    for col in essential_cols:
        if col not in edited_df.columns:
            st.error(f"La columna '{col}' está ausente en los datos editados.")
            st.stop()

    if unit == "VPE" or unit == "PRE":
        # Convertir 'Suma de MONTO' a numérico
        edited_df['Suma de MONTO'] = pd.to_numeric(edited_df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
        edited_df['Total'] = edited_df.apply(calculate_total_vpe_pre, axis=1)
    else:
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
        for col in numeric_columns:
            edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

        edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)

    total_sum = edited_df['Total'].sum()
    difference = desired_total - total_sum

    col1, col2 = st.columns(2)
    col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
    col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")

    save_to_cache(edited_df, unit, tipo)

    st.subheader("Descargar Tabla Modificada")
    edited_df['Total'] = edited_df['Total'].round(0)
    if unit == "VPE" or unit == "PRE":
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")
    else:
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")

# Funciones para mostrar y editar datos de Misiones y Consultorías
def display_misiones_requerimiento(df, unit):
    st.header(f"{unit} - Misiones: Requerimiento del área")
    st.subheader("Tabla Completa - Misiones")
    if unit == "VPE" or unit == "PRE":
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
    else:
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

def display_consultorias_requerimiento(df, unit):
    st.header(f"{unit} - Consultorías: Requerimiento del área")
    st.subheader("Tabla Completa - Consultorías")
    if unit == "VPE" or unit == "PRE":
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
    else:
        st.dataframe(
            df.style.format({
                "Nº": "{:.0f}",
                "Monto mensual": "{:,.0f}",
                "cantidad meses": "{:.0f}",
                "Total": "{:,.0f}"
            }),
            height=400
        )

# Función para editar Misiones DPP 2025
def edit_misiones_dpp(df, unit, desired_total, tipo, use_objetivo):
    st.header(f"{unit} - Misiones: DPP 2025")
    st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")
    st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, groupable=True)

    if unit == "VPE" or unit == "PRE":
        # Configurar columnas para VPE y PRE Misiones
        editable_columns = ['Suma de MONTO']
        gb.configure_columns(editable_columns, editable=True, type=['numericColumn'], valueFormatter="Math.round(x).toLocaleString()")
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                return Math.round(params.data['Suma de MONTO']);
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

    if unit == "VPE" or unit == "PRE":
        # Validar columnas para VPE y PRE Misiones
        essential_cols = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO', 'Total']
    else:
        # Validar columnas para otras unidades
        essential_cols = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                          'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
        if use_objetivo:
            essential_cols.append('Objetivo')

    for col in essential_cols:
        if col not in edited_df.columns:
            st.error(f"La columna '{col}' está ausente en los datos editados.")
            st.stop()

    if unit == "VPE" or unit == "PRE":
        # Convertir 'Suma de MONTO' a numérico
        edited_df['Suma de MONTO'] = pd.to_numeric(edited_df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
        edited_df['Total'] = edited_df.apply(calculate_total_vpe_pre, axis=1)
    else:
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                           'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
        for col in numeric_columns:
            edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

        edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)

    total_sum = edited_df['Total'].sum()
    difference = desired_total - total_sum

    col1, col2 = st.columns(2)
    col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
    col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")

    save_to_cache(edited_df, unit, tipo)

    st.subheader("Descargar Tabla Modificada")
    edited_df['Total'] = edited_df['Total'].round(0)
    if unit == "VPE" or unit == "PRE":
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")
    else:
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")

def edit_consultorias_dpp(df, unit, desired_total, tipo):
    st.header(f"{unit} - Consultorías: DPP 2025")
    st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")
    st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, groupable=True)

    if unit == "VPE" or unit == "PRE":
        # Configurar columnas para VPE y PRE Consultorías
        editable_columns = ['Suma de MONTO']
        gb.configure_columns(editable_columns, editable=True, type=['numericColumn'], valueFormatter="Math.round(x).toLocaleString()")
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                return Math.round(params.data['Suma de MONTO']);
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
                    Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses']) * 1.6
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

    if unit == "VPE" or unit == "PRE":
        # Validar columnas para VPE y PRE Consultorías
        essential_cols = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO', 'Total']
    else:
        # Validar columnas para otras unidades
        essential_cols = ['Cargo', f"{unit}/AREA", 'Nº', 'Monto mensual', 'cantidad meses', 'Total']

    for col in essential_cols:
        if col not in edited_df.columns:
            st.error(f"La columna '{col}' está ausente en los datos editados.")
            st.stop()

    if unit == "VPE" or unit == "PRE":
        # Convertir 'Suma de MONTO' a numérico
        edited_df['Suma de MONTO'] = pd.to_numeric(edited_df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
        edited_df['Total'] = edited_df.apply(calculate_total_vpe_pre, axis=1)
    else:
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
        for col in numeric_columns:
            edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

        edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)

    total_sum = edited_df['Total'].sum()
    difference = desired_total - total_sum

    col1, col2 = st.columns(2)
    col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
    col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")

    save_to_cache(edited_df, unit, tipo)

    st.subheader("Descargar Tabla Modificada")
    edited_df['Total'] = edited_df['Total'].round(0)
    if unit == "VPE" or unit == "PRE":
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")
    else:
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")

if __name__ == "__main__":
    main()
