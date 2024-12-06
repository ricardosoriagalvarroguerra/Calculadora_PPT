import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
import plotly.express as px
import os
import streamlit_authenticator as stauth
from passlib.context import CryptContext

# ------------------- Configuración de la Autenticación -------------------

# Define las credenciales de los usuarios con contraseñas hasheadas
# Reemplaza los hashes de contraseña con los generados anteriormente
users = {
    "usernames": {
        "usuario1": {
            "name": "Usuario Uno",
            "password": "$2b$12$KIXQp6Zx6jB1H.cw8B1e7e7MZf2A9E8aRJpM1yYJWc6A9ZbZTc4Qa"  # Hash para "password1"
        },
        "usuario2": {
            "name": "Usuario Dos",
            "password": "$2b$12$wzQq6Zx6jC2H.cw8C2e8e8Mzf3B0F9E9aSKqM2yYZD7B0AbZTd5Rb"  # Hash para "password2"
        }
    }
}

# Configuración del autenticador
authenticator = stauth.Authenticate(
    users["usernames"],
    "mi_app_auth",  # Nombre de la cookie
    "abcdef",       # Clave secreta (debe ser una cadena segura)
    cookie_expiry_days=30
)

# ------------------- Definición de Contraseñas por Página -------------------

# Define contraseñas para cada página
PAGE_PASSWORDS = {
    "VPO": "vpo_password",
    "VPD": "vpd_password",
    "VPE": "vpe_password",
    "VPF": "vpf_password",
    "PRE": "pre_password",
    "Coordinación": "coord_password",
    "Consolidado": "consolidado_password"
}

# ------------------- Funciones de Cálculo -------------------

def calculate_total_misiones(row):
    return round(
        (row['Costo de Pasaje'] + (row['Alojamiento'] + row['Per-diem y Otros'] + row['Movilidad']) * row['Días']) * row['Cantidad de Funcionarios'],
        2
    )

def calculate_total_consultorias(row):
    return round(row['Nº'] * row['Monto mensual'] * row['cantidad meses'], 2)

# ------------------- Configuración de la Página -------------------

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

# ------------------- Funciones de la Aplicación -------------------

