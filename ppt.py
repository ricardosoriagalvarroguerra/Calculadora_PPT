import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
import os

# Funciones de cálculo
def calculate_total_misiones(row):
    return round(
        (row['Costo de Pasaje'] + (row['Alojamiento'] + row['Per-diem y Otros'] + row['Movilidad']) * row['Días']) * row['Cantidad de Funcionarios']
    )

def calculate_total_consultorias(row):
    return round(row['Nº'] * row['Monto mensual'] * row['cantidad meses'])

# Configuración de la página
st.set_page_config(page_title="Presupuesto", layout="wide")

# Función para guardar datos en cache
def save_to_cache(df, unidad, tipo):
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_file = f"{cache_dir}/{unidad}_{tipo}_DPP2025.csv"
    df.to_csv(cache_file, index=False)

# Función para procesar y mostrar la página de Misiones
def process_misiones_page(unit, tipo, page, deseados, use_objetivo):
    file_path = 'BDD_Ajuste.xlsx'
    sheet_name = f"Misiones_{unit}"
    cache_file = f'cache/{unit}_{tipo}_DPP2025.csv'

    def process_misiones_df(df):
        required_columns = ['País', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                            'Alojamiento', 'Per-diem y Otros', 'Movilidad']
        if use_objetivo:
            required_columns.append('Objetivo')
        for col in required_columns:
            if col not in df.columns:
                st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                st.stop()

        numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
                           'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

        if 'Total' not in df.columns or df['Total'].sum() == 0:
            df['Total'] = df.apply(calculate_total_misiones, axis=1)

        return df

    if page == "DPP 2025":
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file)
        else:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            df = process_misiones_df(df)
    else:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        df = process_misiones_df(df)

    if page == "Requerimiento del área":
        st.header(f"{unit} - Misiones: Requerimiento del área")
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
    elif page == "DPP 2025":
        desired_total = deseados[unit][tipo]
        st.header(f"{unit} - Misiones: DPP 2025")
        st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True, groupable=True)
        grid_options = gb.build()
        grid_response = AgGrid(df, gridOptions=grid_options, data_return_mode=DataReturnMode.FILTERED, update_mode='MODEL_CHANGED')
        edited_df = pd.DataFrame(grid_response['data'])

        edited_df['Total'] = edited_df.apply(calculate_total_misiones, axis=1)
        total_sum = edited_df['Total'].sum()
        difference = desired_total - total_sum

        st.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
        st.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")

        save_to_cache(edited_df, unit, tipo)

        st.download_button("Descargar CSV", data=edited_df.to_csv(index=False), file_name=f"{unit}_misiones_dpp2025.csv", mime="text/csv")

# Función para procesar y mostrar la página de Consultorías
def process_consultorias_page(unit, tipo, page, deseados):
    file_path = 'BDD_Ajuste.xlsx'
    sheet_name = f"Consultores_{unit}"
    cache_file = f'cache/{unit}_{tipo}_DPP2025.csv'

    def process_consultorias_df(df):
        required_columns = ['Cargo', f"{unit}/AREA", 'Nº', 'Monto mensual', 'cantidad meses', 'Total']
        for col in required_columns:
            if col not in df.columns:
                st.error(f"La columna '{col}' no existe en la hoja '{sheet_name}'.")
                st.stop()

        numeric_columns = ['Nº', 'Monto mensual', 'cantidad meses', 'Total']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

        if 'Total' not in df.columns or df['Total'].sum() == 0:
            df['Total'] = df.apply(calculate_total_consultorias, axis=1)

        return df

    if page == "DPP 2025":
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file)
        else:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            df = process_consultorias_df(df)
    else:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        df = process_consultorias_df(df)

    if page == "Requerimiento del área":
        st.header(f"{unit} - Consultorías: Requerimiento del área")
        st.dataframe(
            df.style.format({
                "Nº": "{:.0f}",
                "Monto mensual": "{:,.0f}",
                "cantidad meses": "{:.0f}",
                "Total": "{:,.0f}"
            }),
            height=400
        )
    elif page == "DPP 2025":
        desired_total = deseados[unit][tipo]
        st.header(f"{unit} - Consultorías: DPP 2025")
        st.subheader(f"Monto Total Deseado: {desired_total:,.0f} USD")

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True, groupable=True)
        grid_options = gb.build()
        grid_response = AgGrid(df, gridOptions=grid_options, data_return_mode=DataReturnMode.FILTERED, update_mode='MODEL_CHANGED')
        edited_df = pd.DataFrame(grid_response['data'])

        edited_df['Total'] = edited_df.apply(calculate_total_consultorias, axis=1)
        total_sum = edited_df['Total'].sum()
        difference = desired_total - total_sum

        st.metric("Monto Actual (USD)", f"{total_sum:,.0f}")
        st.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.0f}")

        save_to_cache(edited_df, unit, tipo)

        st.download_button("Descargar CSV", data=edited_df.to_csv(index=False), file_name=f"{unit}_consultorias_dpp2025.csv", mime="text/csv")

# Manejo de cada unidad
def handle_vpo_page(deseados):
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPO_view")
    if view == "Misiones":
        process_misiones_page("VPO", "Misiones", "DPP 2025", deseados, use_objetivo=False)
    elif view == "Consultorías":
        process_consultorias_page("VPO", "Consultorías", "DPP 2025", deseados)

def handle_vpd_page(deseados):
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPD_view")
    if view == "Misiones":
        process_misiones_page("VPD", "Misiones", "DPP 2025", deseados, use_objetivo=False)
    elif view == "Consultorías":
        process_consultorias_page("VPD", "Consultorías", "DPP 2025", deseados)

def handle_vpe_page(deseados):
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPE_view")
    if view == "Misiones":
        process_misiones_page("VPE", "Misiones", "DPP 2025", deseados, use_objetivo=False)
    elif view == "Consultorías":
        process_consultorias_page("VPE", "Consultorías", "DPP 2025", deseados)

def handle_vpf_page(deseados):
    view = st.sidebar.selectbox("Selecciona una vista:", ("Misiones", "Consultorías"), key="VPF_view")
    if view == "Misiones":
        process_misiones_page("VPF", "Misiones", "DPP 2025", deseados, use_objetivo=False)
    elif view == "Consultorías":
        process_consultorias_page("VPF", "Consultorías", "DPP 2025", deseados)

# Configuración de montos deseados
deseados = {
    "VPO": {"Misiones": 434707.0, "Consultorías": 547700.0},
    "VPD": {"Misiones": 168000.0, "Consultorías": 130000.0},
    "VPE": {"Misiones": 28200.0, "Consultorías": 179400.0},
    "VPF": {"Misiones": 138600.0, "Consultorías": 170000.0},
    "PRE": {"Misiones": 0.0, "Consultorías": 0.0}
}

# Main
if __name__ == "__main__":
    st.sidebar.title("Navegación")
    main_page = st.sidebar.selectbox("Selecciona una página principal:", ("VPO", "VPD", "VPE", "VPF", "PRE"))
    if main_page == "VPO":
        handle_vpo_page(deseados)
    elif main_page == "VPD":
        handle_vpd_page(deseados)
    elif main_page == "VPE":
        handle_vpe_page(deseados)
    elif main_page == "VPF":
        handle_vpf_page(deseados)
    elif main_page == "PRE":
        st.header("PRE - Página en Desarrollo")
