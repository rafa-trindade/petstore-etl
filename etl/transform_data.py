import pandas as pd
import numpy as np
from etl.utils import normaliza_endereco


GOLD_CSV = "data/gold/lojas_gold.csv"

def transform_data_silevr_gold(csv_path):

    df_gold = pd.read_csv(csv_path, sep=";", encoding="utf-8")
    
    df_gold = df_gold.rename(columns={"endereco": "logradouro"})
    df_gold["latitude"] = pd.to_numeric(df_gold.get("latitude", np.nan), errors="coerce")
    df_gold["longitude"] = pd.to_numeric(df_gold.get("longitude", np.nan), errors="coerce")

    df_gold = df_gold[[
        "empresa", "nome", "logradouro", "bairro", "cidade",
        "estado", "cep", "latitude", "longitude", "data_extracao"
    ]]

    #df_gold = df_gold.head(45) # sample

    df_gold = normaliza_endereco(df_gold)

    df_gold.to_csv(GOLD_CSV, index=False, sep=";", encoding="utf-8-sig")
    
    return df_gold

if __name__ == "__main__":
    transform_data_silevr_gold()
