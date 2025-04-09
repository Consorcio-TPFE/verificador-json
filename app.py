import streamlit as st
from json_para_df.planejado import process_planejado
from json_para_df.previsto import process_previsto
from json_para_df.producao import process_production
import pandas as pd

st.set_page_config(layout="wide")


# Opções dos arquivos/áreas
arquivos = ["PRODUÇÃO", "PREVISTO", "PLANEJADO"]

# Obtém os query parameters atuais (caso precise usá-los em outra parte)
query_params = st.experimental_get_query_params()

# Função para atualizar os query parameters conforme a seleção
def update_params():
    st.experimental_set_query_params(arquivo=st.session_state.arquivo)

# Cria um selectbox que atualiza os parâmetros da URL quando a seleção muda
selected_arquivo = st.selectbox("Selecionar arquivo", arquivos, key="arquivo", on_change=update_params)

# Definindo os caminhos para os arquivos JSON
PREVISTO_FILE = r"C:\Users\AndréTakeoLoschnerFu\OneDrive - TPF-EGC\Documentos\Entregas-json\jsons-07-04-2025\previsto-exportacao-wbs-2025-04-07T15-37-17.json"
PRODUCAO_FILE = r"C:\Users\AndréTakeoLoschnerFu\OneDrive - TPF-EGC\Documentos\Entregas-json\jsons-07-04-2025\producao-exportacao-wbs-2025-04-07T15-37-17.json"
PLANEJADO_FILE = r"C:\Users\AndréTakeoLoschnerFu\OneDrive - TPF-EGC\Documentos\Entregas-json\jsons-07-04-2025\planejado-exportacao-wbs-2025-04-07T15-37-17.json"


def get_erros(df: pd.DataFrame, titulo=None, colunas =None):
    st.markdown(f"## {titulo}")
    if df.empty or df[~df['is_ok']].copy().empty:
        return st.markdown("#### sem erros")
    if not colunas:
        return st.dataframe(df[~df['is_ok']].copy())
    return st.dataframe(df[~df['is_ok']].copy()[colunas])

# Processa os dados de acordo com a seleção
if selected_arquivo == "PRODUÇÃO":
    df_codes, df_trechos, df_ramais, df_localizadas = process_production(PRODUCAO_FILE)

    st.markdown(f"# Produção (Códigos WBS PAI)")
    df_codes[(~df_codes['is_ok']) | (df_codes['duplicado'])]

    st.markdown("# Trechos")
    print(df_trechos.columns)
    get_erros(df_trechos, "Lineares", ['contrato', 'codigo', 'tipo', 'jusante', 'montante', 'extensao',
       'diametro', 'material', 'metodo_exec', 'endereco'])

    get_erros(df_ramais, "Ramais")
    get_erros(df_localizadas, "Localizadas")




elif selected_arquivo == "PREVISTO":
    df_linear, df_linear_trechos, df_localizada, df_ramais, df_economias = process_previsto(PREVISTO_FILE)
    st.markdown("# Previsto")
    get_erros(df_linear, "Lineares")
    get_erros(df_linear_trechos, "Trechos Lineares")
    get_erros(df_localizada, "Localizadas")
    get_erros(df_ramais, "Ramais")
    get_erros(df_economias, "Economias")
    
elif selected_arquivo == "PLANEJADO":
    df_planejado = process_planejado(PLANEJADO_FILE)
    st.markdown("# Planejado")
    get_erros(df_planejado, "")

