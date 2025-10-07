import os
import re
import pandas as pd
import numpy as np
import time
from serpapi import GoogleSearch
from etl.utils import normaliza_endereco, preencher_ceps_petland


GOLD_CSV = "data/gold/lojas_gold.csv"
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

def transform_data_silver(csv_path):

    df_silver = pd.read_csv(csv_path, sep=";", encoding="utf-8")

    #df_silver = df_silver.tail(2)
    
    df_silver = df_silver.rename(columns={"endereco": "logradouro"})

    if "latitude" not in df_silver.columns:
        df_silver["latitude"] = np.nan
    df_silver["latitude"] = pd.to_numeric(df_silver["latitude"], errors="coerce")

    if "longitude" not in df_silver.columns:
        df_silver["longitude"] = np.nan
    df_silver["longitude"] = pd.to_numeric(df_silver["longitude"], errors="coerce")

    df_silver = df_silver[[
        "empresa", "nome", "logradouro", "bairro", "cidade",
        "estado", "cep", "latitude", "longitude", "data_extracao"
    ]]

    df_silver = preencher_ceps_petland(df_silver)

    df_silver = normaliza_endereco(df_silver)

    df_silver.to_csv(GOLD_CSV, index=False, sep=";", encoding="utf-8-sig")
    
    return df_silver


def transform_data_gold(csv_path, nome_empresa=None):

    df_gold = pd.read_csv(csv_path, sep=";", encoding="utf-8")

    if SERPAPI_API_KEY is None:
        raise ValueError("Chave SERPAPI_KEY não encontrada no arquivo .env")

    mask = df_gold["latitude"].isna() | df_gold["longitude"].isna()
    if nome_empresa:
        mask &= df_gold["nome"].str.lower() == nome_empresa.lower()

    df_faltando = df_gold[mask]

    print(f"🔍 Buscando coordenadas para {len(df_faltando)} lojas...")

    for idx, row in df_faltando.iterrows():
        nome_loja = row.get("nome")
        if not nome_loja:
            continue

        try:
            params = {
                "engine": "google_maps",
                "q": nome_loja,
                "api_key": SERPAPI_API_KEY,
            }
            search = GoogleSearch(params)
            results = search.get_dict()

            gps = results.get("place_results", {}).get("gps_coordinates", {})
            latitude = gps.get("latitude")
            longitude = gps.get("longitude")

            if latitude and longitude:
                df_gold.at[idx, "latitude"] = latitude
                df_gold.at[idx, "longitude"] = longitude
                print(f"✅ {nome_loja} → ({latitude}, {longitude})")
            else:
                print(f"⚠️ {nome_loja} → Coordenadas não encontradas")

        except Exception as e:
            print(f"❌ Erro ao buscar '{nome_loja}': {e}")

        time.sleep(1)

    return df_gold
