import os
import re
import requests
import pandas as pd
import unicodedata
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
HEADERS = {"Authorization": f"Token {API_TOKEN}"}


def preenche_campos(df, caminho_csv):
    # Lê o parquet
    mapa = pd.read_csv(caminho_csv, sep=";", encoding="utf-8-sig" )
    
    # Função para normalizar texto (remove acentos, lowercase)
    def normalizar_texto(txt):
        if pd.isna(txt):
            return txt
        txt = str(txt).lower().strip()
        txt = ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
        return txt
    
    df.rename(columns={"endereco": "logradouro"})

    # Cria colunas temporárias normalizadas
    df['cidade_norm'] = df['cidade'].apply(normalizar_texto)
    df['estado_norm'] = df['estado'].apply(normalizar_texto)
    mapa['cidade_norm'] = mapa['cidade'].apply(normalizar_texto)
    mapa['estado_norm'] = mapa['estado'].apply(normalizar_texto)

    # Merge usando as colunas normalizadas
    df_merged = pd.merge(
        df,
        mapa[['cidade_norm', 'estado_norm', 'cidade_cod_ibge', 'cidade_regiao', 'populacao', 'renda_domiciliar_per_capita']],
        on=['cidade_norm', 'estado_norm'],
        how='left'
    )

    # Renomeia cidade_regiao -> regiao
    df_merged = df_merged.rename(columns={'cidade_regiao': 'regiao'})

    # Define a ordem final das colunas
    colunas_finais = [
        'empresa', 'nome', 'logradouro', 'bairro', 'cidade', 'estado',
        'regiao', 'cep', 'populacao', 'latitude', 'longitude',
        'renda_domiciliar_per_capita', 'cidade_cod_ibge', 'data_extracao'
    ]

    # Garante que todas as colunas existam
    for col in colunas_finais:
        if col not in df_merged.columns:
            df_merged[col] = None

    # Retorna o DataFrame final
    return df_merged[colunas_finais]


