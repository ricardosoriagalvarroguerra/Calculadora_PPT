import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
import plotly.express as px
import os

# Funciones de cálculo con fórmulas corregidas
def calculate_total_misiones(row):
    return round(
        (row['Costo de Pasaje'] + (row['Alojamiento'] + row['Per-diem y Otros'] + row['Movilidad']) * row['Días']) * row['Cantidad de Funcionarios'],
        2
    )

def calculate_total_consultorias(row):
    return round(row['Nº'] * row['Monto mensual'] * row['cantidad meses'], 2)

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

# Función para manejar la página de Consolidado
def handle_consolidado_page():
    st.header("Consolidado")
    
    file_path = 'BDD_Ajuste.xlsx'  # Asegúrate de que la ruta al archivo sea correcta

    try:
        # Leer la hoja 'Consolidado' del archivo Excel
        df_consolidado = pd.read_excel(file_path, sheet_name='Consolidado')
        
        # Redondear todas las columnas numéricas a dos decimales
        numeric_cols_consolidado = df_consolidado.select_dtypes(include=['float', 'int']).columns.tolist()
        df_consolidado[numeric_cols_consolidado] = df_consolidado[numeric_cols_consolidado].round(2)

        # Configurar opciones para AgGrid con formateo de números a dos decimales y autosize
        gb = GridOptionsBuilder.from_dataframe(df_consolidado)
        gb.configure_default_column(editable=False, sortable=True, filter=True, type=["numericColumn"])
        
        for col in numeric_cols_consolidado:
            gb.configure_column(
                col,
                type=["numericColumn"],
                valueFormatter=f'function(params) {{ return params.value.toFixed(2); }}'
            )
        
        gb.configure_pagination(paginationAutoPageSize=True)  # Habilitar paginación
        gb.configure_side_bar()  # Habilitar barra lateral en la tabla
        gb.configure_grid_options(domLayout='autoHeight', suppressColumnVirtualisation=True)

        grid_options = gb.build()

        # Mostrar la tabla usando AgGrid para una mejor interactividad
        AgGrid(
            df_consolidado,
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED,
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True,
            height=500,
            width='100%',
            theme='alpine'
        )

        st.markdown("### Consolidado V2")
        
        # Leer la segunda tabla 'consolidadoV2'
        df_consolidadoV2 = pd.read_excel(file_path, sheet_name='consolidadoV2')

        # Redondear todas las columnas numéricas a dos decimales
        numeric_cols_consolidadoV2 = df_consolidadoV2.select_dtypes(include=['float', 'int']).columns.tolist()
        df_consolidadoV2[numeric_cols_consolidadoV2] = df_consolidadoV2[numeric_cols_consolidadoV2].round(2)

        # Configurar opciones para AgGrid con formateo de números a dos decimales y autosize
        gb_v2 = GridOptionsBuilder.from_dataframe(df_consolidadoV2)
        gb_v2.configure_default_column(editable=False, sortable=True, filter=True, type=["numericColumn"])
        
        for col in numeric_cols_consolidadoV2:
            gb_v2.configure_column(
                col,
                type=["numericColumn"],
                valueFormatter=f'function(params) {{ return params.value.toFixed(2); }}'
            )
        
        gb_v2.configure_pagination(paginationAutoPageSize=True)  # Habilitar paginación
        gb_v2.configure_side_bar()  # Habilitar barra lateral en la tabla
        gb_v2.configure_grid_options(domLayout='autoHeight', suppressColumnVirtualisation=True)

        grid_options_v2 = gb_v2.build()

        # Mostrar la segunda tabla usando AgGrid
        AgGrid(
            df_consolidadoV2,
            gridOptions=grid_options_v2,
            data_return_mode=DataReturnMode.FILTERED,
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True,
            height=500,
            width='100%',
            theme='alpine'
        )

    except Exception as e:
        st.error(f"Error al leer las hojas 'Consolidado' o 'consolidadoV2': {e}")

