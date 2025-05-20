import requests
import urllib.parse
import pandas as pd
from typing import Optional, List


def consultar_arcgis_camada(
    base_url: str,
    where: str = "1=1",
    fields: Optional[List[str]] = None,
    include_geometry: bool = False,
    batch_size: int = 1000,
    verbose: bool = True,
    timeout: int = 30
) -> pd.DataFrame:
    """
    Consulta uma camada ArcGIS paginada e retorna um DataFrame com todos os registros.

    Parâmetros:
    - base_url (str): URL base da camada (sem /query).
    - where (str): Cláusula WHERE da consulta.
    - fields (List[str]): Lista de campos a retornar. Se None, retorna todos ('*').
    - include_geometry (bool): Se True, retorna geometria.
    - batch_size (int): Número de registros por lote.
    - verbose (bool): Se True, imprime logs de progresso.
    - timeout (int): Tempo limite para cada requisição em segundos.

    Retorna:
    - pd.DataFrame com os registros consultados.
    """
    offset = 0
    all_features = []
    where_encoded = urllib.parse.quote(where)
    out_fields = "*" if fields is None else ",".join(fields)
    geometry = "true" if include_geometry else "false"

    while True:
        query_url = (
            f"{base_url}/query?"
            f"f=json&"
            f"where={where_encoded}&"
            f"outFields={urllib.parse.quote(out_fields)}&"
            f"returnGeometry={geometry}&"
            f"resultOffset={offset}&"
            f"resultRecordCount={batch_size}&"
            f"spatialRel=esriSpatialRelIntersects"
        )

        try:
            response = requests.get(query_url, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])
            if not features:
                break

            all_features.extend(features)
            offset += batch_size

            if verbose:
                print(f"✓ Lote com {len(features)} registros carregado (offset {offset})")

        except requests.RequestException as e:
            print(f"⚠️ Erro ao consultar camada: {e}")
            break

    if not all_features:
        print("⚠️ Nenhum dado retornado.")
        return pd.DataFrame()

    # Extrair atributos
    return pd.DataFrame([f["attributes"] for f in all_features])


# EXEMPLOS ESPECÍFICOS

def create_df_RMSP():
    url = "https://services9.arcgis.com/dXZLSzC33uzjAmXl/arcgis/rest/services/Contratos_RMSP_R46_R1_WEB/FeatureServer/1"
    return consultar_arcgis_camada(url, where="WBS_TEXT IS NOT NULL AND WBS_TEXT <> ''")


def create_df_RMBS():
    url = "https://services9.arcgis.com/dXZLSzC33uzjAmXl/arcgis/rest/services/Contratos_R5_R2_20240918_WEB/FeatureServer/0"
    return consultar_arcgis_camada(url, where="WBS_TEXT IS NOT NULL AND WBS_TEXT <> ''")

def endereco_generation(row):
    result = ""
    for part in [row['MUNICIPIO'], row["BAIRRO"], row['LOGRADOURO']]:
        if pd.isna(part):
            continue
        if part == "":
            continue
        if result != "":
            result += ", "
        result += str(part)
    return result

def create_enderecos_df():

    df = pd.concat([create_df_RMSP(), create_df_RMBS()], ignore_index=True)
    df['ENDERECO'] = df.apply(endereco_generation, axis=1)
    

    return df
