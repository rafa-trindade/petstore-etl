import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
HEADERS = {"Authorization": f"Token {API_TOKEN}"}

def normaliza_endereco(df):
    df["cep"] = df["cep"].astype(str).str.strip()

    total = len(df)
    contador = {"i": 0}

    def atualiza_linha(row):
        contador["i"] += 1
        i = contador["i"]
        cep_limpo = row["cep"].replace("-", "").strip()
        print(f"Processando ({i}/{total}): {row['empresa'].capitalize()} - {row['nome']}")

        if not cep_limpo or cep_limpo.lower() in ["nan", "none", ""]:
            row["cep"] = "indisponivel"
            return row

        if not cep_limpo.isdigit() or len(cep_limpo) != 8:
            row["cep"] = "invalido"
            return row

        url = f"https://www.cepaberto.com/api/v3/cep?cep={cep_limpo}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            data = response.json()

            if not data or (not data.get("logradouro") and not data.get("bairro") and not data.get("cidade")):
                print(f" - CEP {cep_limpo} não reconhecido pela API.")
                row["cep"] = "invalido"
                return row

            row["logradouro"] = data.get("logradouro", row.get("logradouro"))
            row["bairro"] = data.get("bairro", row.get("bairro"))
            row["cidade"] = data.get("cidade", {}).get("nome", row.get("cidade"))
            row["estado"] = data.get("estado", {}).get("sigla", row.get("estado"))
            row["latitude"] = data.get("latitude", row.get("latitude"))
            row["longitude"] = data.get("longitude", row.get("longitude"))
            row["cep"] = f"{cep_limpo[:5]}-{cep_limpo[5:]}"
        else:
            print(f" - Erro ao consultar API: {response.status_code}")

            row["cep"] = "invalido"

        return row

    df = df.apply(atualiza_linha, axis=1)
    return df