# Función para manejar la página de Coordinación
def handle_coordinacion_page():
    st.header("Coordinación")
    
    # Suponiendo que 'Coordinacion' está en una hoja llamada 'Coordinacion' en el mismo archivo Excel
    file_path = 'BDD_Ajuste.xlsx'  # Asegúrate de que la ruta al archivo sea correcta

    try:
        # Leer la hoja 'Coordinacion' del archivo Excel
        df_coordinacion = pd.read_excel(file_path, sheet_name='Coordinacion')
        
        # Redondear todas las columnas numéricas a dos decimales
        numeric_cols_coordinacion = df_coordinacion.select_dtypes(include=['float', 'int']).columns.tolist()
        df_coordinacion[numeric_cols_coordinacion] = df_coordinacion[numeric_cols_coordinacion].round(2)

        # Configurar opciones para AgGrid con formateo de números a dos decimales y autosize
        gb = GridOptionsBuilder.from_dataframe(df_coordinacion)
        gb.configure_default_column(editable=False, sortable=True, filter=True, type=["numericColumn"])
        
        for col in numeric_cols_coordinacion:
            gb.configure_column(
                col,
                type=["numericColumn"],
                valueFormatter=f'function(params) {{ return params.value.toFixed(2); }}'
            )
        
        gb.configure_pagination(paginationAutoPageSize=True)  # Habilitar paginación
        gb.configure_side_bar()  # Habilitar barra lateral en la tabla
        gb.configure_grid_options(domLayout='autoHeight', suppressColumnVirtualisation=True)

        grid_options = gb.build()

        # Mostrar la tabla usando AgGrid para una mejor interactividad
        AgGrid(
            df_coordinacion,
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED,
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True,
            height=500,
            width='100%',
            theme='alpine'
        )

    except Exception as e:
        st.error(f"Error al leer la hoja 'Coordinacion': {e}")

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
                row[f"{tipo} - Actual"] = round(actual, 2)
                row[f"{tipo} - Monto DPP 2025"] = round(deseado, 2)
                row[f"{tipo} - Ajuste"] = round(ajuste, 2)
            else:
                deseado = deseados[unidad][tipo]
                row[f"{tipo} - Actual"] = 0.00
                row[f"{tipo} - Monto DPP 2025"] = round(deseado, 2)
                row[f"{tipo} - Ajuste"] = round(deseado, 2)
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
        "{:,.2f}", 
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
        "{:,.2f}", 
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
    main_page = st.sidebar.selectbox(
        "Selecciona una página principal:",
        ("VPO", "VPD", "VPE", "VPF", "PRE", "Coordinación", "Consolidado")
    )
    st.title(main_page)

    # Definir los montos deseados para cada sección
    deseados = {
        "VPO": {
            "Misiones": 434707.00,
            "Consultorías": 547700.00
        },
        "VPD": {
            "Misiones": 168000.00,
            "Consultorías": 130000.00
        },
        "VPE": {
            "Misiones": 28000.00,
            "Consultorías": 179400.00
        },
        "VPF": {
            "Misiones": 138600.00,
            "Consultorías": 170000.00
        },
        "PRE": {
            "Misiones": 0.00,         # Se actualizarán dinámicamente
            "Consultorías": 0.00      # Se actualizarán dinámicamente
        }
    }

    # Calcular los montos deseados para PRE sumando los Totales de "Requerimiento del área"
    file_path = 'BDD_Ajuste.xlsx'
    try:
        # Calcular para Misiones PRE
        df_pre_misiones = pd.read_excel(file_path, sheet_name='Misiones_PRE')
        total_pre_misiones = df_pre_misiones['Total'].sum()
        deseados["PRE"]["Misiones"] = round(total_pre_misiones, 2)
    except Exception as e:
        st.warning(f"No se pudo leer la hoja 'Misiones_PRE' para establecer el monto DPP2025 de Misiones de PRE: {e}")
        deseados["PRE"]["Misiones"] = 0.00

    try:
        # Calcular para Consultorías PRE
        df_pre_consultorias = pd.read_excel(file_path, sheet_name='Consultores_PRE')
        total_pre_consultorias = df_pre_consultorias['Total'].sum()
        deseados["PRE"]["Consultorías"] = round(total_pre_consultorias, 2)
    except Exception as e:
        st.warning(f"No se pudo leer la hoja 'Consultores_PRE' para establecer el monto DPP2025 de Consultorías de PRE: {e}")
        deseados["PRE"]["Consultorías"] = 0.00

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
        handle_coordinacion_page()
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

