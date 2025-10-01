#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo para processamento de dados previstos a partir de arquivos JSON.
Este script valida, organiza e processa itens com base na estrutura definida
nas classes: Campo, Linear, Trecho, Localizada, Ramal e Economia.
"""

# =============================================================================
# Imports e Configurações Iniciais
# =============================================================================
import json
import logging
import pandas as pd
import os
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# Configurações Iniciais
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
load_dotenv()


# Configuração básica do logging

# =============================================================================
# Configurações Globais
# =============================================================================
#PREVISTO_JSON_FILE = r"C:\Users\AndréTakeoLoschnerFu\OneDrive - TPF-EGC\Documentos\Entregas-json\jsons-07-04-2025\previsto-exportacao-wbs-2025-04-07T15-37-17.json"

#PREVISTO_JSON_FILE = os.getenv('PREVISTO_JSON_FILE')

# =============================================================================
# Classes de Validação e Representação dos Dados
# =============================================================================

class Campo:
    """
    Classe para definição de campos com seu nome, tipo, obrigatoriedade
    e aceitação de nulos, além de métodos para validação dos valores.
    """
    def __init__(self, nome: str, tipo=str, obrigatorio=False, pode_nulo=False, opcoes=None):
        self.nome = nome
        self.tipo = tipo
        self.obrigatorio = obrigatorio
        self.pode_nulo = pode_nulo
        self.opcoes = opcoes

    def validar(self, valor, pattern=None):
        erros = []
        # Verifica se o valor é nulo (NaN ou None) usando pd.isna
        if pd.isna(valor):
            if not self.pode_nulo:
                erros.append(f'Campo: {self.nome} não pode ser nulo')
            return erros
        
        # Validação específica de acordo com o tipo do campo
        if self.tipo in [int, float]:
            erros.extend(self.validar_numero(valor))
        elif self.tipo == str:
            erros.extend(self.validar_texto(valor, pattern))
        
        return erros

    def validar_numero(self, valor):
        erros = []
        # Aqui, a verificação de nulo já foi feita na função 'validar'
        if not isinstance(valor, (int, float)):
            erros.append(f'Campo: {self.nome}, tipo errado {self.tipo} -> {type(valor)}')
        else:
            if round(valor, 3) < 0:
                erros.append(f'Campo: {self.nome}, valor negativo')
        return erros

    def validar_texto(self, valor, pattern=None):
        erros = []
        if pattern:
            # Aqui pode ser implementada a validação com regex, se necessário
            print('regex')
        
        if not isinstance(valor, str):
            erros.append(f'Campo: {self.nome}, tipo errado {self.tipo} -> {type(valor)}')

        elif self.obrigatorio and valor.strip() == "":
            erros.append(f'Campo: {self.nome}, está vazio')

        elif self.opcoes and valor not in self.opcoes:
            erros.append(f'Campo: {self.nome}, valor não permitido -> {valor} (opções: {self.opcoes})')
        
        return erros



class Linear:
    """
    Representa um item linear com atributos como código, descrição, unidade,
    quantidade prevista, tipo de conduto, PEP e valor.
    """
    def __init__(self, data, contrato=None):
        self.contrato = contrato
        self.codigo = data.get("codigo")
        self.descricao = data.get("descricao")
        self.unidade = data.get("unidade")
        self.quant_prevista = data.get("quant_prevista")
        self.tipo_conduto = data.get("tipo_conduto")
        self.PEP = data.get("PEP")
        self.valor = data.get("valor")
        self.errors, self.is_ok = self.validate()

    def to_dict(self):
        return {
            "contrato": self.contrato,
            "codigo": self.codigo,
            "descricao": self.descricao,
            "unidade": self.unidade,
            "quant_prevista": self.quant_prevista,
            "tipo_conduto": self.tipo_conduto,
            "PEP": self.PEP,
            "valor": self.valor,
            "errors": self.errors,
            "is_ok": self.is_ok,
        }

    def validate(self):
        errors = []
        errors.extend(Campo('codigo', str, True).validar(self.codigo))
        errors.extend(Campo('descricao', str, True).validar(self.descricao))
        errors.extend(Campo('unidade', str, False).validar(self.unidade))
        errors.extend(Campo('quant_prevista', float, True).validar(self.quant_prevista))

        #^(rce)|(ct)|(it)|(em)|(lr)|(in)|(ad)|(rd)
        errors.extend(Campo('tipo_conduto', str, False, False, ["RCE", "CT", "IT", "EM", "LR", "IN", "AD", "RD"]).validar(self.tipo_conduto))
        errors.extend(Campo('PEP', str, True).validar(self.PEP))
        errors.extend(Campo('valor', float, False).validar(self.valor))
        return errors, len(errors) == 0


class Trecho:
    """
    Representa um trecho linear previsto, com dados de jusante, montante, extensão,
    diâmetro, material, método de execução e endereço.
    """
    def __init__(self, data, contrato=None, codigo=None):
        self.contrato = contrato
        self.codigo = codigo
        self.jusante = data['jusante']['id'] if isinstance(data.get('jusante'), dict) else data.get('jusante')
        self.montante = data['montante']['id'] if isinstance(data.get('montante'), dict) else data.get('montante')
        self.extensao = data.get('extensao')
        self.diametro = data.get('diametro')
        self.material = data.get('material')
        self.metodo_exec = data.get('metodo_exec')
        self.detalhe_metodo = data.get('detalhe_metodo')
        self.endereco = data.get('endereco')
        self.errors, self.is_ok = self.validate()

    def to_dict(self):
        return {
            'contrato': self.contrato,
            'codigo': self.codigo,
            'jusante': self.jusante,
            'montante': self.montante,
            'extensao': self.extensao,
            'diametro': self.diametro,
            'material': self.material,
            'metodo_exec': self.metodo_exec,
            'detalhe_metodo': self.detalhe_metodo,
            'endereco': self.endereco,
            'errors': self.errors,
            'is_ok': self.is_ok,
            'merged': str(self.contrato) + " | " + str(self.codigo) + " | " + str(self.jusante) + " | " +
                      str(self.montante) + " | " + str(self.material) + " | " + str(self.metodo_exec)
        }
    
    def validate(self):
        errors = []
        errors.extend(Campo('jusante', str, True).validar(self.jusante))
        errors.extend(Campo('montante', str, True).validar(self.montante))
        errors.extend(Campo('extensao', float, True, False).validar(self.extensao))
        errors.extend(Campo('diametro', int, False, True).validar(self.diametro))
        errors.extend(Campo('material', str, False, True, ['PVC', 'PEAD', 'CA', 'MBV', 'FoFo', 'ACO']).validar(self.material))
        errors.extend(Campo('metodo_exec', str, False, True, ['VCA', 'MND', 'AE', 'AEREO']).validar(self.metodo_exec))
        errors.extend(Campo('detalhe_metodo', str, False, True, ['HDD', 'VCA','FD', 'TC', 'NATM', 'TL', 'TRAVESSIA', 'APOIADO', 'AE']).validar(self.detalhe_metodo))
        errors.extend(Campo('endereco', str, True).validar(self.endereco))
        return errors, len(errors) == 0


class Localizada:
    """
    Representa uma localização prevista, com código, descrição, endereço,
    número de itens e PEP.
    """
    def __init__(self, data, contrato=None):
        self.contrato = contrato
        self.codigo = data.get('codigo')
        self.descricao = data.get('descricao')
        self.itens = len(data.get('itens'))
        self.endereco = data.get('endereco')
        self.PEP = data.get('PEP')
        self.errors, self.is_ok = self.validate()

    def to_dict(self):
        return {
            'contrato': self.contrato,
            'codigo': self.codigo,
            'descricao': self.descricao,
            'endereco': self.endereco,
            'PEP': self.PEP,
            'itens': self.itens,
            'errors': self.errors,
            'is_ok': self.is_ok,
        }

    def validate(self):
        errors = []
        errors.extend(Campo('codigo', str, True).validar(self.codigo))
        errors.extend(Campo('descricao', str, True).validar(self.descricao))
        errors.extend(Campo('endereco', str, True).validar(self.endereco))
        # Se necessário, adicionar validação para PEP.
        return errors, len(errors) == 0


class Ramal:
    """
    Representa um ramal previsto com atributos como código, tipo, status,
    descrição, quantidade prevista, PEP e valor.
    """
    def __init__(self, data, contrato=None):
        self.contrato = contrato
        self.codigo = data.get('codigo')
        self.tipo = data.get('tipo')
        self.completa = data.get('completa')
        self.descricao = data.get('descricao')
        self.quant_prevista = data.get('quant_prevista')
        self.PEP = data.get('PEP')
        self.valor = data.get('valor')
        self.errors, self.is_ok = self.validate()

    def to_dict(self):
        return {
            'contrato': self.contrato,
            'codigo': self.codigo,
            'tipo': self.tipo,
            'completa': self.completa,
            'descricao': self.descricao,
            'quant_prevista': self.quant_prevista,
            'PEP': self.PEP,
            'valor': self.valor,
            'errors': self.errors,
            'is_ok': self.is_ok
        }
    
    def validate(self):
        errors = []
        errors.extend(Campo('codigo', str, True).validar(self.codigo))
        errors.extend(Campo('tipo', str, True, ['PA', 'TA', 'E', 'TO', 'PO']).validar(self.tipo))
        # A validação para 'completa' pode ser implementada se necessário.
        errors.extend(Campo('descricao', str, True).validar(self.descricao))
        errors.extend(Campo('quant_prevista', int, False).validar(self.quant_prevista))
        # Se necessário, adicionar validação para PEP.
        errors.extend(Campo('valor', float, True).validar(self.valor))
        return errors, len(errors) == 0


class Economia:
    """
    Representa um item de economia previsto contendo código e quantidade prevista.
    """
    def __init__(self, data, contrato=None):
        self.contrato = contrato
        self.codigo = data.get('codigo')
        self.quant_prevista = data.get('quant_prevista')
        self.errors, self.is_ok = self.validate()

    def to_dict(self):
        return {
            'contrato': self.contrato,
            'codigo': self.codigo,
            'quant_prevista': self.quant_prevista,
            'errors': self.errors,
            'is_ok': self.is_ok
        }
    
    def validate(self):
        errors = []
        errors.extend(Campo('codigo', str, True).validar(self.codigo))
        errors.extend(Campo('quant_prevista', int, True).validar(self.quant_prevista))
        return errors, len(errors) == 0


# =============================================================================
# Funções Auxiliares
# =============================================================================
def load_json(file_path):
    """
    Carrega e decodifica um arquivo JSON.
    Retorna o conteúdo do arquivo ou None em caso de erro.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Arquivo {file_path} não encontrado.")
        return None
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar o arquivo JSON: {file_path}")
        return None


