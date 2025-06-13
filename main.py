#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Imports padrão e de terceiros
from bd import conectar_bd, executar_select
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os

# Imports dos módulos de processamento
from json_para_df.planejado import process_planejado
from json_para_df.previsto import process_previsto
from json_para_df.producao import process_production

# Carrega as variáveis do arquivo .env
load_dotenv(dotenv_path=".env")

# Constantes com os caminhos dos arquivos JSON
PREVISTO_FILE = os.getenv("PREVISTO_FILE_PATH")
PRODUCAO_FILE = os.getenv("PRODUCAO_FILE_PATH")
PLANEJADO_FILE = os.getenv("PLANEJADO_FILE_PATH")


# Definição da classe para criação e formatação do arquivo Excel
class ExcelCreator:
    def __init__(self, file_name="output.xlsx"):
        """
        Inicializa a classe definindo o nome do arquivo e o objeto ExcelWriter
        utilizando o engine 'xlsxwriter'.
        """
        self.file_name = file_name
        self.writer = pd.ExcelWriter(self.file_name, engine='xlsxwriter')

    def add_dataframe(self, df, sheet_name="Sheet1"):
        """
        Adiciona um DataFrame à planilha Excel com formatação de tabela e ajuste
        automático da largura das colunas.
        
        Parâmetros:
            df : pandas.DataFrame
                DataFrame a ser adicionado.
            sheet_name : str
                Nome da planilha onde o DataFrame será escrito.
        """
        if df.empty:
            print(f"DataFrame vazio. Não adicionando a planilha '{sheet_name}'.")
            return
        
        # Escreve o DataFrame na planilha sem cabeçalho, iniciando na linha 1 (para cabeçalho customizado)
        df.to_excel(self.writer, sheet_name=sheet_name, index=False, startrow=1, header=False)
        
        # Acessa o workbook e a worksheet criados pelo ExcelWriter
        workbook = self.writer.book
        worksheet = self.writer.sheets[sheet_name]
        
        # Define o formato do cabeçalho da tabela
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'bottom',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Escreve os cabeçalhos na primeira linha com o formato definido
        for col_num, header in enumerate(df.columns):
            worksheet.write(0, col_num, header, header_format)
        
        # Define o intervalo da tabela (linha inicial, coluna inicial, linha final, coluna final)
        max_row, max_col = df.shape
        table_range = [0, 0, max_row, max_col - 1]
        
        # Cria a tabela formatada com os cabeçalhos
        worksheet.add_table(table_range[0], table_range[1], table_range[2], table_range[3],
                              {'columns': [{'header': col} for col in df.columns]})
        
        # Ajusta a largura de cada coluna para acomodar os dados
        for i, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_length)

    def save(self):
        """
        Salva o arquivo Excel criado com todas as planilhas adicionadas.
        """
        self.writer.close()


def get_errors(df):
    """
    Filtra e retorna os registros que possuem erro.

    Parâmetros:
        df : pandas.DataFrame
            DataFrame a ser filtrado.
    
    Retorna:
        pandas.DataFrame
            DataFrame com os registros que não estão OK (coluna 'is_ok' == False)
            ou que são duplicados.
    """
    if df.empty:
        return df.copy()
    return df[~df["is_ok"]].copy()


def process_producao(excel_creator):
    """
    Processa os dados de produção e adiciona as planilhas de erros ao Excel.
    """
    # Processa os dados de produção
    df_codes, df_trechos, df_ramais, df_localizadas = process_production(PRODUCAO_FILE)
    
    # Filtra os códigos com erro ou duplicados
    df_codes_erros = df_codes[(~df_codes["is_ok"]) | (df_codes["duplicado"] == True)]
    excel_creator.add_dataframe(df_codes_erros, sheet_name="Produção CodWBS")


    
    # Adiciona as demais planilhas de erros
    excel_creator.add_dataframe(get_errors(df_trechos), sheet_name="Produção Trechos")
    excel_creator.add_dataframe(get_errors(df_ramais), sheet_name="Produção Ramais")
    excel_creator.add_dataframe(get_errors(df_localizadas), sheet_name="Produção Localizadas")
    return df_codes, df_trechos, df_ramais, df_localizadas


def process_previsto_data(excel_creator):
    """
    Processa os dados previstos e adiciona as planilhas de erros ao Excel.
    """
    df_linear, df_linear_trechos, df_localizada, df_ramais, df_economias = process_previsto(PREVISTO_FILE)
    
    excel_creator.add_dataframe(get_errors(df_linear), sheet_name="Previsto Linear")
    excel_creator.add_dataframe(get_errors(df_linear_trechos), sheet_name="Previsto Linear Trechos")
    excel_creator.add_dataframe(get_errors(df_localizada), sheet_name="Previsto Localizadas")
    excel_creator.add_dataframe(get_errors(df_ramais), sheet_name="Previsto Ramais")
    excel_creator.add_dataframe(get_errors(df_economias), sheet_name="Previsto Economias")
    return df_linear, df_linear_trechos, df_localizada, df_ramais, df_economias


def process_planejado_data(excel_creator):
    """
    Processa os dados planejados e adiciona a planilha de erros ao Excel.
    """

    df_planejado = process_planejado(PLANEJADO_FILE)
    excel_creator.add_dataframe(get_errors(df_planejado), sheet_name="Planejado")
    return df_planejado


def main():
    """
    Função principal que orquestra o processamento dos dados e a geração do arquivo Excel.
    """
    # Obtém a data atual para incluir no nome do arquivo
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = f"Erros_json_{current_datetime}.xlsx"
    
    # Inicializa o ExcelCreator
    excel_creator = ExcelCreator(output_file)
    
    # Processa os dados de Produção, Previsto e Planejado
    process_producao(excel_creator)
    df_linear, df_linear_trechos, df_localizada, df_ramais, df_economias = process_previsto_data(excel_creator)
    df_planejado = process_planejado_data(excel_creator)

    # pegar todos os conjuntos de contrato, codigo dos previstos e planejados
    df_codigos_previstos = pd.concat([df_linear, df_linear_trechos, df_localizada, df_ramais, df_economias], ignore_index=True)
    df_codigos_previstos = df_codigos_previstos[["contrato", "codigo"]].drop_duplicates()
    df_codigos_planejados = df_planejado[["contrato", "codigo"]].drop_duplicates()

    # preciso descobrir códigos que estão no planejado e não no preisto
    df_codigos_faltantes = pd.merge(df_codigos_planejados, df_codigos_previstos, how="left", on=["contrato", 'codigo'], indicator=True)
    df_codigos_faltantes = df_codigos_faltantes[df_codigos_faltantes["_merge"] == "left_only"]

    # Adiciona a planilha de códigos faltantes
    if df_codigos_faltantes.empty:
        print("Não foram encontrados códigos faltantes.")
    else:
        excel_creator.add_dataframe(df_codigos_faltantes, sheet_name="Planejado não está no Previsto")

    # Salva o arquivo Excel final
    excel_creator.save()
    print(f"Arquivo '{output_file}' gerado com sucesso.")


if __name__ == '__main__':
    main()
