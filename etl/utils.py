import pandas as pd
import requests
import re
import time
import traceback
from brazilcep import get_address_from_cep

USER_AGENT = "petstore-etl/1.0"

def padronizar_logradouro(logradouro_full):
    if not logradouro_full:
        return None
    logradouro = re.sub(r'\s*(?:,|\d+).*$', '', logradouro_full)
    return logradouro.strip()

def preencher_dados(endereco, cidade, estado):
    if pd.isna(endereco) or pd.isna(cidade):
        return None, endereco, None, None, estado

    params = {
        "street": endereco,
        "city": cidade,
        "state": estado if pd.notna(estado) else "",
        "country": "Brasil",
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }

    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None, endereco, None, None, estado

        address = data[0].get("address", {})
        logradouro_full = address.get("road") or endereco
        logradouro = padronizar_logradouro(logradouro_full)
        latitude = float(data[0].get("lat")) if data[0].get("lat") else None
        longitude = float(data[0].get("lon")) if data[0].get("lon") else None

        estado_api = address.get("state")
        siglas = {
            "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM",
            "Bahia": "BA", "Ceará": "CE", "Distrito Federal": "DF", "Espírito Santo": "ES",
            "Goiás": "GO", "Maranhão": "MA", "Mato Grosso": "MT", "Mato Grosso do Sul": "MS",
            "Minas Gerais": "MG", "Pará": "PA", "Paraíba": "PB", "Paraná": "PR",
            "Pernambuco": "PE", "Piauí": "PI", "Rio de Janeiro": "RJ", "Rio Grande do Norte": "RN",
            "Rio Grande do Sul": "RS", "Rondônia": "RO", "Roraima": "RR", "Santa Catarina": "SC",
            "São Paulo": "SP", "Sergipe": "SE", "Tocantins": "TO"
        }
        estado_sigla = siglas.get(estado_api, estado) if estado_api else estado

        return address.get("postcode"), logradouro, latitude, longitude, estado_sigla

    except Exception as e:
        print(f"Erro ao consultar {endereco}, {cidade}: {e}")
        return None, endereco, None, None, estado


def preencher_endereco_campos(df, coluna_cep='cep'):
    print(">> type(df):", type(df))
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df não é um pandas.DataFrame. Verifique a variável.")
    print(">> shape:", df.shape)
    print(">> colunas:", df.columns.tolist())

    if coluna_cep not in df.columns:
        raise KeyError(f"Coluna '{coluna_cep}' não encontrada no DataFrame.")

    for col in ['logradouro', 'bairro', 'cidade', 'estado']:
        if col not in df.columns:
            df[col] = None
    print(">> colunas de endereço garantidas no DataFrame.")

    ceps = df.loc[df[coluna_cep].notna(), coluna_cep].astype(str).str.strip().unique()
    print(f">> {len(ceps)} CEP(s) únicos encontrados para consulta (ex.: {ceps[:5]})")

    cache = {}
    for i, cep in enumerate(ceps, start=1):
        if cep in cache:
            continue
        try:
            e = get_address_from_cep(cep)
            cache[cep] = {
                'logradouro': e.get('street'),
                'bairro': e.get('complement') or e.get('district'),
                'cidade': e.get('city'),
                'estado': e.get('uf')
            }
            print(f"[{i}/{len(ceps)}] {cep} -> {cache[cep]}")
        except Exception as exc:
            cache[cep] = {'logradouro': None, 'bairro': None, 'cidade': None, 'estado': None}
            print(f"[{i}/{len(ceps)}] ERRO ao buscar {cep}: {exc}")
        time.sleep(0.1)

    def map_cache(cep, campo):
        if pd.isna(cep):
            return None
        cep = str(cep).strip()
        return cache.get(cep, {}).get(campo)

    for campo in ['logradouro', 'bairro', 'cidade', 'estado']:
        df[campo] = df[coluna_cep].apply(lambda x: map_cache(x, campo))
        print(f">> Campo '{campo}' preenchido com base no CEP.")

    print(">> Preenchimento concluído com sucesso!")
    print(df[['cep', 'logradouro', 'bairro', 'cidade', 'estado']].head(10))
    return df

    def map_cache(cep, campo):
        if pd.isna(cep):
            return None
        cep = str(cep).strip()
        return cache.get(cep, {}).get(campo)

    for campo in ['endereco', 'bairro', 'cidade', 'estado']:
        df[campo] = df[coluna_cep].apply(lambda x: map_cache(x, campo))
        print(f">> Campo '{campo}' preenchido com base no CEP.")

    print(">> Preenchimento concluído com sucesso!")
    print(df[['cep', 'endereco', 'bairro', 'cidade', 'estado']].head(10))
    return df