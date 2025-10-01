import os
import json

# ================ CONFIGURAÇÃO ================
PASTA_ENTRADA = "JSON 202509"
CAMINHO_MAIO = os.path.join(PASTA_ENTRADA, "producao-exportacao-wbs-2025-08-11T17-30-52.json")
CAMINHO_JUNHO = os.path.join(PASTA_ENTRADA, "producao-exportacao-wbs-2025-09-12T15-22-57.json")
CAMINHO_SAIDA = os.path.join(PASTA_ENTRADA, "producao-2025-09-filtrado.json")
# ==============================================

def carregar_enderecos(caminho_json):
    print(f"Lendo endereços de referência em: {caminho_json}")
    with open(caminho_json, encoding='utf-8') as f:
        dados = json.load(f)
    enderecos = set()
    for mes in dados:
        for prod in mes.get("producao", []):
            for item in prod.get("itens", []):
                for prod_item in item.get("producao", []):
                    endereco = prod_item.get("endereco")
                    if endereco:
                        enderecos.add(endereco)
    print(f"Total de endereços únicos em maio: {len(enderecos)}")
    return enderecos

def filtrar_json(caminho_junho, enderecos_maio):
    print(f"Lendo arquivo de junho: {caminho_junho}")
    with open(caminho_junho, encoding='utf-8') as f:
        dados = json.load(f)

    total_antes = sum(
        len(item.get("producao", [])) 
        for mes in dados 
        for bloco in mes.get("producao", [])
        for item in bloco.get("itens", [])
    )

    for mes in dados:
        for prod in mes.get("producao", []):
            for item in prod.get("itens", []):
                if "producao" in item and isinstance(item["producao"], list):
                    item["producao"] = [
                        pr for pr in item["producao"]
                        if pr.get("endereco") not in enderecos_maio
                    ]
            prod["itens"] = [
                it for it in prod["itens"]
                if not it.get("producao") or len(it["producao"]) > 0
            ]
        mes["producao"] = [
            pr for pr in mes.get("producao", [])
            if pr.get("itens")
        ]

    dados_filtrados = [
        m for m in dados
        if m.get("producao")
    ]

    total_depois = sum(
        len(item.get("producao", [])) 
        for mes in dados_filtrados 
        for bloco in mes.get("producao", [])
        for item in bloco.get("itens", [])
    )

    print(f"Total de produções ANTES do filtro: {total_antes}")
    print(f"Total de produções APÓS o filtro: {total_depois}")
    print(f"Total removido: {total_antes - total_depois}")

    return dados_filtrados

def salvar_json(dados, caminho_saida):
    print(f"Salvando resultado em: {caminho_saida}")
    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print("Arquivo final salvo com sucesso!")

def main():
    enderecos_maio = carregar_enderecos(CAMINHO_MAIO)
    dados_filtrados = filtrar_json(CAMINHO_JUNHO, enderecos_maio)
    salvar_json(dados_filtrados, CAMINHO_SAIDA)

if __name__ == "__main__":
    main()