# Función para manejar la página de Consolidado
def handle_consolidado_page():
    st.header("Consolidado")
    
    file_path = 'BDD_Ajuste.xlsx'  # Asegúrate de que la ruta es correcta

    try:
        # Leer la hoja 'consolidadoV2' primero y renombrarla a 'Resumen'
        df_resumen = pd.read_excel(file_path, sheet_name='consolidadoV2')
        numeric_cols_resumen = df_resumen.select_dtypes(include=['float', 'int']).columns.tolist()
        for col in numeric_cols_resumen:
            df_resumen[col] = pd.to_numeric(df_resumen[col], errors='coerce')
        # Redondear a una decimal
        df_resumen[numeric_cols_resumen] = df_resumen[numeric_cols_resumen].round(1)

        # Formateador a una sola decimal
        one_decimal_formatter = '''
            function(params) { 
                if (params.value == null || params.value === "") { 
                    return ""; 
                } 
                var val = Number(params.value); 
                if (isNaN(val)) {
                    return params.value;
                } 
                return val.toFixed(1); 
            }
        '''

        # Configurar AgGrid para Resumen
        gb_resumen = GridOptionsBuilder.from_dataframe(df_resumen)
        gb_resumen.configure_default_column(editable=False, sortable=True, filter=True, type=["numericColumn"])

        for col in numeric_cols_resumen:
            gb_resumen.configure_column(
                col,
                type=["numericColumn"],
                valueFormatter=one_decimal_formatter,
                headerStyle={'backgroundColor': '#f2f2f2', 'fontWeight': 'bold'}
            )
        
        # Eliminar la paginación
        # gb_resumen.configure_pagination(paginationAutoPageSize=True)  # Comentado o eliminado

        gb_resumen.configure_side_bar()
        grid_options_resumen = gb_resumen.build()

        # Calcular la altura de la tabla Resumen
        num_rows_resumen = len(df_resumen)
        row_height = 35  # Altura por fila en píxeles (ajusta según tu preferencia)
        max_height = 800  # Altura máxima para la tabla
        calculated_height_resumen = min(row_height * num_rows_resumen + 100, max_height)  # 100 píxeles adicionales para cabecera y márgenes

        # Añadir una sección con un fondo ligeramente coloreado para Resumen
        st.markdown(
            """
            <div style="background-color:#e6f7ff; padding:10px; border-radius:5px;">
                <h3>Resumen</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("")

        AgGrid(
            df_resumen,
            gridOptions=grid_options_resumen,
            data_return_mode=DataReturnMode.FILTERED,
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True,
            height=calculated_height_resumen,
            width='100%',
            theme='balham'  # Usar el mismo tema para consistencia
        )

        st.markdown("---")  # Separador horizontal

        # Leer la hoja 'Consolidado' y renombrarla a 'Desglose'
        df_desglose = pd.read_excel(file_path, sheet_name='Consolidado')
        numeric_cols_desglose = df_desglose.select_dtypes(include=['float', 'int']).columns.tolist()
        for col in numeric_cols_desglose:
            df_desglose[col] = pd.to_numeric(df_desglose[col], errors='coerce')
        # Redondear a una decimal
        df_desglose[numeric_cols_desglose] = df_desglose[numeric_cols_desglose].round(1)

        # Configurar AgGrid para Desglose
        gb_desglose = GridOptionsBuilder.from_dataframe(df_desglose)
        gb_desglose.configure_default_column(editable=False, sortable=True, filter=True, type=["numericColumn"])

        for col in numeric_cols_desglose:
            gb_desglose.configure_column(
                col,
                type=["numericColumn"],
                valueFormatter=one_decimal_formatter,
                headerStyle={'backgroundColor': '#f2f2f2', 'fontWeight': 'bold'}
            )
        
        # Eliminar la paginación
        # gb_desglose.configure_pagination(paginationAutoPageSize=True)  # Comentado o eliminado

        gb_desglose.configure_side_bar()
        grid_options_desglose = gb_desglose.build()

        # Calcular la altura de la tabla Desglose
        num_rows_desglose = len(df_desglose)
        calculated_height_desglose = min(row_height * num_rows_desglose + 100, max_height)  # 100 píxeles adicionales para cabecera y márgenes

        # Añadir una sección con un fondo ligeramente coloreado para Desglose
        st.markdown(
            """
            <div style="background-color:#fff2e6; padding:10px; border-radius:5px;">
                <h3>Desglose</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("")

        AgGrid(
            df_desglose,
            gridOptions=grid_options_desglose,
            data_return_mode=DataReturnMode.FILTERED,
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True,
            height=calculated_height_desglose,
            width='100%',
            theme='balham'  # Usar el mismo tema para consistencia
        )

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

        # Formatear a una sola decimal
        consolidado_misiones_display = consolidado_misiones_df[['Unidad Organizacional', "Misiones - Actual", "Misiones - Monto DPP 2025", "Misiones - Ajuste"]]
        styled_misiones_df = consolidado_misiones_display.style.applymap(highlight_zero, subset=["Misiones - Ajuste"])
        styled_misiones_df = styled_misiones_df.format(
            "{:,.1f}", 
            subset=[
                "Misiones - Actual",
                "Misiones - Monto DPP 2025",
                "Misiones - Ajuste"
            ]
        )

        consolidado_consultorias_display = consolidado_consultorias_df[['Unidad Organizacional', "Consultorías - Actual", "Consultorías - Monto DPP 2025", "Consultorías - Ajuste"]]
        styled_consultorias_df = consolidado_consultorias_display.style.applymap(highlight_zero, subset=["Consultorías - Ajuste"])
        styled_consultorias_df = styled_consultorias_df.format(
            "{:,.1f}", 
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

    # Función para manejar la autenticación por página
    def authenticate_page(page_name):
        if 'page_authenticated' not in st.session_state:
            st.session_state['page_authenticated'] = {}

        if page_name not in st.session_state['page_authenticated']:
            st.session_state['page_authenticated'][page_name] = False

        if not st.session_state['page_authenticated'][page_name]:
            st.header(f"🔒 Acceso a la página: {page_name}")
            password = st.text_input(f"Ingresa la contraseña para la página {page_name}:", type="password", key=f"password_{page_name}")
            if st.button(f"Ingresar a {page_name}"):
                if password == PAGE_PASSWORDS.get(page_name, ""):
                    st.session_state['page_authenticated'][page_name] = True
                    st.success("¡Autenticación exitosa!")
                    st.experimental_rerun()
                else:
                    st.error("Contraseña incorrecta. Inténtalo de nuevo.")

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

        # Formatear a una sola decimal
        consolidado_misiones_display = consolidado_misiones_df[['Unidad Organizacional', "Misiones - Actual", "Misiones - Monto DPP 2025", "Misiones - Ajuste"]]
        styled_misiones_df = consolidado_misiones_display.style.applymap(highlight_zero, subset=["Misiones - Ajuste"])
        styled_misiones_df = styled_misiones_df.format(
            "{:,.1f}", 
            subset=[
                "Misiones - Actual",
                "Misiones - Monto DPP 2025",
                "Misiones - Ajuste"
            ]
        )

        consolidado_consultorias_display = consolidado_consultorias_df[['Unidad Organizacional', "Consultorías - Actual", "Consultorías - Monto DPP 2025", "Consultorías - Ajuste"]]
        styled_consultorias_df = consolidado_consultorias_display.style.applymap(highlight_zero, subset=["Consultorías - Ajuste"])
        styled_consultorias_df = styled_consultorias_df.format(
            "{:,.1f}", 
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

    # Función para manejar la página VPO
    def handle_vpo_page(deseados):
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPO_view")

        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPO_Misiones_page")
            process_misiones_page("VPO", "Misiones", page, deseados, use_objetivo=True)
        elif view == "Consultorías":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPO_Consultorias_page")
            process_consultorias_page("VPO", "Consultorías", page, deseados)

    # Función para manejar la página VPD
    def handle_vpd_page(deseados):
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPD_view")

        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPD_Misiones_page")
            process_misiones_page("VPD", "Misiones", page, deseados, use_objetivo=False)
        elif view == "Consultorías":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPD_Consultorias_page")
            process_consultorias_page("VPD", "Consultorías", page, deseados)

    # Función para manejar la página VPE
    def handle_vpe_page(deseados):
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPE_view")

        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPE_Misiones_page")
            process_misiones_page("VPE", "Misiones", page, deseados, use_objetivo=False)
        elif view == "Consultorías":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPE_Consultorias_page")
            process_consultorias_page("VPE", "Consultorías", page, deseados)

    # Función para manejar la página VPF
    def handle_vpf_page(deseados):
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPF_view")

        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPF_Misiones_page")
            process_misiones_page("VPF", "Misiones", page, deseados, use_objetivo=False)
        elif view == "Consultorías":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPF_Consultorias_page")
            process_consultorias_page("VPF", "Consultorías", page, deseados)

    # Función para manejar la página PRE
    def handle_pre_page(deseados):
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="PRE_view")

        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="PRE_Misiones_page")
            process_misiones_page("PRE", "Misiones", page, deseados, use_objetivo=False)
        elif view == "Consultorías":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="PRE_Consultorias_page")
            process_consultorias_page("PRE", "Consultorías", page, deseados)

    # Función para procesar la página de Misiones
    def process_misiones_page(unit, tipo, page, deseados, use_objetivo):
        file_path = 'BDD_Ajuste.xlsx'
        sheet_name = f"Misiones_{unit}"
        cache_file = f'cache/{unit}_{tipo}_DPP2025.csv'

        def process_misiones_df(df, sheet_name, unit):
            if unit == "VPE":
                required_columns = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO']
            elif unit == "PRE":
                required_columns = ['País', 'Operación', 'PRE o VP', 'Cantidad de Funcionarios', 'Días',
                                    'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total', 'Area imputacion']
            else:
                required_columns = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                    'Alojamiento', 'Per-diem y Otros', 'Movilidad']
                if use_objetivo:
                    required_columns.append('Objetivo')

            for col in required_columns:
                if col not in df.columns:
                    st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                    st.stop()

            if unit == "VPE":
                df['Total'] = pd.to_numeric(df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            elif unit == "PRE":
                df['Total'] = pd.to_numeric(df['Total'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
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

    # Función para procesar la página de Consultorías
    def process_consultorias_page(unit, tipo, page, deseados):
        file_path = 'BDD_Ajuste.xlsx'
        sheet_name = f"Consultores_{unit}"
        cache_file = f'cache/{unit}_{tipo}_DPP2025.csv'

        def process_consultorias_df(df, sheet_name, unit):
            if unit == "VPE":
                required_columns = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO']
            elif unit == "PRE":
                required_columns = ['Cargo', 'PRE/AREA', 'Nº', 'Monto mensual', 'cantidad meses', 'Total', 'Area imputacion']
            elif unit == "VPO":
                required_columns = ['Cargo', 'Nº', 'Monto mensual', 'cantidad meses', 'Total', 'Observaciones', 'Objetivo', 'tipo']
            else:
                required_columns = ['Cargo', f"{unit}/AREA", 'Nº', 'Monto mensual', 'cantidad meses', 'Total']

            for col in required_columns:
                if col not in df.columns:
                    st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                    st.stop()

            if unit == "VPE":
                df['Total'] = pd.to_numeric(df['Suma de MONTO'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            elif unit == "PRE":
                df['Total'] = pd.to_numeric(df['Total'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            elif unit == "VPO":
                if 'Total' not in df.columns or df['Total'].sum() == 0:
                    df['Total'] = df.apply(calculate_total_consultorias, axis=1)
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

    # Función para mostrar la tabla de Misiones - Requerimiento del área
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

    # Función para mostrar la tabla de Consultorías - Requerimiento del área
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

    # Función para editar Misiones - DPP 2025
    def edit_misiones_dpp(df, unit, desired_total, tipo, use_objetivo):
        st.header(f"{unit} - Misiones: DPP 2025")
        st.subheader(f"Monto DPP 2025: {desired_total:,.2f} USD")
        st.write("Edita los valores en la tabla para ajustar el presupuesto.")

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True, groupable=True)

        if unit == "VPE":
            editable_columns = ['Suma de MONTO']
            gb.configure_columns(editable_columns, editable=True, type=['numericColumn'],
                                 valueFormatter="Math.round(x).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})")
        elif unit == "PRE":
            editable_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
            for col in editable_columns:
                gb.configure_column(
                    col,
                    editable=True,
                    type=['numericColumn'],
                    valueFormatter="Math.round(x).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                )
            gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                function(params) {
                    return Math.round(
                        (Number(params.data['Costo de Pasaje']) + 
                        (Number(params.data['Alojamiento']) + Number(params.data['Per-diem y Otros']) + Number(params.data['Movilidad'])) * 
                        Number(params.data['Días'])) * 
                        Number(params.data['Cantidad de Funcionarios'])
                    * 100) / 100;
                }
            """))
        else:
            numeric_columns_aggrid = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                      'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
            for col in numeric_columns_aggrid:
                gb.configure_column(
                    col,
                    type=['numericColumn'],
                    valueFormatter="Math.round(x).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                )

            gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                function(params) {
                    return Math.round(
                        (Number(params.data['Costo de Pasaje']) + 
                        (Number(params.data['Alojamiento']) + Number(params.data['Per-diem y Otros']) + Number(params.data['Movilidad'])) * 
                        Number(params.data['Días'])) * 
                        Number(params.data['Cantidad de Funcionarios'])
                    * 100) / 100;
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
            essential_cols = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO', 'Total']
        elif unit == "PRE":
            essential_cols = ['País', 'Operación', 'PRE o VP', 'Cantidad de Funcionarios', 'Días',
                              'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total', 'Area imputacion']
        else:
            essential_cols = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                              'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
            if use_objetivo:
                essential_cols.append('Objetivo')

        for col in essential_cols:
            if col not in edited_df.columns:
                st.error(f"La columna '{col}' está ausente en los datos editados.")
                st.stop()

        if unit == "VPE":
            numeric_columns = ['Suma de MONTO']
            for col in numeric_columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            edited_df['Total'] = edited_df['Suma de MONTO']
        elif unit == "PRE":
            numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
            for col in numeric_columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)
        else:
            numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                               'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
            for col in numeric_columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)

        total_sum = edited_df['Total'].sum()
        difference = desired_total - total_sum

        col1, col2 = st.columns(2)
        col1.metric("Monto Actual (USD)", f"{total_sum:,.2f}")
        col2.metric("Diferencia con el Monto DPP 2025 (USD)", f"{difference:,.2f}")

        save_to_cache(edited_df, unit, tipo)

        st.subheader("Descargar Tabla Modificada")
        edited_df['Total'] = edited_df['Total'].round(2)
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")

    # Función para editar Consultorías - DPP 2025
    def edit_consultorias_dpp(df, unit, desired_total, tipo):
        st.header(f"{unit} - Consultorías: DPP 2025")
        st.subheader(f"Monto DPP 2025: {desired_total:,.2f} USD")
        st.write("Edita los valores en la tabla para ajustar el presupuesto.")

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True, groupable=True)

        if unit == "VPE":
            editable_columns = ['Suma de MONTO']
            gb.configure_columns(editable_columns, editable=True, type=['numericColumn'],
                                 valueFormatter="Math.round(x).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})")
        elif unit == "PRE":
            editable_columns = ['Nº', 'Monto mensual', 'cantidad meses']
            for col in editable_columns:
                gb.configure_column(
                    col,
                    editable=True,
                    type=['numericColumn'],
                    valueFormatter="Math.round(x).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                )
            gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                function(params) {
                    return Math.round(
                        Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses'])
                    * 100) / 100;
                }
            """))
        elif unit == "VPO":
            editable_columns = ['Nº', 'Monto mensual', 'cantidad meses']
            for col in editable_columns:
                gb.configure_column(
                    col,
                    editable=True,
                    type=['numericColumn'],
                    valueFormatter="Math.round(x).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                )
            gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                function(params) {
                    return Math.round(
                        Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses'])
                    * 100) / 100;
                }
            """))
        else:
            numeric_columns_aggrid = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
            for col in numeric_columns_aggrid:
                gb.configure_column(
                    col,
                    type=['numericColumn'],
                    valueFormatter="Math.round(x).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                )

            gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                function(params) {
                    return Math.round(
                        Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses'])
                    * 100) / 100;
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
            essential_cols = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO', 'Total']
        elif unit == "PRE":
            essential_cols = ['Cargo', 'PRE/AREA', 'Nº', 'Monto mensual', 'cantidad meses', 'Total', 'Area imputacion']
        elif unit == "VPO":
            essential_cols = ['Cargo', 'Nº', 'Monto mensual', 'cantidad meses', 'Total', 'Observaciones', 'Objetivo', 'tipo']
        else:
            essential_cols = ['Cargo', f"{unit}/AREA", 'Nº', 'Monto mensual', 'cantidad meses', 'Total']

        for col in essential_cols:
            if col not in edited_df.columns:
                st.error(f"La columna '{col}' está ausente en los datos editados.")
                st.stop()

        if unit == "VPE":
            numeric_columns = ['Suma de MONTO']
            for col in numeric_columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            edited_df['Total'] = edited_df['Suma de MONTO']
        elif unit == "PRE":
            numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses']
            for col in numeric_columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)
        else:
            numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
            for col in numeric_columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)

        total_sum = edited_df['Total'].sum()
        difference = desired_total - total_sum

        col1, col2 = st.columns(2)
        col1.metric("Monto Actual (USD)", f"{total_sum:,.2f}")
        col2.metric("Diferencia con el Monto DPP 2025 (USD)", f"{difference:,.2f}")

        save_to_cache(edited_df, unit, tipo)

        st.subheader("Descargar Tabla Modificada")
        edited_df['Total'] = edited_df['Total'].round(2)
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")

    # Función para crear gráficas de dona (pie charts)
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

    # Función para editar Consultorías - DPP 2025
    def edit_consultorias_dpp(df, unit, desired_total, tipo):
        st.header(f"{unit} - Consultorías: DPP 2025")
        st.subheader(f"Monto DPP 2025: {desired_total:,.2f} USD")
        st.write("Edita los valores en la tabla para ajustar el presupuesto.")

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True, groupable=True)

        if unit == "VPE":
            editable_columns = ['Suma de MONTO']
            gb.configure_columns(editable_columns, editable=True, type=['numericColumn'],
                                 valueFormatter="Math.round(x).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})")
        elif unit == "PRE":
            editable_columns = ['Nº', 'Monto mensual', 'cantidad meses']
            for col in editable_columns:
                gb.configure_column(
                    col,
                    editable=True,
                    type=['numericColumn'],
                    valueFormatter="Math.round(x).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                )
            gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                function(params) {
                    return Math.round(
                        Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses'])
                    * 100) / 100;
                }
            """))
        elif unit == "VPO":
            editable_columns = ['Nº', 'Monto mensual', 'cantidad meses']
            for col in editable_columns:
                gb.configure_column(
                    col,
                    editable=True,
                    type=['numericColumn'],
                    valueFormatter="Math.round(x).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                )
            gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                function(params) {
                    return Math.round(
                        Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses'])
                    * 100) / 100;
                }
            """))
        else:
            numeric_columns_aggrid = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
            for col in numeric_columns_aggrid:
                gb.configure_column(
                    col,
                    type=['numericColumn'],
                    valueFormatter="Math.round(x).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                )

            gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                function(params) {
                    return Math.round(
                        Number(params.data['Nº']) * Number(params.data['Monto mensual']) * Number(params.data['cantidad meses'])
                    * 100) / 100;
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
            essential_cols = ['ÍTEM PRESUPUESTO', 'OFICINA', 'UNID. ORG.', 'ACCIONES', 'CATEGORÍA', 'SUBCATEGORÍA', 'Suma de MONTO', 'Total']
        elif unit == "PRE":
            essential_cols = ['Cargo', 'PRE/AREA', 'Nº', 'Monto mensual', 'cantidad meses', 'Total', 'Area imputacion']
        elif unit == "VPO":
            essential_cols = ['Cargo', 'Nº', 'Monto mensual', 'cantidad meses', 'Total', 'Observaciones', 'Objetivo', 'tipo']
        else:
            essential_cols = ['Cargo', f"{unit}/AREA", 'Nº', 'Monto mensual', 'cantidad meses', 'Total']

        for col in essential_cols:
            if col not in edited_df.columns:
                st.error(f"La columna '{col}' está ausente en los datos editados.")
                st.stop()

        if unit == "VPE":
            numeric_columns = ['Suma de MONTO']
            for col in numeric_columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            edited_df['Total'] = edited_df['Suma de MONTO']
        elif unit == "PRE":
            numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses']
            for col in numeric_columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)
        else:
            numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
            for col in numeric_columns:
                edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
            edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)

        total_sum = edited_df['Total'].sum()
        difference = desired_total - total_sum

        col1, col2 = st.columns(2)
        col1.metric("Monto Actual (USD)", f"{total_sum:,.2f}")
        col2.metric("Diferencia con el Monto DPP 2025 (USD)", f"{difference:,.2f}")

        save_to_cache(edited_df, unit, tipo)

        st.subheader("Descargar Tabla Modificada")
        edited_df['Total'] = edited_df['Total'].round(2)
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar CSV", data=csv, file_name=f"tabla_modificada_{tipo.lower()}_{unit.lower()}.csv", mime="text/csv")

    # ------------------- Función Principal -------------------

    def main_app(deseados):
        st.sidebar.title("Navegación")
        main_page = st.sidebar.selectbox(
            "Selecciona una página principal:",
            ("VPO", "VPD", "VPE", "VPF", "PRE", "Coordinación", "Consolidado")
        )
        st.title(main_page)

        file_path = 'BDD_Ajuste.xlsx'
        try:
            df_pre_misiones = pd.read_excel(file_path, sheet_name='Misiones_PRE')
            total_pre_misiones = df_pre_misiones['Total'].sum()
            deseados["PRE"]["Misiones"] = total_pre_misiones
        except Exception as e:
            st.warning(f"No se pudo leer la hoja 'Misiones_PRE': {e}")
            deseados["PRE"]["Misiones"] = 0.0

        try:
            df_pre_consultorias = pd.read_excel(file_path, sheet_name='Consultores_PRE')
            total_pre_consultorias = df_pre_consultorias['Total'].sum()
            deseados["PRE"]["Consultorías"] = total_pre_consultorias
        except Exception as e:
            st.warning(f"No se pudo leer la hoja 'Consultores_PRE': {e}")
            deseados["PRE"]["Consultorías"] = 0.0

        # Autenticación por página
        authenticate_page(main_page)

        if st.session_state['page_authenticated'].get(main_page, False):
            # Route to the appropriate page handler
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

    # ------------------- Función Principal de Autenticación -------------------

    def main():
        # Autenticación de usuario
        name, authentication_status, username = authenticator.login('Iniciar Sesión', 'main')

        if authentication_status:
            # Autenticación exitosa
            authenticator.logout('Cerrar Sesión', 'main')
            st.sidebar.write(f"Bienvenido *{name}*")

            # Define tu diccionario 'deseados' como antes
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

            main_app(deseados)

        elif authentication_status == False:
            st.error('Nombre de usuario o contraseña incorrectos')
        elif authentication_status == None:
            st.warning('Por favor, ingresa tu nombre de usuario y contraseña')

    # ------------------- Ejecutar la Aplicación -------------------

    if __name__ == "__main__":
        main()
