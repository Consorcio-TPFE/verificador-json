import pandas as pd
import numpy as np
import json
import ast
import chardet
import re
import logging
from dotenv import load_dotenv
import os


# Configuração básica do log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
# Processamento dos dados de PRODUÇÃO
# =============================================================================
def process_production(file_path):
    """
    Processa os dados de produção dos contratos conforme a estrutura descrita.
    """
    data = load_json(file_path)
    codes = []
    details = []
    logging.info("Iniciando o processamento dos dados de produção.")
    for entry in data:
        mes_ref = entry.get('mes_ref')
        for prod in entry.get('producao', []):
            contrato = prod.get('contrato')
            for item in prod.get('itens', []):
                n_detalhes = len(item.get('producao', []))
                codes.append({
                    'mes_ref': mes_ref,
                    'contrato': contrato,
                    'codigo': item.get('codigo'),
                    'executado': item.get('executado'),
                    'concluido': item.get('concluido'),
                    'n_detalhes': n_detalhes
                })
                for det in item.get('producao', []):
                    # Identifica o tipo com base nas chaves presentes
                    if 'jusante' in det and 'montante' in det:
                        jusante = det.get('jusante')
                        if isinstance(jusante, dict):
                            jusante = jusante.get('id')
                        montante = det.get('montante')
                        if isinstance(montante, dict):
                            montante = montante.get('id')
                        detail_entry = {
                            'contrato': contrato,
                            'codigo': item.get('codigo'),
                            'tipo': 'linear',
                            'jusante': jusante,
                            'montante': montante,
                            'extensao': det.get('extensao'),
                            'diametro': det.get('diametro'),
                            'material': det.get('material'),
                            'metodo_exec': det.get('metodo_exec'),
                            'endereco': det.get('endereco')
                        }
                        details.append(detail_entry)
                    elif 'posicao' in det:
                        detail_entry = {
                            'contrato': contrato,
                            'codigo': item.get('codigo'),
                            'tipo': 'ramal',
                            'posicao': det.get('posicao'),
                            'completo': det.get('completo'),
                            'endereco': det.get('endereco')
                        }
                        details.append(detail_entry)
                    elif 'descricao' in det:
                        detail_entry = {
                            'contrato': contrato,
                            'codigo': item.get('codigo'),
                            'tipo': 'localizada',
                            'descricao': det.get('descricao'),
                            'num_inventario': det.get('num_inventario')
                        }
                        details.append(detail_entry)
                    else:
                        detail_entry = {
                            'contrato': contrato,
                            'codigo': item.get('codigo'),
                            'tipo': 'desconhecido',
                            'raw': det
                        }
                        details.append(detail_entry)
    df_codes = pd.DataFrame(codes)
    df_details = pd.DataFrame(details)
    logging.info(f"Processamento de produção concluído: {len(df_codes)} códigos e {len(df_details)} detalhes extraídos.")
    return df_codes, df_details

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
# Funções de validação com logs e mensagem de erro por linha
# =============================================================================
def validate_production_detail(row):
    errors = []
    if row['tipo'] == 'linear':
        for field in ['jusante', 'montante', 'extensao', 'diametro', 'material', 'metodo_exec', 'endereco']:
            if pd.isna(row.get(field)) or row.get(field) == '':
                errors.append(f"{field} ausente")
    elif row['tipo'] == 'ramal':
        for field in ['posicao', 'completo', 'endereco']:
            if pd.isna(row.get(field)) or row.get(field) == '':
                errors.append(f"{field} ausente")
    elif row['tipo'] == 'localizada':
        if pd.isna(row.get('descricao')) or row.get('descricao') == '':
            errors.append("descricao ausente")
    return "; ".join(errors)

def validate_linear_row(row):
    errors = []
    for field in ['codigo', 'descricao', 'quant_prevista', 'PEP']:
        if pd.isna(row.get(field)) or row.get(field) == '':
            errors.append(f"{field} ausente")
    if row.get('n_trechos', 0) > 0:
        for field in ['extensao', 'endereco']:
            if pd.isna(row.get(field)) or row.get(field) == '':
                errors.append(f"{field} ausente")
        if 'jusante.id' in row and (pd.isna(row.get('jusante.id')) or row.get('jusante.id') == ''):
            errors.append("jusante.id ausente")
    return "; ".join(errors)