# Funciones para procesar Misiones y Consultorías
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
            df['Total'] = pd.to_numeric(df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)
        elif unit == "PRE":
            # Para PRE, 'Total' ya está calculado
            df['Total'] = pd.to_numeric(df['Total'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)
        else:
            # Para otras unidades, recalcular 'Total' si es necesario
            numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                               'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)
                else:
                    st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                    st.stop()

            if 'Total' not in df.columns or df['Total'].sum() == 0:
                df['Total'] = df.apply(calculate_total_misiones, axis=1)

        return df

    if page == "DPP 2025":
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file)
            # Asegurarse de que los valores numéricos estén redondeados a dos decimales
            numeric_cols = df.select_dtypes(include=['float', 'int']).columns.tolist()
            df[numeric_cols] = df[numeric_cols].round(2)
        else:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except Exception as e:
                st.error(f"Error al leer el archivo Excel: {e}")
                st.stop()
            df = process_misiones_df(df, sheet_name, unit)
            # Guardar en cache
            save_to_cache(df, unit, tipo)
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
            df['Total'] = pd.to_numeric(df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)
        elif unit == "PRE":
            # Para PRE, 'Total' ya está calculado
            df['Total'] = pd.to_numeric(df['Total'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)
        elif unit == "VPO":
            # Para VPO Consultorías, 'Total' ya está calculado o debe ser recalculado
            if 'Total' not in df.columns or df['Total'].sum() == 0:
                df['Total'] = df.apply(calculate_total_consultorias, axis=1).round(2)
        else:
            # Para otras unidades, recalcular 'Total' si es necesario
            numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)
                else:
                    st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                    st.stop()

            if 'Total' not in df.columns or df['Total'].sum() == 0:
                df['Total'] = df.apply(calculate_total_consultorias, axis=1).round(2)

        return df

    if page == "DPP 2025":
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file)
            # Asegurarse de que los valores numéricos estén redondeados a dos decimales
            numeric_cols = df.select_dtypes(include=['float', 'int']).columns.tolist()
            df[numeric_cols] = df[numeric_cols].round(2)
        else:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except Exception as e:
                st.error(f"Error al leer el archivo Excel: {e}")
                st.stop()
            df = process_consultorias_df(df, sheet_name, unit)
            # Guardar en cache
            save_to_cache(df, unit, tipo)
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
                "Suma de MONTO": "{:,.2f}",
                "Total": "{:,.2f}"
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
                "Costo de Pasaje": "{:,.2f}",
                "Alojamiento": "{:,.2f}",
                "Per-diem y Otros": "{:,.2f}",
                "Movilidad": "{:,.2f}",
                "Total": "{:,.2f}",
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
                "Costo de Pasaje": "{:,.2f}",
                "Alojamiento": "{:,.2f}",
                "Per-diem y Otros": "{:,.2f}",
                "Movilidad": "{:,.2f}",
                "Total": "{:,.2f}"
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
                "Suma de MONTO": "{:,.2f}",
                "Total": "{:,.2f}"
            }),
            height=400
        )
    elif unit == "PRE":
        st.dataframe(
            df.style.format({
                "Cargo": "{}",
                "PRE/AREA": "{}",
                "Nº": "{:.0f}",
                "Monto mensual": "{:,.2f}",
                "cantidad meses": "{:.0f}",
                "Total": "{:,.2f}",
                "Area imputacion": "{}"
            }),
            height=400
        )
    elif unit == "VPO":
        st.dataframe(
            df.style.format({
                "Cargo": "{}",
                "Nº": "{:.0f}",
                "Monto mensual": "{:,.2f}",
                "cantidad meses": "{:.0f}",
                "Total": "{:,.2f}",
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
                "Monto mensual": "{:,.2f}",
                "cantidad meses": "{:.0f}",
                "Total": "{:,.2f}"
            }),
            height=400
        )

