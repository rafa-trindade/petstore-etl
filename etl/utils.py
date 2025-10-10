import os
import requests
import pandas as pd
import unicodedata
from dotenv import load_dotenv
from tabulate import tabulate
import re
import time

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
HEADERS = {"Authorization": f"Token {API_TOKEN}"}


def preenche_campos(df, caminho_csv):

    mapa = pd.read_csv(caminho_csv, sep=";", encoding="utf-8-sig")

    cols_to_normalize = ["cidade"]
    
    for col in cols_to_normalize:
        if col in mapa.columns:
            mapa[col] = mapa[col].apply(limpar_texto)
       
    df.rename(columns={"endereco": "logradouro"}, inplace=True)

    df_merged = pd.merge(
        df,
        mapa[['cidade', 'estado', 'cod_cidade', 'regiao', 'populacao', 'renda_domiciliar_per_capita']],
        on=['cidade', 'estado'],
        how='left'
    )

    colunas_finais = [
        'empresa', 'nome', 'logradouro', 'bairro', 'cidade', 'estado',
        'regiao', 'cep', 'populacao', 'latitude', 'longitude',
        'renda_domiciliar_per_capita', 'cod_cidade', 'data_extracao'
    ]

    for col in colunas_finais:
        if col not in df_merged.columns:
            df_merged[col] = None

    nao_preenchidas = df_merged[df_merged['cod_cidade'].isna()]
    nao_preenchidas = nao_preenchidas.dropna(subset=['cidade', 'estado'], how='all')

    if not nao_preenchidas.empty:
        print("Linhas que não foi possível preencher (cidade e estado):")
        print(nao_preenchidas[['cidade', 'estado']])

    return df_merged[colunas_finais]

def limpar_texto(texto):
    if not texto:
        return ""
    t = str(texto)
    t = t.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    t = " ".join(t.split())
    return t.strip()

def normaliza_campos(df):
    total = len(df)
    preenchidos = 0
    falhas = 0

    for idx, row in df.iterrows():
        empresa_nome = f"{row.get('empresa', '')} - {row.get('nome', '')}"
        print(f"- Processando ({idx+1}/{total}): {empresa_nome}")

        cep = str(row.get("cep") or "").replace("-", "").strip()
        estado = row.get("estado") or ""
        cidade = row.get("cidade") or ""

        dados_coord = None
        metodo = None

        if not cep or len(cep) != 8:
            try:
                url_address = "https://www.cepaberto.com/api/v3/address"
                params = {"estado": estado, "cidade": cidade}
                resp = requests.get(url_address, headers=HEADERS, params=params, timeout=10)
                if resp.ok:
                    dados = resp.json()
                    cep = dados.get("cep")
                    if cep:
                        df.at[idx, "cep"] = cep
                        metodo = "UF+CIDADE"
            except Exception as e:
                print(f" - Erro ao buscar CEP via cidade/UF: {e}")
            time.sleep(1)  

        if cep and len(cep) == 8:
            try:
                url_cep = f"https://www.cepaberto.com/api/v3/cep?cep={cep}"
                resp = requests.get(url_cep, headers=HEADERS, timeout=10)
                if resp.ok:
                    dados_coord = resp.json()
                    metodo = metodo or "CEP"
            except Exception as e:
                print(f" - Erro ao buscar coordenadas via CEP: {e}")
            time.sleep(1)  

        if dados_coord:
            try:
                lat_api = dados_coord.get("latitude")
                lon_api = dados_coord.get("longitude")
                if lat_api is not None:
                    df.at[idx, "latitude"] = float(lat_api)
                if lon_api is not None:
                    df.at[idx, "longitude"] = float(lon_api)

                logradouro = dados_coord.get("logradouro")
                bairro = dados_coord.get("bairro")
                if logradouro:
                    df.at[idx, "logradouro"] = logradouro
                if bairro:
                    df.at[idx, "bairro"] = bairro

                preenchidos += 1
            except Exception as e:
                print(f" - Erro ao atualizar linha: {e}")
                falhas += 1
        else:
            falhas += 1


    return df

def eda(df):

    total_linhas = df.shape[0]
    total_cols = df.shape[1]
    print(f"\nDimensão: {total_linhas} linhas x {total_cols} colunas\n")

    # =================== LISTAGEM DE COLUNAS POR TIPO ===================
    tipos_colunas = {
        "Numéricas": df.select_dtypes(include=['int64', 'float64']).columns.tolist(),
        "Categóricas (object/category)": df.select_dtypes(include=['object', 'category']).columns.tolist(),
        "Booleanas": df.select_dtypes(include=['bool']).columns.tolist(),
        "Datas": df.select_dtypes(include=['datetime64[ns]']).columns.tolist(),
        "Períodos": [c for c in df.columns if pd.api.types.is_period_dtype(df[c])],
        "Timedeltas": df.select_dtypes(include=['timedelta64[ns]']).columns.tolist(),
        "Outros tipos": [c for c in df.columns if c not in 
                        df.select_dtypes(include=['int64','float64','object','category','bool','datetime64[ns]','timedelta64[ns]']).columns.tolist()]
    }

    # Detectar variáveis binárias (2 valores únicos)
    binarias = []
    for col in df.columns:
        if df[col].nunique(dropna=True) == 2:
            binarias.append(col)

    # Remover binárias de Numéricas e Categóricas
    tipos_colunas["Numéricas"] = [c for c in tipos_colunas["Numéricas"] if c not in binarias]
    tipos_colunas["Categóricas (object/category)"] = [c for c in tipos_colunas["Categóricas (object/category)"] if c not in binarias]
    tipos_colunas["Binárias"] = binarias

    # Mostrar apenas tipos com pelo menos uma coluna
    for tipo, cols in tipos_colunas.items():
        if cols:  
            print(f"🔹 {tipo} ({len(cols)} colunas):")
            print(cols, "\n")


    # =================== VALORES NULOS ===================
    nulos = df.isnull().sum().reset_index()
    nulos.columns = ["Coluna", "Nulos"]
    nulos = nulos[nulos["Nulos"] > 0]
    if not nulos.empty:
        nulos["% Nulos"] = (nulos["Nulos"] / total_linhas * 100).round(2).astype(str) + "%"
        print("Valores nulos por coluna:")
        print(tabulate(nulos, headers="keys", tablefmt="github"))
    else:
        print("Nenhuma coluna possui valores nulos.")
    print("\n")


def normalize_text(text):
    if pd.isna(text):
        return text
    
    text = re.sub(r'[\t\n\r]+', ' ', text)
    text = text.strip()

    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

    text = text.replace("'", "")

    text = text.lower()
    return text