# =============================================================================
# Imports
# =============================================================================
import json
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# =============================================================================
# Configurações Globais
# =============================================================================


# =============================================================================
# Classes de Validação e Representação dos Dados
# =============================================================================
class Campo:
    """
    Classe para definição de campos com seu nome, tipo e obrigatoriedade,
    além de métodos para validação dos valores.
    """
    def __init__(self, nome: str, tipo=str, obrigatorio=False, opcoes=None):
        self.nome = nome
        self.tipo = tipo
        self.obrigatorio = obrigatorio
        self.opcoes = opcoes

    def validar(self, valor, pattern=None):
        if self.tipo in [int, float]:
            return self.validar_numero(valor)
        elif self.tipo == str:
            return self.validar_texto(valor, pattern)
        return []

    def validar_numero(self, valor):
        erros = []
        if pd.isna(valor) or type(valor) == type(None):
            # erros.append(f'Campo: {self.nome}, valor nulo')
            erros.append({'campo': self.nome, 'erro': "Valor nulo"})
            return erros

        if not isinstance(valor, (int, float)):
            # erros.append(f'Campo: {self.nome}, tipo errado {self.tipo} -> {type(valor)}')
            erros.append({'campo': self.nome, 'erro': f"Valo com tipo {type(valor)}, mas deveria ser {self.tipo}"})

        
        if round(valor, 3) < 0:
            # erros.append(f'Campo: {self.nome}, valor negativo')
            erros.append({'campo': self.nome, 'erro': "Valor negativo"})


        return erros

    def validar_texto(self, valor, pattern=None):
        erros = []
        if pattern:
            print('regex')  # Implementar a validação com regex se necessário

        if not isinstance(valor, str):
            # erros.append(f'Campo: {self.nome}, tipo errado {self.tipo} -> {type(valor)}')
            erros.append({'campo': self.nome, 'erro': f"Valo com tipo {type(valor)}, mas deveria ser {self.tipo}"})

            return erros
        
        if self.obrigatorio and valor.strip() == "":
            # erros.append(f'Campo: {self.nome}, está vazio')
            erros.append({'campo': self.nome, 'erro': "Campo é obrigatório, mas tem valor vazio"})

        if self.opcoes and valor not in self.opcoes:
            # erros.append(f'Campo: {self.nome}, valor inválido. Opções válidas: {self.opcoes}')
            erros.append({'campo': self.nome, 'erro': f"Valor inválido. Opções válidas: {self.opcoes}"})


        return erros


class Item:
    """
    Representa um item de produção, contendo dados básicos e métodos
    para validação e conversão para dicionário.
    """
    def __init__(self, data):
        self.contrato = data.get('contrato')
        self.codigo = data.get('codigo')
        self.executado = data.get('executado')
        self.concluido = data.get('concluido')
        self.errors, self.is_ok = self.validate()
    
    def to_dict(self):
        return {
            'contrato': self.contrato,
            'codigo': self.codigo,
            'executado': self.executado,
            'concluido': self.concluido,
            'errors': self.errors,
            'is_ok': self.is_ok,
            'merged': self.contrato + " | " + self.codigo
        }
    
    def validate(self):
        errors = []
        errors.extend(Campo('executado', float, True).validar(self.executado))
        return errors, len(errors) == 0