def validate_localizada_row(row):
    errors = []
    for field in ['codigo', 'descricao', 'endereco']:
        if pd.isna(row.get(field)) or row.get(field) == '':
            errors.append(f"{field} ausente")
    return "; ".join(errors)

def validate_ramais_row(row):
    errors = []
    for field in ['descricao', 'tipo', 'completa']:
        if pd.isna(row.get(field)) or row.get(field) == '':
            errors.append(f"{field} ausente")
    return "; ".join(errors)

def validate_economias_row(row):
    errors = []
    if pd.isna(row.get('codigo')) or row.get('codigo') == '':
        errors.append("codigo ausente")
    if 'quantidade' in row:
        if pd.isna(row.get('quantidade')) or row.get('quantidade') == '':
            errors.append("quantidade ausente")
    return "; ".join(errors)

# =============================================================================
# Caminhos para os arquivos JSON (ajuste conforme necessário)
# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# =============================================================================
producao = os.getenv("PRODUCAO_JSON_PATH")
previsto = os.getenv("PREVISTO_JSON_PATH")

if not producao or not previsto:
    logging.error("Os caminhos para os arquivos JSON não foram encontrados nas variáveis de ambiente.")
    raise ValueError("Os caminhos para os arquivos JSON não foram encontrados nas variáveis de ambiente.")

# =============================================================================
# Processamento dos dados
# =============================================================================
try:
    df_prod_codes, df_prod_details = process_production(producao)
    logging.info(f"df_prod_codes: {len(df_prod_codes)} registros; df_prod_details: {len(df_prod_details)} registros")
except Exception as e:
    logging.error(f"Erro ao processar dados de produção: {e}")

try:
    df_linear, df_localizada, df_ramais, df_economias = process_previsto(previsto)
    logging.info(f"df_linear: {len(df_linear)} registros; df_localizada: {len(df_localizada)} registros; "
                 f"df_ramais: {len(df_ramais)} registros; df_economias: {len(df_economias)} registros")
except Exception as e:
    logging.error(f"Erro ao processar dados previstos: {e}")

# =============================================================================
# Checagens para dados de PRODUÇÃO
# =============================================================================
logging.info("Validando códigos de produção...")
df_prod_codes_null = df_prod_codes[df_prod_codes.isnull().any(axis=1)].copy()
if not df_prod_codes_null.empty:
    df_prod_codes_null["erro"] = "Campos nulos ou vazios"
    logging.info(f"{len(df_prod_codes_null)} registros com campos nulos.")
    
df_prod_codes_negative = df_prod_codes[df_prod_codes['executado'] < 0].copy()
if not df_prod_codes_negative.empty:
    df_prod_codes_negative["erro"] = "Valor 'executado' negativo"
    logging.info(f"{len(df_prod_codes_negative)} registros com 'executado' negativo.")
    
df_prod_codes_duplicates = df_prod_codes[df_prod_codes.duplicated(subset=['contrato', 'codigo'], keep=False)].copy()
if not df_prod_codes_duplicates.empty:
    df_prod_codes_duplicates["erro"] = "Registro duplicado de contrato e codigo"
    logging.info(f"{len(df_prod_codes_duplicates)} registros duplicados.")

logging.info("Validando detalhes de produção...")
df_prod_details["erro"] = df_prod_details.apply(validate_production_detail, axis=1)
df_prod_details_errors = df_prod_details[df_prod_details["erro"] != ""].copy()
if not df_prod_details_errors.empty:
    logging.info(f"{len(df_prod_details_errors)} detalhes de produção com erro.")

# =============================================================================
# Checagens para dados PREVISTOS
# =============================================================================
logging.info("Validando dados previstos para lineares...")
mask_linear_base = (
    (df_linear['codigo'].isnull() | (df_linear['codigo'] == '')) |
    (df_linear['descricao'].isnull() | (df_linear['descricao'] == '')) |
    (df_linear['quant_prevista'].isnull() | (df_linear['quant_prevista'] == '')) |
    (df_linear['PEP'].isnull() | (df_linear['PEP'] == ''))
)
mask_linear_trechos = (
    (df_linear['n_trechos'] > 0) & (
        (df_linear['extensao'].isnull() | (df_linear['extensao'] == '')) |
        (df_linear['endereco'].isnull() | (df_linear['endereco'] == '')) |
        (df_linear['jusante.id'].isnull() | (df_linear['jusante.id'] == ''))
    )
)
mask_linear = mask_linear_base | mask_linear_trechos
df_linear_incomplete = df_linear[mask_linear].copy()
if not df_linear_incomplete.empty:
    df_linear_incomplete["erro"] = df_linear_incomplete.apply(validate_linear_row, axis=1)
    logging.info(f"{len(df_linear_incomplete)} registros incompletos em lineares.")

