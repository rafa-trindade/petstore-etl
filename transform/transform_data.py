import pandas as pd
import numpy as np
import time
from utils import preencher_dados, preencher_endereco_campos

csv_raw = "https://raw.githubusercontent.com/rafa-trindade/petstore-scraping/main/data/bronze/lojas_bronze.csv"
df_silver = pd.read_csv(csv_raw, sep=";", encoding="utf-8")
df_silver["latitude"] = np.nan
df_silver["longitude"] = np.nan
df_silver["latitude"] = pd.to_numeric(df_silver["latitude"], errors="coerce")
df_silver["longitude"] = pd.to_numeric(df_silver["longitude"], errors="coerce")
df_silver = df_silver.rename(columns={"endereco": "logradouro"})
df_silver = df_silver[["empresa", "nome", "logradouro", "bairro", "cidade", "estado", "cep", "latitude", "longitude"]]

#df_silver = df_silver.head(20) #sample 

for col in ["bairro", "cep", "logradouro", "latitude", "longitude"]:
    if col not in df_silver.columns:
        df_silver[col] = ""

for i, row in df_silver.iterrows():

    if pd.notna(row.get("cep")) and row["cep"] != "":
        cep_existente = row["cep"]
        logradouro = row["logradouro"]
        lat_existente = row.get("latitude")
        lon_existente = row.get("longitude")
        estado_existente = row["estado"]

        if pd.isna(lat_existente) or pd.isna(lon_existente):
            cep, logradouro, lat, lon, estado_sigla = preencher_dados(
                row["logradouro"], row["cidade"], row["estado"]
            )
            if lat:
                df_silver.at[i, "latitude"] = lat
            if lon:
                df_silver.at[i, "longitude"] = lon
        else:
            cep, logradouro, lat, lon, estado_sigla = cep_existente, logradouro, lat_existente, lon_existente, estado_existente

    else:
        cep, logradouro, lat, lon, estado_sigla = preencher_dados(
            row["logradouro"], row["cidade"], row["estado"]
        )
        if cep:
            df_silver.at[i, "cep"] = cep
        if logradouro:
            df_silver.at[i, "logradouro"] = logradouro
        if lat:
            df_silver.at[i, "latitude"] = lat
        if lon:
            df_silver.at[i, "longitude"] = lon
        if estado_sigla:
            df_silver.at[i, "estado"] = estado_sigla

    print(f"Processado {i+1}/{len(df_silver)}: {row['empresa']} - {row['nome']}")
    time.sleep(1)


SILVER_CSV = "data/silver/lojas_silver.csv"
df_silver.to_csv(SILVER_CSV, index=False, sep=";", encoding="utf-8-sig")
print(f"\nProcesso concluído. Arquivo salvo como: {SILVER_CSV}")

df_gold = pd.read_csv(SILVER_CSV, sep=";", encoding="utf-8")
df_gold = preencher_endereco_campos(df_gold)

GOLD_CSV = "data/gold/lojas_gold.csv"
df_gold.to_csv(GOLD_CSV, index=False, sep=";", encoding="utf-8-sig")
print(f"\nProcesso concluído. Arquivo salvo como: {GOLD_CSV}")