class Trecho:
    """
    Representa um trecho linear da produção, extraindo e validando dados
    como jusante, montante, extensão, diâmetro, material, método de execução
    e endereço.
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
            'endereco': self.endereco,
            'errors': self.errors,
            'is_ok': self.is_ok,
            'merged': str(self.contrato) + " | " +  str(self.codigo) + " | " +  str(self.jusante) + " | " +  
                      str(self.montante) + " | " +  str(self.material) + " | " +  str(self.metodo_exec) + " | " +  str(self.detalhe_metodo)
        }
    
    def validate(self):
        errors = []
        errors.extend(Campo('jusante', str, True).validar(self.jusante))
        errors.extend(Campo('montante', str, True).validar(self.montante))
        errors.extend(Campo('extensao', float, True).validar(self.extensao))
        errors.extend(Campo('diametro', int, True).validar(self.diametro))
        errors.extend(Campo('material', str, True, ['PVC', 'PEAD', 'CA', 'MBV', 'FoFo', 'ACO']).validar(self.material))
        errors.extend(Campo('metodo_exec', str, True, ['VCA', 'MND', 'AE']).validar(self.metodo_exec))
        errors.extend(Campo('endereco', str, True).validar(self.endereco))
        return errors, len(errors) == 0


class Localizada:
    """
    Representa uma localizada na produção, validando os campos descrição
    e número de inventário.
    """
    def __init__(self, data, contrato=None, codigo=None):
        self.contrato = contrato
        self.codigo = codigo
        self.descricao = data.get('descricao')
        self.num_inventario = data.get('num_inventario')
        self.errors, self.is_ok = self.validate()

    def to_dict(self):
        return {
            'contrato': self.contrato,
            'codigo': self.codigo,
            'descricao': self.descricao,
            'num_inventario': self.num_inventario,
            'errors': self.errors,
            'is_ok': self.is_ok
        }
    
    def validate(self):
        errors = []
        errors.extend(Campo('descricao', str, True).validar(self.descricao))
        errors.extend(Campo('num_inventario', str, False).validar(self.num_inventario))
        return errors, len(errors) == 0


class Ramal:
    """
    Representa um ramal na produção, validando campos de posição, completo
    e endereço.
    """
    def __init__(self, data, contrato=None, codigo=None):
        self.contrato = contrato
        self.codigo = codigo
        self.posicao = data.get('posicao')
        self.completo = data.get('completo')
        self.endereco = data.get('endereco')
        self.errors, self.is_ok = self.validate()

    def to_dict(self):
        return {
            'contrato': self.contrato,
            'codigo': self.codigo,
            'posicao': self.posicao,
            'completo': self.completo,
            'endereco': self.endereco,
            'errors': self.errors,
            'is_ok': self.is_ok
        }
    
    def validate(self):
        errors = []
        errors.extend(Campo('posicao', str, False).validar(self.posicao))
        errors.extend(Campo('endereco', str, False).validar(self.endereco))
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


def identificar_classe(data, contrato=None, codigo=None):
    """
    Identifica a classe apropriada (Trecho, Localizada ou Ramal) a partir de um
    dicionário de dados, conforme as chaves encontradas.
    """
    if 'jusante' in data and 'montante' in data:
        return Trecho(data, contrato=contrato, codigo=codigo)
    elif 'descricao' in data and 'num_inventario' in data:
        return Localizada(data, contrato=contrato, codigo=codigo)
    elif 'posicao' in data and 'completo' in data:
        return Ramal(data, contrato=contrato, codigo=codigo)
    else:
        raise ValueError("Dados não correspondem a nenhuma classe conhecida.")


def merged_count(df, valor):
    """
    Conta as ocorrências de um valor específico na coluna 'merged' de um DataFrame.
    """
    return len(df[df['merged'] == valor])


def process_production(file_path):
    """
    Processa os dados de produção a partir do arquivo JSON especificado, extrai
    os códigos e detalhes referentes aos itens, trechos, ramais e localizadas.
    Retorna os DataFrames correspondentes.
    """
    data = load_json(file_path)
    if data is None:
        raise ValueError("Os dados não puderam ser carregados. Verifique o arquivo JSON.")

    codes = []
    details_trechos = []
    details_ramais = []
    details_localizadas = []
    details_unknown = []  # Opcional: para itens que não se encaixam em nenhuma classe conhecida

    logging.info("Iniciando o processamento dos dados de produção.")
    
    for entry in data:
        mes_ref = entry.get('mes_ref')
        for prod in entry.get('producao', []):
            contrato = prod.get('contrato')
            for item in prod.get('itens', []):
                n_detalhes = len(item.get('producao', []))
                item_temp = Item({
                    'mes_ref': mes_ref,
                    'contrato': contrato,
                    'codigo': item.get('codigo'),
                    'executado': item.get('executado'),
                    'concluido': item.get('concluido'),
                    'n_detalhes': n_detalhes
                })
                code_temp = item_temp.to_dict()
                code_temp['merged'] = code_temp['contrato'] + " | " + code_temp['codigo']
                codes.append(code_temp)

                for det in item.get('producao', []):
                    detail_entry = {'contrato': contrato, 'codigo': item.get('codigo')}
                    try:
                        # Identifica a classe adequada e instancia o objeto correspondente
                        obj = identificar_classe(det, contrato=contrato, codigo=item.get('codigo'))
                        if isinstance(obj, Trecho):
                            detail_entry.update({'tipo': 'linear', **obj.to_dict()})
                            details_trechos.append(detail_entry)
                        elif isinstance(obj, Ramal):
                            detail_entry.update({'tipo': 'ramal', **obj.to_dict()})
                            details_ramais.append(detail_entry)
                        elif isinstance(obj, Localizada):
                            detail_entry.update({'tipo': 'localizada', **obj.to_dict()})
                            details_localizadas.append(detail_entry)
                    except ValueError:
                        detail_entry.update({'tipo': 'desconhecido', 'raw': det})
                        details_unknown.append(detail_entry)

    df_codes = pd.DataFrame(codes)
    df_trechos = pd.DataFrame(details_trechos)
    df_ramais = pd.DataFrame(details_ramais)
    df_localizadas = pd.DataFrame(details_localizadas)

    df_codes['duplicado'] = df_codes.apply(lambda x: merged_count(df_codes, x['merged']) > 1, axis=1)

    # Muito complicado saber se tem trecho duplicado. Vou não fazer isso por enquanto. srry :-(
    # df_trechos['ocorrencias'] = df_trechos.apply(lambda x: merged_count(df_trechos, x['merged']),axis=1)
    
    logging.info(f"Processamento concluído: {len(df_codes)} códigos, {len(df_trechos)} trechos, "
                 f"{len(df_ramais)} ramais e {len(df_localizadas)} localizadas extraídos.")

    # Retorna os DataFrames separados (pode incluir df_unknown se necessário).
    return df_codes, df_trechos, df_ramais, df_localizadas


