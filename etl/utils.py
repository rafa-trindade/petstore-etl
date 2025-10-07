import os
import requests
import pandas as pd
from dotenv import load_dotenv
import time
import re
from serpapi import GoogleSearch
from tqdm import tqdm

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
HEADERS = {"Authorization": f"Token {API_TOKEN}"}
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
CEP_REGEX = re.compile(r"\d{5}-\d{3}")


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




def preencher_ceps_petland(df, empresa="petland", sleep_sec=1, country="br", language="pt-BR"):

    df_emp = df[df["empresa"].str.lower() == empresa.lower()].copy()
    cache = {} 

    for idx, row in tqdm(df_emp.iterrows(), total=df_emp.shape[0], desc="Petland CEPs"):
        nome = str(row.get("nome", "")).strip()
        current_cep = str(row.get("cep", "")).strip()
        if CEP_REGEX.match(current_cep):
            continue

        if nome in cache:
            found = cache[nome]
            if found:
                df_emp.at[idx, "cep"] = found
            continue

        params = {
            "engine": "google_maps",
            "type": "search",
            "q": nome,
            "hl": language,
            "gl": country,
            "api_key": SERPAPI_API_KEY
        }
        search = GoogleSearch(params)
        try:
            res = search.get_dict()
        except Exception as e:
            print(f"Erro SerpApi para '{nome}': {e}")
            cache[nome] = None
            time.sleep(sleep_sec)
            continue

        cep = None

        local_results = res.get("local_results") or res.get("local_results", [])
        if isinstance(local_results, list):
            for item in local_results:
                addr = item.get("address") or item.get("address_string") or item.get("formatted_address") or ""
                if not addr:
                    addr = " ".join([str(item.get(k, "")) for k in ("address", "address_string", "formatted_address")])
                m = CEP_REGEX.search(addr)
                if m:
                    cep = m.group(0)
                    break

        if not cep:
            place_results = res.get("place_results") or {}
            if isinstance(place_results, dict):
                addr = place_results.get("address") or place_results.get("address_string") or place_results.get("formatted_address") or ""
                m = CEP_REGEX.search(addr)
                if m:
                    cep = m.group(0)

        if not cep and isinstance(local_results, list):
            for item in local_results:
                pid = item.get("place_id") or item.get("data_id") or item.get("data_cid")
                if not pid:
                    continue
                params2 = {"engine": "google_maps", "place_id": pid, "api_key": api_key}
                search2 = GoogleSearch(params2)
                try:
                    res2 = search2.get_dict()
                except Exception:
                    continue
                place2 = res2.get("place_results") or {}
                addr = place2.get("address") or place2.get("address_string") or place2.get("formatted_address") or ""
                m = CEP_REGEX.search(addr)
                if m:
                    cep = m.group(0)
                    break
                time.sleep(sleep_sec)

        if cep:
            df_emp.at[idx, "cep"] = cep
            cache[nome] = cep
            print(f"{nome} -> {cep}")
        else:
            cache[nome] = None
            print(f"{nome} -> CEP não encontrado")

        time.sleep(sleep_sec)

    df.update(df_emp)

    return df




def preencher_coordenadas(df: pd.DataFrame, empresa: str = None):
    """
    Preenche latitude e longitude de lojas usando SerpApi (Google Maps).
    Pesquisa pelo campo 'nome' apenas nas linhas onde latitude ou longitude estão vazias.
    """

    if SERPAPI_API_KEY is None:
        raise ValueError("Chave SERPAPI_KEY não encontrada no arquivo .env")

    df_target = df.copy()

    # Filtro: somente linhas com lat/lon vazias
    mask = df_target["latitude"].isna() | df_target["longitude"].isna()
    if empresa:
        mask &= df_target["empresa"].str.lower() == empresa.lower()

    df_faltando = df_target[mask]

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
                df_target.at[idx, "latitude"] = latitude
                df_target.at[idx, "longitude"] = longitude
                print(f"✅ {nome_loja} → ({latitude}, {longitude})")
            else:
                print(f"⚠️ {nome_loja} → Coordenadas não encontradas")

        except Exception as e:
            print(f"❌ Erro ao buscar '{nome_loja}': {e}")

        time.sleep(1)  # evitar limite da API

    return df_target