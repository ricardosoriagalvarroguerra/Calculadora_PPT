import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
import plotly.express as px
import os  # Importación necesaria para manejar archivos y directorios

# Definir las contraseñas directamente en el código
VPO_PASSWORD = "contraseña_vpo"  # Reemplaza con tu contraseña para VPO
VPD_PASSWORD = "contraseña_vpd"  # Reemplaza con tu contraseña para VPD
VPE_PASSWORD = "contraseña_vpe"  # Reemplaza con tu contraseña para VPE
VPF_PASSWORD = "contraseña_vpf"  # Reemplaza con tu contraseña para VPF
PRE_PASSWORD = "contraseña_pre"  # Reemplaza con tu contraseña para PRE

# Función para calcular el total para Misiones VPO, VPD y VPF
def calculate_total_misiones(row):
    return round(
        row['Costo de Pasaje'] * (row['Alojamiento'] + row['Per-diem y Otros'] + row['Movilidad']) * 
        row['Días'] * row['Cantidad de Funcionarios']
    )

# Función para calcular el total para Consultorías VPO, VPD y VPF
def calculate_total_consultorias(row):
    return round(row['Nº'] * row['Monto mensual'] * 1.6 * row['cantidad meses'])

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

# Sidebar para selección de página principal, vista y subpágina
st.sidebar.title("Navegación")
main_page = st.sidebar.selectbox("Selecciona una página principal:", ("VPO", "VPD", "VPE", "VPF", "PRE", "Consolidado"))

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
    st.header("")
    cache_dir = 'cache'
    unidades = ['VPO', 'VPD', 'VPE', 'VPF', 'PRE']  # Añadido VPE, VPF, PRE
    tipos = ['Misiones', 'Consultorías']

    # Inicializar listas para almacenar los datos de Misiones y Consultorías
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
                # Si no hay datos, asumimos que el actual es 0
                deseado = deseados[unidad][tipo]
                row[f"{tipo} - Actual"] = 0
                row[f"{tipo} - Ajuste"] = deseado
                row[f"{tipo} - Deseado"] = deseado
            if tipo == 'Misiones':
                data_misiones.append(row)
            else:
                data_consultorias.append(row)

    # Crear DataFrames separados
    consolidado_misiones_df = pd.DataFrame(data_misiones)
    consolidado_consultorias_df = pd.DataFrame(data_consultorias)

    # Aplicar formato y estilo
    def highlight_zero(val):
        color = 'background-color: #90ee90' if val == 0 else ''
        return color

    # Formatear y estilizar la tabla de Misiones
    styled_misiones_df = consolidado_misiones_df.style.applymap(highlight_zero, subset=[f"Misiones - Ajuste"])
    styled_misiones_df = styled_misiones_df.format(
        "{:,.0f}", 
        subset=[
            "Misiones - Actual",
            "Misiones - Ajuste",
            "Misiones - Deseado"
        ]
    )

    # Formatear y estilizar la tabla de Consultorías
    styled_consultorias_df = consolidado_consultorias_df.style.applymap(highlight_zero, subset=[f"Consultorías - Ajuste"])
    styled_consultorias_df = styled_consultorias_df.format(
        "{:,.0f}", 
        subset=[
            "Consultorías - Actual",
            "Consultorías - Ajuste",
            "Consultorías - Deseado"
        ]
    )

    # Mostrar las tablas por separado
    st.subheader("Misiones")
    st.dataframe(styled_misiones_df)

    st.subheader("Consultorías")
    st.dataframe(styled_consultorias_df)

# Función auxiliar para crear gráficos de dona con anillo más delgado y tamaño más pequeño
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

# Inicializar variables de estado para autenticación
if 'authenticated_vpo' not in st.session_state:
    st.session_state['authenticated_vpo'] = False

if 'authenticated_vpd' not in st.session_state:
    st.session_state['authenticated_vpd'] = False

if 'authenticated_vpe' not in st.session_state:
    st.session_state['authenticated_vpe'] = False

if 'authenticated_vpf' not in st.session_state:
    st.session_state['authenticated_vpf'] = False