def edit_misiones_dpp(df, unit, desired_total, tipo, use_objetivo):
    st.header(f"{unit} - Misiones: DPP 2025")
    st.subheader(f"Monto DPP 2025: {desired_total:,.2f} USD")
    st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto DPP 2025.")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, groupable=True)

    if unit == "VPE":
        # Configurar columnas para VPE Misiones
        editable_columns = ['Suma de MONTO']
        gb.configure_columns(editable_columns, editable=True, type=['numericColumn'], valueFormatter="params.value.toFixed(2)")
        # 'Total' ya está calculado y no editable
    elif unit == "PRE":
        # Configurar columnas para PRE Misiones
        editable_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
        for col in editable_columns:
            gb.configure_column(
                col,
                editable=True,
                type=['numericColumn'],
                valueFormatter="params.value.toFixed(2)"
            )
        # Recalcular 'Total'
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                let total = (Number(params.data['Costo de Pasaje']) + 
                             (Number(params.data['Alojamiento']) + Number(params.data['Per-diem y Otros']) + Number(params.data['Movilidad'])) * 
                             Number(params.data['Días'])) * 
                             Number(params.data['Cantidad de Funcionarios']);
                return total.toFixed(2);
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
                valueFormatter="params.value.toFixed(2)"
            )

        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                let total = (Number(params.data['Costo de Pasaje']) + 
                             (Number(params.data['Alojamiento']) + Number(params.data['Per-diem y Otros']) + Number(params.data['Movilidad'])) * 
                             Number(params.data['Días'])) * 
                             Number(params.data['Cantidad de Funcionarios']);
                return total.toFixed(2);
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
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)
            else:
                st.error(f"La columna '{col}' está ausente en los datos editados.")
                st.stop()
        # Recalcular 'Total'
        edited_df['Total'] = edited_df.apply(lambda row: round(row['Suma de MONTO'], 2), axis=1)
    elif unit == "PRE":
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
        for col in numeric_columns:
            if col in edited_df.columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)
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
            edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)

        edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)

    # Calcular la suma total y la diferencia con el monto DPP 2025
    total_sum = edited_df['Total'].sum().round(2)
    difference = round(desired_total - total_sum, 2)

    col1, col2 = st.columns(2)
    col1.metric("Monto Actual (USD)", f"{total_sum:,.2f}")
    col2.metric("Diferencia con el Monto DPP 2025 (USD)", f"{difference:,.2f}")

    save_to_cache(edited_df, unit, tipo)

    st.subheader("Descargar Tabla Modificada")
    edited_df['Total'] = edited_df['Total'].round(2)
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")

def edit_consultorias_dpp(df, unit, desired_total, tipo):
    st.header(f"{unit} - Consultorías: DPP 2025")
    st.subheader(f"Monto DPP 2025: {desired_total:,.2f} USD")
    st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto DPP 2025.")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, groupable=True)

    if unit == "VPE":
        # Configurar columnas para VPE Consultorías
        editable_columns = ['Suma de MONTO']
        gb.configure_columns(editable_columns, editable=True, type=['numericColumn'], valueFormatter="params.value.toFixed(2)")
        # 'Total' ya está calculado y no editable
    elif unit == "PRE":
        # Configurar columnas para PRE Consultorías
        editable_columns = ['Nº', 'Monto mensual', 'cantidad meses']
        for col in editable_columns:
            gb.configure_column(
                col,
                editable=True,
                type=['numericColumn'],
                valueFormatter="params.value.toFixed(2)"
            )
        # Recalcular 'Total'
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                let total = Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses']);
                return total.toFixed(2);
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
                valueFormatter="params.value.toFixed(2)"
            )
        # Recalcular 'Total'
        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                let total = Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses']);
                return total.toFixed(2);
            }
        """))
    else:
        # Configurar columnas para otras unidades
        numeric_columns_aggrid = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
        for col in numeric_columns_aggrid:
            gb.configure_column(
                col,
                type=['numericColumn'],
                valueFormatter="params.value.toFixed(2)"
            )

        gb.configure_column('Total', editable=False, valueGetter=JsCode("""
            function(params) {
                let total = Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses']);
                return total.toFixed(2);
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
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)
            else:
                st.error(f"La columna '{col}' está ausente en los datos editados.")
                st.stop()
        # Recalcular 'Total'
        edited_df['Total'] = edited_df.apply(lambda row: round(row['Suma de MONTO'], 2), axis=1)
    elif unit == "PRE":
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses']
        for col in numeric_columns:
            if col in edited_df.columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)
            else:
                st.error(f"La columna '{col}' está ausente en los datos editados.")
                st.stop()
        # Recalcular 'Total'
        edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)
    else:
        # Convertir columnas numéricas a numérico
        numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
        for col in numeric_columns:
            edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0).round(2)

        edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)

    # Calcular la suma total y la diferencia con el monto DPP 2025
    total_sum = edited_df['Total'].sum().round(2)
    difference = round(desired_total - total_sum, 2)

    col1, col2 = st.columns(2)
    col1.metric("Monto Actual (USD)", f"{total_sum:,.2f}")
    col2.metric("Diferencia con el Monto DPP 2025 (USD)", f"{difference:,.2f}")

    save_to_cache(edited_df, unit, tipo)

    st.subheader("Descargar Tabla Modificada")
    edited_df['Total'] = edited_df['Total'].round(2)
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")

if __name__ == "__main__":
    main()
