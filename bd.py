import os
import json
import logging
import pyodbc
import pandas as pd
from decimal import Decimal
from datetime import datetime
import requests
import urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def conectar_bd() -> pyodbc.Connection:
    try:
        conexao = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=HWC-HWP-5176900;'
            'DATABASE=SABESP_BI;'
            'UID=sabesp_bi;'
            'PWD=S5c0W37k#3QR;'
        )
        logger.info("Conexão com o banco de dados estabelecida com sucesso.")
        return conexao
    except Exception as e:
        logger.error(f"Falha ao conectar no banco de dados: {e}")
        return None

def executar_select(consulta_sql: str, conexao: pyodbc.Connection) -> pd.DataFrame:
    if conexao is None:
        logger.error("Conexão com o banco não fornecida. Não é possível executar a consulta.")
        return None

    try:
        cursor = conexao.cursor()
        cursor.execute(consulta_sql)
        resultado = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame.from_records(resultado, columns=colunas)
        cursor.close()
        return df
    except Exception as e:
        logger.error(f"Erro ao executar SELECT: {e}")
        return None