if 'authenticated_pre' not in st.session_state:
    st.session_state['authenticated_pre'] = False

# Función para manejar cada página principal
def handle_page(main_page):
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
        "VPE": {  # Definir montos deseados para VPE
            "Misiones": 0.0,         # Reemplaza con los valores reales
            "Consultorías": 0.0      # Reemplaza con los valores reales
        },
        "VPF": {  # Definir montos deseados para VPF
            "Misiones": 138600.0,    # Valor real
            "Consultorías": 170000.0  # Valor real
        },
        "PRE": {  # Definir montos deseados para PRE
            "Misiones": 0.0,         # Reemplaza con los valores reales
            "Consultorías": 0.0      # Reemplaza con los valores reales
        }
    }

    # Función para verificar autenticación
    def authenticate(unidad):
        if unidad == "VPO":
            auth_key = 'authenticated_vpo'
            password = st.sidebar.text_input("Contraseña para VPO", type="password", key="vpo_password")
            correct_password = VPO_PASSWORD
        elif unidad == "VPD":
            auth_key = 'authenticated_vpd'
            password = st.sidebar.text_input("Contraseña para VPD", type="password", key="vpd_password")
            correct_password = VPD_PASSWORD
        elif unidad == "VPE":
            auth_key = 'authenticated_vpe'
            password = st.sidebar.text_input("Contraseña para VPE", type="password", key="vpe_password")
            correct_password = VPE_PASSWORD
        elif unidad == "VPF":
            auth_key = 'authenticated_vpf'
            password = st.sidebar.text_input("Contraseña para VPF", type="password", key="vpf_password")
            correct_password = VPF_PASSWORD
        elif unidad == "PRE":
            auth_key = 'authenticated_pre'
            password = st.sidebar.text_input("Contraseña para PRE", type="password", key="pre_password")
            correct_password = PRE_PASSWORD
        else:
            return False

        if st.sidebar.button("Ingresar", key=f"{unidad}_login"):
            if password == correct_password:
                st.session_state[auth_key] = True
                st.sidebar.success("Contraseña correcta")
            else:
                st.sidebar.error("Contraseña incorrecta")

    # Autenticación para VPO, VPD, VPE, VPF y PRE
    if main_page in ["VPO", "VPD", "VPE", "VPF", "PRE"]:
        auth_key = f'authenticated_{main_page.lower()}'
        if not st.session_state[auth_key]:
            authenticate(main_page)
            if not st.session_state[auth_key]:
                st.warning(f"Ingresa la contraseña para acceder a la sección {main_page}.")
                st.stop()  # Detiene la ejecución hasta que el usuario se autentique

    # Manejo de cada página principal
    if main_page == "VPO":
        # Seleccionar Vista: Misiones o Consultorías
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPO_view")

        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPO_Misiones_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Misiones_VPO'
            cache_file = 'cache/VPO_Misiones_DPP2025.csv'
            cache_dir = 'cache'

            # Función para procesar el DataFrame de VPO Misiones
            def process_vpo_misiones_df(df, sheet_name):
                # Verificar columnas
                required_columns = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                    'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Objetivo']
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

                # Verificar valores en 'Objetivo'
                valid_objetivos = ['R', 'E']
                if 'Objetivo' in df.columns and not df['Objetivo'].dropna().isin(valid_objetivos).all():
                    st.warning("La columna 'Objetivo' contiene valores distintos a 'R' y 'E'. Estos valores serán ignorados en los gráficos de Objetivo.")

                # Calcular 'Total' si es necesario
                if 'Total' not in df.columns or df['Total'].sum() == 0:
                    df['Total'] = df.apply(calculate_total_misiones, axis=1)

                return df

            if page == "DPP 2025":
                # Cargar datos desde cache si existe
                if os.path.exists(cache_file):
                    df = pd.read_csv(cache_file)
                else:
                    # Cargar datos desde Excel
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                    except FileNotFoundError:
                        st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                        st.stop()
                    except Exception as e:
                        st.error(f"Error al leer el archivo Excel: {e}")
                        st.stop()

                    # Procesar datos
                    df = process_vpo_misiones_df(df, sheet_name)
            else:
                # Cargar datos desde Excel
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                except FileNotFoundError:
                    st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                    st.stop()
                except Exception as e:
                    st.error(f"Error al leer el archivo Excel: {e}")
                    st.stop()

                # Procesar datos
                df = process_vpo_misiones_df(df, sheet_name)

            # Definir paleta de colores para Objetivo
            objetivo_color_map = {
                'E': '#a4161a',
                'R': '#d3d3d3'
            }

            # Definir paleta de colores para Países
            pais_color_map = {
                'Argentina': '#457b9d',
                'Bolivia': '#3a5a40',
                'Brasil': '#ffb703',
                'Paraguay': '#d62828',
                'Uruguay': '#1d3557'
            }

            # Página Requerimiento del área para Misiones VPO
            if page == "Requerimiento del área":
                st.header("VPO - Misiones: Requerimiento del área")

                # Resumen por País
                summary_country = df.groupby('País')['Total'].sum().reset_index()

                # Resumen por Objetivo R y E
                summary_obj = df[df['Objetivo'].isin(['R', 'E'])].groupby('Objetivo')['Total'].sum().reset_index()

                # Crear gráficos de dona
                col1, col2 = st.columns(2)

                # Gráfico de Dona: Montos Totales por País
                fig1 = crear_dona(
                    df=summary_country,
                    nombres='País',
                    valores='Total',
                    titulo="Montos Totales por País",
                    color_map=pais_color_map,
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col1.plotly_chart(fig1, use_container_width=True)

                # Gráfico de Dona: Distribución por Objetivo R y E
                fig2 = crear_dona(
                    df=summary_obj,
                    nombres='Objetivo',
                    valores='Total',
                    titulo="Distribución por Objetivo R y E",
                    color_map=objetivo_color_map,
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col2.plotly_chart(fig2, use_container_width=True)

                # Mostrar tabla completa con formato sin decimales en columnas específicas
                st.subheader("Tabla Completa - Misiones VPO")
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

            # Página DPP 2025 para Misiones VPO
            elif page == "DPP 2025":
                st.header("VPO - Misiones: DPP 2025")

                # Monto Total Deseado
                desired_total = deseados["VPO"]["Misiones"]
                st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")

                st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")

                # Configuración de AgGrid para edición
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True, groupable=True)

                # Configurar columnas para mostrar sin decimales
                numeric_columns_aggrid = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                          'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in numeric_columns_aggrid:
                    gb.configure_column(
                        col,
                        type=['numericColumn'],
                        valueFormatter="Math.round(x).toLocaleString()"
                    )

                # Configurar la columna 'Total' para cálculo dinámico sin decimales
                gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                    function(params) {
                        return Math.round(
                            Number(params.data['Costo de Pasaje']) * (Number(params.data['Alojamiento']) + Number(params.data['Per-diem y Otros']) + Number(params.data['Movilidad'])) * 
                            Number(params.data['Días']) * Number(params.data['Cantidad de Funcionarios'])
                        );
                    }
                """))

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
                essential_cols = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                  'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Objetivo', 'Total']
                for col in essential_cols:
                    if col not in edited_df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()

                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                   'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in numeric_columns:
                    edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

                # Verificar valores en 'Objetivo'
                if 'Objetivo' in edited_df.columns and not edited_df['Objetivo'].dropna().isin(['R', 'E']).all():
                    st.warning("La columna 'Objetivo' contiene valores distintos a 'R' y 'E'. Estos valores serán ignorados en los gráficos de Objetivo.")

                # Recalcular 'Total' si es necesario
                edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)

                # Calcular métricas sin decimales
                total_sum = edited_df['Total'].sum()
                difference = desired_total - total_sum

                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")

                # Resumen por País y Objetivo
                summary_country = edited_df.groupby('País')['Total'].sum().reset_index()
                summary_obj = edited_df[edited_df['Objetivo'].isin(['R', 'E'])].groupby('Objetivo')['Total'].sum().reset_index()

                # Crear gráficos de dona actualizados
                col3, col4 = st.columns(2)

                # Gráfico de Dona: Montos Totales por País (Actualizado)
                fig3 = crear_dona(
                    df=summary_country,
                    nombres='País',
                    valores='Total',
                    titulo="Montos Totales por País (Actualizado)",
                    color_map=pais_color_map,
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col3.plotly_chart(fig3, use_container_width=True)

                # Gráfico de Dona: Distribución por Objetivo R y E (Actualizado)
                if not summary_obj.empty:
                    fig4 = crear_dona(
                        df=summary_obj,
                        nombres='Objetivo',
                        valores='Total',
                        titulo="Distribución por Objetivo R y E (Actualizado)",
                        color_map=objetivo_color_map,
                        hole=0.5,        # Aumento del hole para anillo más delgado
                        height=300,      # Reducción de tamaño del gráfico
                        margin_l=50      # Ajuste de márgenes
                    )
                    col4.plotly_chart(fig4, use_container_width=True)

                # Guardar datos editados en cache
                save_to_cache(edited_df, 'VPO', 'Misiones')

                # Descargar tabla modificada sin decimales
                st.subheader("Descargar Tabla Modificada - Misiones VPO")
                edited_df['Total'] = edited_df['Total'].round(0)
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_misiones_vpo.csv", mime="text/csv")

    elif main_page == "VPD":
        # Seleccionar Vista: Misiones o Consultorías
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPD_view")

        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPD_Misiones_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Misiones_VPD'
            cache_file = 'cache/VPD_Misiones_DPP2025.csv'
            cache_dir = 'cache'

            # Función para procesar el DataFrame de VPD Misiones
            def process_vpd_misiones_df(df, sheet_name):
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

                return df

            if page == "DPP 2025":
                # Cargar datos desde cache si existe
                if os.path.exists(cache_file):
                    df = pd.read_csv(cache_file)
                else:
                    # Cargar datos desde Excel
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                    except FileNotFoundError:
                        st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                        st.stop()
                    except Exception as e:
                        st.error(f"Error al leer el archivo Excel: {e}")
                        st.stop()

                    # Procesar datos
                    df = process_vpd_misiones_df(df, sheet_name)
            else:
                # Cargar datos desde Excel
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                except FileNotFoundError:
                    st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                    st.stop()
                except Exception as e:
                    st.error(f"Error al leer el archivo Excel: {e}")
                    st.stop()

                # Procesar datos
                df = process_vpd_misiones_df(df, sheet_name)

            # Página Requerimiento del área para Misiones VPD
            if page == "Requerimiento del área":
                st.header("VPD - Misiones: Requerimiento del área")

                # Mostrar tabla completa sin decimales
                st.subheader("Tabla Completa - Misiones VPD")
                st.dataframe(
                    df.style.format({
                        "Cantidad de Funcionarios": "{:.0f}",
                        "Días": "{:.0f}",
                        "Costo de Pasaje": "{:,.0f}",
                        "Alojamiento": "{:,.0f}",
                        "Per-diem y Otros": "{:,.0f}",
                        "Movilidad": "{:,.0f}",
                        "Total": "{:.0f}"
                    }),
                    height=400
                )

            # Página DPP 2025 para Misiones VPD
            elif page == "DPP 2025":
                st.header("VPD - Misiones: DPP 2025")

                # Monto Total Deseado
                desired_total = deseados["VPD"]["Misiones"]
                st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")

                st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")

                # Configuración de AgGrid para edición
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True, groupable=True)

                # Configurar columnas para mostrar sin decimales
                numeric_columns_aggrid = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                          'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in numeric_columns_aggrid:
                    gb.configure_column(
                        col,
                        type=['numericColumn'],
                        valueFormatter="Math.round(x).toLocaleString()"
                    )

                # Configurar la columna 'Total' para cálculo dinámico sin decimales
                gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                    function(params) {
                        return Math.round(
                            Number(params.data['Costo de Pasaje']) * (Number(params.data['Alojamiento']) + Number(params.data['Per-diem y Otros']) + Number(params.data['Movilidad'])) * 
                            Number(params.data['Días']) * Number(params.data['Cantidad de Funcionarios'])
                        );
                    }
                """))

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
                essential_cols = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                  'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Objetivo', 'Total']
                for col in essential_cols:
                    if col not in edited_df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()

                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                   'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in numeric_columns:
                    edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

                # Verificar valores en 'Objetivo'
                if 'Objetivo' in edited_df.columns and not edited_df['Objetivo'].dropna().isin(['R', 'E']).all():
                    st.warning("La columna 'Objetivo' contiene valores distintos a 'R' y 'E'. Estos valores serán ignorados en los gráficos de Objetivo.")

                # Recalcular 'Total' si es necesario
                edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)

                # Calcular métricas sin decimales
                total_sum = edited_df['Total'].sum()
                difference = desired_total - total_sum

                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")

                # Resumen por País y Objetivo
                summary_country = edited_df.groupby('País')['Total'].sum().reset_index()
                summary_obj = edited_df[edited_df['Objetivo'].isin(['R', 'E'])].groupby('Objetivo')['Total'].sum().reset_index()

                # Crear gráficos de dona actualizados
                col3, col4 = st.columns(2)

                # Gráfico de Dona: Montos Totales por País (Actualizado)
                fig3 = crear_dona(
                    df=summary_country,
                    nombres='País',
                    valores='Total',
                    titulo="Montos Totales por País (Actualizado)",
                    color_map=pais_color_map,
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col3.plotly_chart(fig3, use_container_width=True)

                # Gráfico de Dona: Distribución por Objetivo R y E (Actualizado)
                if not summary_obj.empty:
                    fig4 = crear_dona(
                        df=summary_obj,
                        nombres='Objetivo',
                        valores='Total',
                        titulo="Distribución por Objetivo R y E (Actualizado)",
                        color_map=objetivo_color_map,
                        hole=0.5,        # Aumento del hole para anillo más delgado
                        height=300,      # Reducción de tamaño del gráfico
                        margin_l=50      # Ajuste de márgenes
                    )
                    col4.plotly_chart(fig4, use_container_width=True)

                # Guardar datos editados en cache
                save_to_cache(edited_df, 'VPD', 'Misiones')

                # Descargar tabla modificada sin decimales
                st.subheader("Descargar Tabla Modificada - Misiones VPD")
                edited_df['Total'] = edited_df['Total'].round(0)
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_misiones_vpd.csv", mime="text/csv")

    elif main_page == "VPE":
        # Aquí debes implementar la lógica específica para la página VPE
        st.header("VPE - Página en Desarrollo")
        st.write("Aquí puedes agregar las funcionalidades específicas para VPE.")
        # Ejemplo de estructura similar a VPO y VPD
        # Puedes replicar el manejo de vistas, subpáginas, autenticación de datos, etc.

    elif main_page == "VPF":
        # Seleccionar Vista: Misiones o Consultorías
        view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPF_view")

        if view == "Misiones":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPF_Misiones_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Misiones_VPF'  # Define la hoja correspondiente en tu Excel
            cache_file = 'cache/VPF_Misiones_DPP2025.csv'
            cache_dir = 'cache'

            # Función para procesar el DataFrame de VPF Misiones
            def process_vpf_misiones_df(df, sheet_name):
                # Verificar columnas
                required_columns = ['País', 'Motivo', 'VPF/AREA', 'Cantidad de Funcionarios', 'Días', 
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

                return df

            if page == "DPP 2025":
                # Cargar datos desde cache si existe
                if os.path.exists(cache_file):
                    df = pd.read_csv(cache_file)
                else:
                    # Cargar datos desde Excel
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                    except FileNotFoundError:
                        st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                        st.stop()
                    except Exception as e:
                        st.error(f"Error al leer el archivo Excel: {e}")
                        st.stop()

                    # Procesar datos
                    df = process_vpf_misiones_df(df, sheet_name)
            else:
                # Cargar datos desde Excel
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                except FileNotFoundError:
                    st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                    st.stop()
                except Exception as e:
                    st.error(f"Error al leer el archivo Excel: {e}")
                    st.stop()

                # Procesar datos
                df = process_vpf_misiones_df(df, sheet_name)

            # Definir paleta de colores para VPF/AREA
            vpf_area_unique = df['VPF/AREA'].unique()
            # Asignar colores únicos a cada VPF/AREA
            vpf_area_color_map = {area: px.colors.qualitative.Pastel[i % len(px.colors.qualitative.Pastel)] for i, area in enumerate(vpf_area_unique)}

            # Página Requerimiento del área para Misiones VPF
            if page == "Requerimiento del área":
                st.header("VPF - Misiones: Requerimiento del área")

                # Resumen por País
                summary_country = df.groupby('País')['Total'].sum().reset_index()

                # Resumen por VPF/AREA
                summary_vpf_area = df.groupby('VPF/AREA')['Total'].sum().reset_index()

                # Crear gráficos de dona
                col1, col2 = st.columns(2)

                # Gráfico de Dona: Montos Totales por País
                fig1 = crear_dona(
                    df=summary_country,
                    nombres='País',
                    valores='Total',
                    titulo="Montos Totales por País",
                    color_map=vpf_area_color_map,  # Puedes ajustar el color_map si es necesario
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col1.plotly_chart(fig1, use_container_width=True)

                # Gráfico de Dona: Distribución por VPF/AREA
                fig2 = crear_dona(
                    df=summary_vpf_area,
                    nombres='VPF/AREA',
                    valores='Total',
                    titulo="Distribución por VPF/AREA",
                    color_map=vpf_area_color_map,
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col2.plotly_chart(fig2, use_container_width=True)

                # Mostrar tabla completa con formato sin decimales en columnas específicas
                st.subheader("Tabla Completa - Misiones VPF")
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

            # Página DPP 2025 para Misiones VPF
            elif page == "DPP 2025":
                st.header("VPF - Misiones: DPP 2025")

                # Monto Total Deseado
                desired_total = deseados["VPF"]["Misiones"]
                st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")

                st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")

                # Configuración de AgGrid para edición
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True, groupable=True)

                # Configurar columnas para mostrar sin decimales
                numeric_columns_aggrid = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                          'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in numeric_columns_aggrid:
                    gb.configure_column(
                        col,
                        type=['numericColumn'],
                        valueFormatter="Math.round(x).toLocaleString()"
                    )

                # Configurar la columna 'Total' para cálculo dinámico sin decimales
                gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                    function(params) {
                        return Math.round(
                            Number(params.data['Costo de Pasaje']) * 
                            (Number(params.data['Alojamiento']) + Number(params.data['Per-diem y Otros']) + Number(params.data['Movilidad'])) * 
                            Number(params.data['Días']) * 
                            Number(params.data['Cantidad de Funcionarios'])
                        );
                    }
                """))

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
                essential_cols = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                  'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Objetivo', 'Total']
                for col in essential_cols:
                    if col not in edited_df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()

                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                                   'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
                for col in numeric_columns:
                    edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

                # Verificar valores en 'Objetivo'
                if 'Objetivo' in edited_df.columns and not edited_df['Objetivo'].dropna().isin(['R', 'E']).all():
                    st.warning("La columna 'Objetivo' contiene valores distintos a 'R' y 'E'. Estos valores serán ignorados en los gráficos de Objetivo.")

                # Recalcular 'Total' si es necesario
                edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)

                # Calcular métricas sin decimales
                total_sum = edited_df['Total'].sum()
                difference = desired_total - total_sum

                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")

                # Resumen por País y VPF/AREA
                summary_country = edited_df.groupby('País')['Total'].sum().reset_index()
                summary_vpf_area = edited_df.groupby('VPF/AREA')['Total'].sum().reset_index()

                # Crear gráficos de dona actualizados
                col3, col4 = st.columns(2)

                # Gráfico de Dona: Montos Totales por País (Actualizado)
                fig3 = crear_dona(
                    df=summary_country,
                    nombres='País',
                    valores='Total',
                    titulo="Montos Totales por País (Actualizado)",
                    color_map=vpf_area_color_map,
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col3.plotly_chart(fig3, use_container_width=True)

                # Gráfico de Dona: Distribución por VPF/AREA (Actualizado)
                fig4 = crear_dona(
                    df=summary_vpf_area,
                    nombres='VPF/AREA',
                    valores='Total',
                    titulo="Distribución por VPF/AREA (Actualizado)",
                    color_map=vpf_area_color_map,
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col4.plotly_chart(fig4, use_container_width=True)

                # Guardar datos editados en cache
                save_to_cache(edited_df, 'VPF', 'Misiones')

                # Descargar tabla modificada sin decimales
                st.subheader("Descargar Tabla Modificada - Misiones VPF")
                edited_df['Total'] = edited_df['Total'].round(0)
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_misiones_vpf.csv", mime="text/csv")

        elif view == "Consultorías":
            page = st.sidebar.selectbox("Selecciona una subpágina:", ("Requerimiento del área", "DPP 2025"), key="VPF_Consultorias_page")
            file_path = 'BDD_Ajuste.xlsx'
            sheet_name = 'Consultores_VPF'
            cache_file = 'cache/VPF_Consultorias_DPP2025.csv'
            cache_dir = 'cache'

            # Función para procesar el DataFrame de VPF Consultorías
            def process_vpf_consultorias_df(df, sheet_name):
                # Verificar columnas
                required_columns = ['Cargo', 'VPF/AREA', 'Nº', 'Monto mensual', 'cantidad meses', 'Total']
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

                return df

            if page == "DPP 2025":
                # Cargar datos desde cache si existe
                if os.path.exists(cache_file):
                    df = pd.read_csv(cache_file)
                else:
                    # Cargar datos desde Excel
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                    except FileNotFoundError:
                        st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                        st.stop()
                    except Exception as e:
                        st.error(f"Error al leer el archivo Excel: {e}")
                        st.stop()

                    # Procesar datos
                    df = process_vpf_consultorias_df(df, sheet_name)
            else:
                # Cargar datos desde Excel
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                except FileNotFoundError:
                    st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
                    st.stop()
                except Exception as e:
                    st.error(f"Error al leer el archivo Excel: {e}")
                    st.stop()

                # Procesar datos
                df = process_vpf_consultorias_df(df, sheet_name)

            # Definir paleta de colores para VPF/AREA
            vpf_area_unique = df['VPF/AREA'].unique()
            # Asignar colores únicos a cada VPF/AREA
            vpf_area_color_map = {area: px.colors.qualitative.Pastel[i % len(px.colors.qualitative.Pastel)] for i, area in enumerate(vpf_area_unique)}

            # Página Requerimiento del área para Consultorías VPF
            if page == "Requerimiento del área":
                st.header("VPF - Consultorías: Requerimiento del área")

                # Resumen por Cargo
                summary_cargo = df.groupby('Cargo')['Total'].sum().reset_index()

                # Resumen por VPF/AREA
                summary_vpf_area = df.groupby('VPF/AREA')['Total'].sum().reset_index()

                # Crear gráficos de dona
                col1, col2 = st.columns(2)

                # Gráfico de Dona: Montos Totales por Cargo
                fig1 = crear_dona(
                    df=summary_cargo,
                    nombres='Cargo',
                    valores='Total',
                    titulo="Montos Totales por Cargo",
                    color_map=vpf_area_color_map,  # Puedes ajustar el color_map si es necesario
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col1.plotly_chart(fig1, use_container_width=True)

                # Gráfico de Dona: Distribución por VPF/AREA
                fig2 = crear_dona(
                    df=summary_vpf_area,
                    nombres='VPF/AREA',
                    valores='Total',
                    titulo="Distribución por VPF/AREA",
                    color_map=vpf_area_color_map,
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col2.plotly_chart(fig2, use_container_width=True)

                # Mostrar tabla completa con formato sin decimales en columnas específicas
                st.subheader("Tabla Completa - Consultorías VPF")
                st.dataframe(
                    df.style.format({
                        "Nº": "{:.0f}",
                        "Monto mensual": "{:,.0f}",
                        "cantidad meses": "{:.0f}",
                        "Total": "{:,.0f}"
                    }),
                    height=400
                )

            # Página DPP 2025 para Consultorías VPF
            elif page == "DPP 2025":
                st.header("VPF - Consultorías: DPP 2025")

                # Monto Total Deseado
                desired_total = deseados["VPF"]["Consultorías"]
                st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")

                st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")

                # Configuración de AgGrid para edición
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True, groupable=True)

                # Configurar columnas para mostrar sin decimales
                numeric_columns_aggrid = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in numeric_columns_aggrid:
                    gb.configure_column(
                        col,
                        type=['numericColumn'],
                        valueFormatter="Math.round(x).toLocaleString()"
                    )

                # Configurar la columna 'Total' para cálculo dinámico sin decimales
                gb.configure_column('Total', editable=False, valueGetter=JsCode("""
                    function(params) {
                        return Math.round(
                            Number(params.data['Nº']) * Number(params.data['Monto mensual']) * 1.6 * Number(params.data['cantidad meses'])
                        );
                    }
                """))

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
                essential_cols = ['Cargo', 'VPF/AREA', 'Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in essential_cols:
                    if col not in edited_df.columns:
                        st.error(f"La columna '{col}' está ausente en los datos editados.")
                        st.stop()

                # Limpiar y convertir columnas numéricas
                numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
                for col in numeric_columns:
                    edited_df[col] = pd.to_numeric(edited_df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

                # Recalcular 'Total' si es necesario
                edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)

                # Calcular métricas sin decimales
                total_sum = edited_df['Total'].sum()
                difference = desired_total - total_sum

                # Mostrar métricas sin decimales
                col1, col2 = st.columns(2)
                col1.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
                col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")

                # Resumen por Cargo y VPF/AREA
                summary_cargo = edited_df.groupby('Cargo')['Total'].sum().reset_index()
                summary_vpf_area = edited_df.groupby('VPF/AREA')['Total'].sum().reset_index()

                # Crear gráficos de dona actualizados
                col3, col4 = st.columns(2)

                # Gráfico de Dona: Montos Totales por Cargo (Actualizado)
                fig3 = crear_dona(
                    df=summary_cargo,
                    nombres='Cargo',
                    valores='Total',
                    titulo="Montos Totales por Cargo (Actualizado)",
                    color_map=vpf_area_color_map,
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col3.plotly_chart(fig3, use_container_width=True)

                # Gráfico de Dona: Distribución por VPF/AREA (Actualizado)
                fig4 = crear_dona(
                    df=summary_vpf_area,
                    nombres='VPF/AREA',
                    valores='Total',
                    titulo="Distribución por VPF/AREA (Actualizado)",
                    color_map=vpf_area_color_map,
                    hole=0.5,        # Aumento del hole para anillo más delgado
                    height=300,      # Reducción de tamaño del gráfico
                    margin_l=50      # Ajuste de márgenes
                )
                col4.plotly_chart(fig4, use_container_width=True)

                # Guardar datos editados en cache
                save_to_cache(edited_df, 'VPF', 'Consultorías')

                # Descargar tabla modificada sin decimales
                st.subheader("Descargar Tabla Modificada - Consultorías VPF")
                edited_df['Total'] = edited_df['Total'].round(0)
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada_consultorias_vpf.csv", mime="text/csv")

    elif main_page == "PRE":
        # Aquí debes implementar la lógica específica para la página PRE
        st.header("PRE - Página en Desarrollo")
        st.write("Aquí puedes agregar las funcionalidades específicas para PRE.")
        # Ejemplo de estructura similar a VPO y VPD
        # Puedes replicar el manejo de vistas, subpáginas, autenticación de datos, etc.

    elif main_page == "Consolidado":
        create_consolidado(deseados)

# Ejecutar la función según la selección
handle_page(main_page)
