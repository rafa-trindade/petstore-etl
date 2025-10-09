import os
import requests
import pandas as pd
import unicodedata
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
HEADERS = {"Authorization": f"Token {API_TOKEN}"}


def preenche_campos(df, caminho_csv):

    mapa = pd.read_csv(caminho_csv, sep=";", encoding="utf-8-sig" )
    
    def normalizar_texto(txt):
        if pd.isna(txt):
            return txt
        txt = str(txt).lower().strip()
        txt = ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
        return txt
    
    df.rename(columns={"endereco": "logradouro"}, inplace=True)

    df['cidade_norm'] = df['cidade'].apply(normalizar_texto)
    df['estado_norm'] = df['estado'].apply(normalizar_texto)
    mapa['cidade_norm'] = mapa['cidade'].apply(normalizar_texto)
    mapa['estado_norm'] = mapa['estado'].apply(normalizar_texto)

    df_merged = pd.merge(
        df,
        mapa[['cidade_norm', 'estado_norm', 'cidade_cod_ibge', 'cidade_regiao', 'populacao', 'renda_domiciliar_per_capita']],
        on=['cidade_norm', 'estado_norm'],
        how='left'
    )

    df_merged = df_merged.rename(columns={'cidade_regiao': 'regiao'})

    colunas_finais = [
        'empresa', 'nome', 'logradouro', 'bairro', 'cidade', 'estado',
        'regiao', 'cep', 'populacao', 'latitude', 'longitude',
        'renda_domiciliar_per_capita', 'cidade_cod_ibge', 'data_extracao'
    ]

    for col in colunas_finais:
        if col not in df_merged.columns:
            df_merged[col] = None

    return df_merged[colunas_finais]



def normaliza_campos(df):
    
    for col in ["logradouro", "bairro", "cidade", "estado", "cep", "empresa", "nome"]:
        if col not in df.columns:
            df[col] = pd.Series(dtype="object")
        else:
            df[col] = df[col].astype("object")
    
    for col in ["latitude", "longitude"]:
        if col not in df.columns:
            df[col] = pd.Series(dtype="float")
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    total = len(df)
    
    for idx, row in df.iterrows():
        cep_atual = str(row.get("cep", "")).replace("-", "").strip()
        cidade_ibge = row.get("cidade_cod_ibge")
        empresa_nome = f"{row.get('empresa','')} - {row.get('nome','')}"
        print(f"Processando ({idx+1}/{total}): {empresa_nome}")
        
        if not cep_atual or cep_atual.lower() in ["nan", "none", ""]:
            if cidade_ibge:
                try:
                    url_ibge = f"https://www.cepaberto.com/api/v3/cep?ibge={cidade_ibge}"
                    response = requests.get(url_ibge, headers=HEADERS, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        cep_geral = data.get("cep", "")
                        if cep_geral:
                            cep_geral = cep_geral.replace("-", "")
                            df.at[idx, "cep"] = f"{cep_geral[:5]}-{cep_geral[5:]}"
                except Exception as e:
                    print(f" - Erro de conexão: {e}")
                    df.at[idx, "cep"] = df.at[idx, "cep"]
            else:
                df.at[idx, "cep"] = "indisponivel"
            cep_atual = str(df.at[idx, "cep"]).replace("-", "").strip()
        
        if cep_atual and cep_atual.lower() not in ["nan", "none", "indisponivel"]:
            try:
                url_cep = f"https://www.cepaberto.com/api/v3/cep?cep={cep_atual}"
                response = requests.get(url_cep, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data and data.get("cep"):
                        # Atualizar campos de texto
                        df.at[idx, "logradouro"] = data.get("logradouro", row.get("logradouro"))
                        df.at[idx, "bairro"] = data.get("bairro", row.get("bairro"))
                        df.at[idx, "cidade"] = data.get("cidade", {}).get("nome", row.get("cidade"))
                        df.at[idx, "estado"] = data.get("estado", {}).get("sigla", row.get("estado"))

                        cep_valid = data.get("cep").replace("-", "")
                        df.at[idx, "cep"] = f"{cep_valid[:5]}-{cep_valid[5:]}"
            except Exception as e:
                print(f" - Erro de conexão: {e}")
                df.at[idx, "cep"] = "erro conexao"
        
        lat = row.get("latitude")
        lon = row.get("longitude")
        if pd.isna(lat) or pd.isna(lon) or lat == "" or lon == "":
            try:
                if cep_atual and cep_atual.lower() not in ["nan", "none", "indisponivel"]:
                    url_latlon = f"https://www.cepaberto.com/api/v3/cep?cep={cep_atual}"
                    response = requests.get(url_latlon, headers=HEADERS, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        lat_api = data.get("latitude")
                        lon_api = data.get("longitude")
                        if lat_api is not None and lon_api is not None:
                            df.at[idx, "latitude"] = float(lat_api)
                            df.at[idx, "longitude"] = float(lon_api)
                            continue
            except:
                pass
            
            if cidade_ibge:
                try:
                    url_ibge = f"https://www.cepaberto.com/api/v3/cep?ibge={cidade_ibge}"
                    response = requests.get(url_ibge, headers=HEADERS, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        lat_api = data.get("latitude")
                        lon_api = data.get("longitude")
                        if lat_api is not None and lon_api is not None:
                            df.at[idx, "latitude"] = float(lat_api)
                            df.at[idx, "longitude"] = float(lon_api)
                except:
                    pass
    
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