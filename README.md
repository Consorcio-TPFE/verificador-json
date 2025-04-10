# Processamento e Validação de Dados JSON

Este projeto tem como objetivo processar e validar dados provenientes de arquivos JSON referentes à produção e à previsão de contratos. O script realiza diversas etapas, desde a detecção do encoding dos arquivos até a geração de um relatório de erros em um arquivo Excel.


## Funcionalidades


item(8) + D2(fator fisico d(2)) + D3(tipo obra d(2)) + Municipio 


- **Detecção de Encoding:** Utiliza o módulo `chardet` para identificar o encoding do arquivo JSON.
- **Carregamento de JSON:** Faz o carregamento e decodificação dos arquivos JSON, tratando exceções como arquivo não encontrado ou erros na decodificação.
- **Processamento de Dados de Produção:**
  - Extração de códigos e detalhes dos dados de produção.
  - Organização dos dados em DataFrames utilizando a biblioteca `pandas`.
- **Processamento de Dados Previstos:**
  - Manipulação dos dados de lineares, localizadas, ramais e economias.
  - Expansão de estruturas aninhadas (como listas de trechos) para facilitar a análise.
- **Validação dos Dados:**
  - Funções específicas para validar os registros de produção e previstos, identificando campos ausentes, valores inconsistentes ou duplicados.
  - Registro dos erros encontrados por meio de logs.
- **Geração de Relatório em Excel:** Criação de um arquivo `checagens_formatado.xlsx` com múltiplas sheets, onde cada sheet corresponde a um conjunto de dados com erros ou inconsistências.

## Configuração do Ambiente

1. **Instalação das Dependências:**

   Execute o comando abaixo para instalar as bibliotecas necessárias:

   ```bash
   pip install -r requirements.txt
   ```
   
   > **Nota:** Sempre que uma nova dependência for adicionada ao projeto, atualize o arquivo `requirements.txt` com o seguinte comando: *pip freeze > requirements.txt*

2. **Configuração das Variáveis de Ambiente:**

   Crie um arquivo `.env` na raiz do projeto e defina as seguintes variáveis com os caminhos dos arquivos JSON:

   ```env
   PREVISTO_FILE_PATH=path/para/arquivo_previsto.json
   PRODUCAO_FILE_PATH=path/para/arquivo_producao.json
   PLANEJADO_FILE_PATH=path/para/arquivo_planejado.json
   ```

## Como Executar

Após configurar o ambiente, execute o script principal:

```bash
python main.py
```

Ao final da execução, será gerado o arquivo `checagens_formatado.xlsx` contendo os dados processados e, se houver, os erros encontrados.

## Logs

O projeto utiliza o módulo `logging` para:

- Informar o progresso das operações.
- Reportar erros e avisos durante o processamento dos dados.

Os logs são exibidos no console durante a execução, facilitando o monitoramento e a depuração.

## Estrutura do Código

- **Funções Auxiliares:**
  - `detect_encoding(file_path)`: Detecta o encoding do arquivo.
  - `load_json(file_path, encoding=None)`: Carrega o conteúdo do arquivo JSON.
- **Processamento dos Dados de Produção:**
  - `process_production(file_path)`: Processa os dados de produção, extraindo códigos e detalhes.
- **Processamento dos Dados Previstos:**
  - `process_previsto(file_path)`: Processa os dados de previsão para lineares, localizadas, ramais e economias.
- **Validações:**
  - Funções específicas para validar cada tipo de registro e apontar inconsistências (ex.: `validate_production_detail`, `validate_linear_row`, etc.).
- **Geração do Excel:**
  - Consolida os DataFrames com erros em um arquivo Excel com múltiplas sheets para facilitar a análise dos dados.