logging.info("Validando dados previstos para localizadas...")
mask_localizada_base = (
    (df_localizada['codigo'].isnull() | (df_localizada['codigo'] == '')) |
    (df_localizada['descricao'].isnull() | (df_localizada['descricao'] == ''))
)
mask_localizada_endereco = (df_localizada['endereco'].isnull() | (df_localizada['endereco'] == ''))
mask_localizada = mask_localizada_base | mask_localizada_endereco
df_localizada_incomplete = df_localizada[mask_localizada].copy()
if not df_localizada_incomplete.empty:
    df_localizada_incomplete["erro"] = df_localizada_incomplete.apply(validate_localizada_row, axis=1)
    logging.info(f"{len(df_localizada_incomplete)} registros incompletos em localizadas.")

logging.info("Validando dados previstos para ramais...")
mask_ramais = (
    (df_ramais['descricao'].isnull() | (df_ramais['descricao'] == '')) |
    (df_ramais['tipo'].isnull() | (df_ramais['tipo'] == '')) |
    (df_ramais['completa'].isnull())
)
df_ramais_incomplete = df_ramais[mask_ramais].copy()
if not df_ramais_incomplete.empty:
    df_ramais_incomplete["erro"] = df_ramais_incomplete.apply(validate_ramais_row, axis=1)
    logging.info(f"{len(df_ramais_incomplete)} registros incompletos em ramais.")

logging.info("Validando dados previstos para economias...")
if 'quantidade' in df_economias.columns:
    mask_economias = (
        (df_economias['codigo'].isnull() | (df_economias['codigo'] == '')) |
        (df_economias['quantidade'].isnull() | (df_economias['quantidade'] == ''))
    )
else:
    logging.warning("A coluna 'quantidade' não foi encontrada em df_economias. Checando apenas 'codigo'.")
    mask_economias = (df_economias['codigo'].isnull() | (df_economias['codigo'] == ''))
df_economias_incomplete = df_economias[mask_economias].copy()
if not df_economias_incomplete.empty:
    df_economias_incomplete["erro"] = df_economias_incomplete.apply(validate_economias_row, axis=1)
    logging.info(f"{len(df_economias_incomplete)} registros incompletos em economias.")

# =============================================================================
# Preparando dicionário com as sheets somente se houver erros
# =============================================================================
sheets = {}

# Produção
if not df_prod_codes_null.empty:
    sheets['Prod_Nulls'] = df_prod_codes_null
if not df_prod_codes_negative.empty:
    sheets['Prod_Negativos'] = df_prod_codes_negative
if not df_prod_codes_duplicates.empty:
    sheets['Prod_Duplicados'] = df_prod_codes_duplicates
if not df_prod_details_errors.empty:
    sheets['Prod_Details_Errors'] = df_prod_details_errors

# Previsto
if not df_linear_incomplete.empty:
    sheets['Lineares_Incompletos'] = df_linear_incomplete
if not df_localizada_incomplete.empty:
    sheets['Localizadas_Incompletas'] = df_localizada_incomplete
if not df_ramais_incomplete.empty:
    sheets['Ramais_Incompletos'] = df_ramais_incomplete
if not df_economias_incomplete.empty:
    sheets['Economias_Incompletas'] = df_economias_incomplete

if not sheets:
    sheets['Sem_Erros'] = pd.DataFrame({"Mensagem": ["Nenhum erro encontrado."]})
    logging.info("Nenhum erro encontrado em todas as validações.")

# =============================================================================
# Gerando o Excel com múltiplas sheets (somente as que tiverem erros)
# =============================================================================
output_file = 'checagens_formatado.xlsx'
with pd.ExcelWriter(output_file) as writer:
    for sheet_name, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)
logging.info(f"Arquivo '{output_file}' gerado com sucesso.")