def normaliza_campos(df):
    """
    Normaliza CEPs no DataFrame e preenche logradouro, bairro, cidade, estado,
    além de latitude e longitude.
    """
    df = df.copy()
    total = len(df)

    for idx, row in df.iterrows():
        cep_atual = str(row.get("cep", "")).replace("-", "").strip()
        cidade_ibge = row.get("cidade_cod_ibge")
        empresa_nome = f"{row.get('empresa','')} - {row.get('nome','')}"
        
        print(f"Processando ({idx+1}/{total}): {empresa_nome}")

        # ===============================
        # PARTE 1: NORMALIZAÇÃO CEP E ENDEREÇO
        # ===============================

        # Se CEP vazio, busca o CEP geral via cidade_cod_ibge
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
                        else:
                            df.at[idx, "cep"] = df.at[idx, "cep"]
                    else:
                        df.at[idx, "cep"] = df.at[idx, "cep"]
                except Exception as e:
                    print(f" - Erro de conexão: {e}")
                    df.at[idx, "cep"] = df.at[idx, "cep"]
            else:
                df.at[idx, "cep"] = "indisponivel"
            # Após preencher CEP, continua para próxima etapa
            cep_atual = str(df.at[idx, "cep"]).replace("-", "").strip()

        # CEP preenchido: consulta para validar e atualizar endereço
        if cep_atual and cep_atual.lower() not in ["nan", "none", "indisponivel"]:
            try:
                url_cep = f"https://www.cepaberto.com/api/v3/cep?cep={cep_atual}"
                response = requests.get(url_cep, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data and data.get("cep"):
                        # CEP válido → atualiza endereço
                        df.at[idx, "logradouro"] = data.get("logradouro", row.get("logradouro"))
                        df.at[idx, "bairro"] = data.get("bairro", row.get("bairro"))
                        df.at[idx, "cidade"] = data.get("cidade", {}).get("nome", row.get("cidade"))
                        df.at[idx, "estado"] = data.get("estado", {}).get("sigla", row.get("estado"))
                        # Normaliza CEP
                        cep_valid = data.get("cep").replace("-", "")
                        df.at[idx, "cep"] = f"{cep_valid[:5]}-{cep_valid[5:]}"
                    else:
                        # CEP inválido → preenche com CEP geral via cidade_cod_ibge
                        if cidade_ibge:
                            try:
                                url_ibge = f"https://www.cepaberto.com/api/v3/cep?ibge={cidade_ibge}"
                                resp_ibge = requests.get(url_ibge, headers=HEADERS, timeout=10)
                                if resp_ibge.status_code == 200:
                                    data_ibge = resp_ibge.json()
                                    cep_geral = data_ibge.get("cep", "")
                                    if cep_geral:
                                        cep_geral = cep_geral.replace("-", "")
                                        df.at[idx, "cep"] = f"{cep_geral[:5]}-{cep_geral[5:]}"
                            except:
                                pass
            except Exception as e:
                print(f" - Erro de conexão: {e}")
                df.at[idx, "cep"] = "erro conexao"

        # ===============================
        # PARTE 2: PREENCHE LATITUDE E LONGITUDE
        # ===============================
        lat = row.get("latitude")
        lon = row.get("longitude")

        if pd.isna(lat) or pd.isna(lon) or lat == "" or lon == "":
            # Tenta obter pelo CEP
            try:
                if cep_atual and cep_atual.lower() not in ["nan", "none", "indisponivel"]:
                    url_latlon = f"https://www.cepaberto.com/api/v3/cep?cep={cep_atual}"
                    response = requests.get(url_latlon, headers=HEADERS, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        lat_api = data.get("latitude")
                        lon_api = data.get("longitude")
                        if lat_api is not None and lon_api is not None:
                            df.at[idx, "latitude"] = lat_api
                            df.at[idx, "longitude"] = lon_api
                            continue  # já preencheu, passa para próxima linha
            except:
                pass

            # Se não obteve pelo CEP, tenta pelo cidade_cod_ibge
            if cidade_ibge:
                try:
                    url_ibge = f"https://www.cepaberto.com/api/v3/cep?ibge={cidade_ibge}"
                    response = requests.get(url_ibge, headers=HEADERS, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        lat_api = data.get("latitude")
                        lon_api = data.get("longitude")
                        if lat_api is not None and lon_api is not None:
                            df.at[idx, "latitude"] = lat_api
                            df.at[idx, "longitude"] = lon_api
                except:
                    pass
        # Se lat/lon já existirem, mantém como estão

    return df



SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

def atualizar_lat_long(df, nome_coluna='nome', lat_coluna='latitude', lon_coluna='longitude'):
    """
    Atualiza latitude e longitude no DataFrame usando a API SerpAPI Maps
    apenas para linhas onde latitude ou longitude estão vazias.
    
    Args:
        df (pd.DataFrame): DataFrame com pelo menos as colunas nome, latitude, longitude
        nome_coluna (str): nome da coluna que será usada para pesquisa
        lat_coluna (str): nome da coluna de latitude
        lon_coluna (str): nome da coluna de longitude
        
    Returns:
        pd.DataFrame: DataFrame atualizado
    """
    
    # Itera somente pelas linhas com latitude ou longitude vazias
    for idx, row in df[df[lat_coluna].isna() | df[lon_coluna].isna()].iterrows():
        query = row[nome_coluna]
        
        # Monta a requisição para SerpAPI
        params = {
            "engine": "google_maps",
            "q": query,
            "api_key": SERPAPI_API_KEY
        }
        
        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()
        
        try:
            # Pega o primeiro resultado e extrai latitude e longitude
            location = data['local_results'][0]['gps_coordinates']
            lat_api = float(location['latitude'])
            lon_api = float(location['longitude'])
            
            df.at[idx, lat_coluna] = lat_api
            df.at[idx, lon_coluna] = lon_api
        except (KeyError, IndexError, ValueError):
            print(f"Não foi possível obter coordenadas para: {query}")
            continue
    
    return df