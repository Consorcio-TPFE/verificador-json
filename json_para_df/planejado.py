"""
Projeto de Planejamento - Exemplo de carregamento, validação e transformação de JSON em DataFrame

Referências:
- PEP 8 – Style Guide for Python Code: https://peps.python.org/pep-0008/
- python-dotenv documentation: https://pypi.org/project/python-dotenv/
- chardet: https://github.com/chardet/chardet
- pandas: https://pandas.pydata.org/docs/
"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import os
import json
import logging
from dotenv import load_dotenv

import pandas as pd
import chardet

# ------------------------------------------------------------------------------
# Configurações Iniciais
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
load_dotenv()

# Variável de ambiente para o caminho do arquivo JSON
PLANEJADO_JSON_PATH = os.getenv('PLANEJADO_JSON_PATH')

# ------------------------------------------------------------------------------
# Funções Auxiliares
# ------------------------------------------------------------------------------
def detect_encoding(file_path):
    """
    Detecta o encoding de um arquivo.
    
    :param file_path: Caminho do arquivo.
    :return: Encoding detectado.
    """
    logging.info(f"Detectando encoding do arquivo: {file_path}")
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
    encoding = result['encoding']
    logging.info(f"Encoding detectado: {encoding}")
    return encoding

def load_json(file_path, encoding=None):
    """
    Carrega um arquivo JSON utilizando o encoding apropriado.
    
    :param file_path: Caminho do arquivo JSON.
    :param encoding: Encoding a ser utilizado. Se None, detecta automaticamente.
    :return: Dados do JSON carregados.
    """
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

# ------------------------------------------------------------------------------
# Classes de Domínio
# ------------------------------------------------------------------------------
class Campo:
    """
    Classe para definição de campos com seu nome, tipo e obrigatoriedade,
    além de métodos para validação dos valores.
    """
    def __init__(self, nome: str, tipo=str, obrigatorio=False):
        self.nome = nome
        self.tipo = tipo
        self.obrigatorio = obrigatorio

    def validar(self, valor, pattern=None):
        """
        Valida o valor de acordo com o tipo e retorna uma lista de erros (se houver).
        """
        if self.tipo in [int, float]:
            return self.validar_numero(valor)
        elif self.tipo == str:
            return self.validar_texto(valor, pattern)
        return []

    def validar_numero(self, valor):
        erros = []
        if pd.isna(valor):
            erros.append(f'Campo: {self.nome}, valor é NaN')
            return erros

        if not isinstance(valor, (int, float)):
            erros.append(f'Campo: {self.nome}, tipo errado {self.tipo} -> {type(valor)}')
        
        if round(valor, 3) < 0:
            erros.append(f'Campo: {self.nome}, valor negativo')
        return erros

    def validar_texto(self, valor, pattern=None):
        erros = []
        if pattern:
            # Implementar validação com regex se necessário
            print('regex')

        if not isinstance(valor, str):
            erros.append(f'Campo: {self.nome}, tipo errado {self.tipo} -> {type(valor)}')
            return erros
        
        if self.obrigatorio and valor.strip() == "":
            erros.append(f'Campo: {self.nome}, está vazio')
        return erros

class Mes:
    """
    Representa um mês com seus dados de projeção.
    """
    def __init__(self, contrato, codigo, data):
        self.contrato = contrato
        self.codigo = codigo
        self.mes = data['mes']
        self.quant_projetada = data['quant_projetada']
        self.erros, self.is_ok = self.validate()
    
    def to_dict(self):
        return {
            'contrato': self.contrato,
            'codigo': self.codigo,
            'mes': self.mes,
            'quant_projetada': self.quant_projetada,
            'errors': self.erros,
            'is_ok': self.is_ok
        }
    
    def validate(self):
        erros = []
        campo_mes = Campo('mes', str, True)
        campo_quant_projetada = Campo('quant_projetada', float, True)

        erros.extend(campo_mes.validar(self.mes))
        erros.extend(campo_quant_projetada.validar(self.quant_projetada))
        return erros, len(erros) == 0 

class ProjecaoProd:
    """
    Representa a projeção de produção para um determinado contrato.
    """
    def __init__(self, contrato, projecao_prod):
        self.contrato = contrato
        self.codigo = projecao_prod['codigo']
        self.meses = projecao_prod['meses']
    
    def to_dict(self):
        return [Mes(self.contrato, self.codigo, mes).to_dict() for mes in self.meses]

class Contrato:
    """
    Representa um contrato contendo uma lista de projeções de produção.
    """
    def __init__(self, contrato, list_projecao_prod):
        self.contrato = contrato
        self.list_projecao_prod = list_projecao_prod

    def to_dict(self):
        result = []
        for projecao_prod in self.list_projecao_prod:
            result.extend(ProjecaoProd(self.contrato, projecao_prod).to_dict())
        return result

class Planejado:
    """
    Processa os dados planejados e os transforma em um DataFrame.
    """
    def __init__(self, data):
        self.mes_ref = data[0]['mes_ref']
        self.itens = data[0]['itens']
        self.df = pd.DataFrame(self.to_dict())

    def to_dict(self):
        result = []
        for item in self.itens:
            contrato = item['contrato']
            projecao_produtos = item['projecao_prod']
            result.extend(Contrato(contrato, projecao_produtos).to_dict())
        return result

# ------------------------------------------------------------------------------
# Execução Principal
# ------------------------------------------------------------------------------
def process_planejado(path):
    try:
        # Carrega o JSON utilizando o caminho definido na variável de ambiente
        planejado_data = load_json(path)
        planejado = Planejado(planejado_data)
        df = planejado.df
        # Exibe as primeiras linhas do DataFrame
        return df
    except Exception as e:
        logging.error("Ocorreu um erro na execução principal.", exc_info=e)