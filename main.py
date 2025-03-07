import pandas as pd
import numpy as np
import json
import ast
import chardet
import re
import logging
from dotenv import load_dotenv
import os
from datetime import datetime

# Configuração básica do log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =============================================================================
# Carregar municípios a partir de um arquivo JSON
# =============================================================================
def load_municipios(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            municipios = json.load(file)
        logging.info("Municípios carregados com sucesso.")
        return municipios
    except FileNotFoundError:
        logging.error(f"Erro: O arquivo '{json_path}' de municípios não foi encontrado.")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Erro ao decodificar o JSON de municípios: {e}")
        raise

# Exemplo de caminho para o arquivo de municípios
municipios_json_path = os.getenv("MUNICIPIOS_JSON_PATH", "municipios.json")
municipios = load_municipios(municipios_json_path)
df_municipios = pd.DataFrame(list(municipios.items()), columns=["cod", "Municipio"])

# =============================================================================
# Funções auxiliares para carregar JSON
# =============================================================================
def detect_encoding(file_path):
    logging.info(f"Detectando encoding do arquivo: {file_path}")
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
    encoding = result['encoding']
    logging.info(f"Encoding detectado: {encoding}")
    return encoding

def load_json(file_path, encoding=None):
    if encoding is None:
        encoding = detect_encoding(file_path)
    try:
        logging.info(f"Carregando JSON do arquivo: {file_path}")
        with open(file_path, 'r', encoding=encoding) as file:
            data = json.load(file)
        logging.info("JSON carregado com sucesso.")
        return data
    except FileNotFoundError:
        logging.error(f"Erro: O arquivo '{file_path}' não foi encontrado.")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Erro ao decodificar o JSON: {e}")
        raise

# =============================================================================
# Processamento dos dados PREVISTOS
# =============================================================================
def process_previsto(file_path):
    data = load_json(file_path)
    linear = []
    localizada = []
    ramais = []
    economias = []
    logging.info("Iniciando o processamento dos dados previstos.")
    for contrato_item in data:
        contrato = contrato_item.get('contrato')
        if contrato_item.get('linear'):
            for item in contrato_item.get('linear'):
                item['contrato'] = contrato
                item['n_trechos'] = len(item.get('trechos', []))
                linear.append(item)
        if contrato_item.get('localizada'):
            for item in contrato_item.get('localizada'):
                item['contrato'] = contrato
                localizada.append(item)
        if contrato_item.get('ramais'):
            for item in contrato_item.get('ramais'):
                item['contrato'] = contrato
                ramais.append(item)
        if contrato_item.get('economias'):
            for item in contrato_item.get('economias'):
                item['contrato'] = contrato
                economias.append(item)
    df_linear = pd.DataFrame(linear)
    if 'trechos' in df_linear.columns:
        df_linear['trechos'] = df_linear['trechos'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        df_linear = df_linear.explode('trechos', ignore_index=True)
        if not df_linear.empty and isinstance(df_linear.iloc[0]['trechos'], dict):
            trechos_expanded = pd.json_normalize(df_linear['trechos'])
            df_linear = pd.concat([df_linear.drop(columns=['trechos']), trechos_expanded], axis=1)
    df_localizada = pd.DataFrame(localizada)
    df_ramais = pd.DataFrame(ramais)
    df_economias = pd.DataFrame(economias)
    logging.info("Processamento de dados previstos concluído.")
    return df_linear, df_localizada, df_ramais, df_economias

# =============================================================================
# Função para extrair código do município
# =============================================================================
def find_municipio_code(texto):
    valor = texto.rstrip('0')
    return valor[-5:-2]

# =============================================================================
# Carregar variáveis de ambiente e processar dados
# =============================================================================
load_dotenv()
previsto = os.getenv("PREVISTO_JSON_PATH")
if not previsto:
    logging.error("O caminho para o arquivo JSON de previsto não foi encontrado na variável de ambiente.")
    raise ValueError("Caminho do JSON não definido.")

df_linear, df_localizada, df_ramais, df_economias = process_previsto(previsto)

# =============================================================================
# Processamento dos registros sem endereço em 'localizada'
# =============================================================================
sem_endereco = df_localizada[(df_localizada['endereco'] == '') | (df_localizada['endereco'].isna())].copy()
if not sem_endereco.empty:
    sem_endereco['cod'] = sem_endereco['codigo'].apply(find_municipio_code)
    sem_endereco = pd.merge(sem_endereco, df_municipios, on='cod', how='left')
    logging.info(f"{len(sem_endereco)} registros de 'localizada' sem endereço encontrados.")
else:
    logging.info("Nenhum registro sem endereço encontrado em 'localizada'.")

# =============================================================================
# Geração do Excel com múltiplas sheets (dados com erros e registros sem endereço)
# =============================================================================
sheets = {}

# Validação para 'localizadas' incompletas (exceto ausência de endereço)
mask_localizada_incomplete = (
    (df_localizada['codigo'].isnull() | (df_localizada['codigo'] == '')) |
    (df_localizada['descricao'].isnull() | (df_localizada['descricao'] == ''))
)
df_localizada_incomplete = df_localizada[mask_localizada_incomplete].copy()
if not df_localizada_incomplete.empty:
    sheets['Localizadas_Incompletas'] = df_localizada_incomplete

# Adiciona a sheet com os registros sem endereço (enriquecidos com o município)
if not sem_endereco.empty:
    sheets['Localizadas_Sem_Endereco'] = sem_endereco

if not sheets:
    sheets['Sem_Erros'] = pd.DataFrame({"Mensagem": ["Nenhum erro encontrado."]})
    logging.info("Nenhum erro encontrado em todas as validações.")

# =============================================================================
# Gerar o nome do arquivo Excel com data e horário
# =============================================================================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f'checagens_formatado_{timestamp}.xlsx'
with pd.ExcelWriter(output_file) as writer:
    for sheet_name, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)
logging.info(f"Arquivo '{output_file}' gerado com sucesso.")