# =============================================================================
# Execução Principal (Caso o módulo seja executado diretamente)
# =============================================================================
import os
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

municipios_json_path = os.getenv("MUNICIPIOS_JSON_PATH", "municipios.json")
municipios = load_municipios(municipios_json_path)
df_municipios = pd.DataFrame(list(municipios.items()), columns=["cod", "Municipio"])


# =============================================================================
# Função para extrair código do município
# =============================================================================

# certos contratos seguem um padrão no código wbs: item(8) + D2(fator fisico d(2)) + D3(tipo obra d(2)) + Municipio(d(3))
from bd import conectar_bd, executar_select

def contratos_integra():
    # conectar ao bd, e pegar os dados dessa query
    conn = conectar_bd()

    query = "SELECT DISTINCT CONTRATO FROM FIN_BD_WBS WHERE CADASTRO_APROVADO_UN IS NOT NULL;"
    return list(executar_select(query, conn)['CONTRATO'])

def find_municipio_code(row):
    # Exemplo simples: remove zeros à direita e pega 3 dígitos do final
    if row['integra']:
        if pd.isna(row['codigo']) or not isinstance(row['codigo'], str):
            return ""
        else:
            return row['codigo'][12:15]
    else:
        return ""



# =============================================================================
# Processamento dos Dados Previstos
# =============================================================================
def process_previsto(file_path):
    """
    Processa os dados previstos a partir do arquivo JSON especificado.
    Retorna DataFrames com os dados de Linear, Trechos, Localizada, Ramais e Economias.
    """
    logging.info("Iniciando o processamento dos dados previstos.")
    data = load_json(file_path)
    
    # Listas para armazenar os registros processados
    linear = []
    linear_trechos = []
    localizada = []
    ramais = []
    economias = []
    
    for contrato_item in data:
        contrato = contrato_item.get('contrato')
        
        # Processamento de itens lineares e seus trechos
        for linear_item in contrato_item.get('linear', []):
            linear_obj = Linear(linear_item, contrato)
            linear.append(linear_obj.to_dict())
            for trecho_item in linear_item.get('trechos', []):
                trecho_obj = Trecho(trecho_item, contrato, linear_item.get('codigo'))
                linear_trechos.append(trecho_obj.to_dict())
        
        # Processamento de itens localizados
        for localizada_item in contrato_item.get('localizada', []):
            localizada_obj = Localizada(localizada_item, contrato)
            localizada.append(localizada_obj.to_dict())
        
        # Processamento de ramais
        for ramal_item in contrato_item.get('ramais', []):
            ramal_obj = Ramal(ramal_item, contrato)
            ramais.append(ramal_obj.to_dict())
        
        # Processamento de economias
        for economia_item in contrato_item.get('economias', []):
            economia_obj = Economia(economia_item, contrato)
            economias.append(economia_obj.to_dict())

    # Criação dos DataFrames com os dados processados
    df_linear = pd.DataFrame(linear)
    df_linear_trechos = pd.DataFrame(linear_trechos)
    df_localizada = pd.DataFrame(localizada)
    df_ramais = pd.DataFrame(ramais)
    df_economias = pd.DataFrame(economias)

    integra = contratos_integra()

    df_localizada['integra'] = df_localizada['contrato'].apply(lambda x: x in integra)
    df_localizada['cod'] = df_localizada.apply(find_municipio_code, axis=1)
    df_localizada = pd.merge(df_localizada, df_municipios, on='cod', how='left')

    logging.info("Processamento de dados previstos concluído.")
    return df_linear, df_linear_trechos, df_localizada, df_ramais, df_economias
