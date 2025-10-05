import pandas as pd

def extract_data(url):
    
    df_bronze = pd.read_csv(url, sep=";", encoding="utf-8")
    print(f"Extraindo de {url.split('rafa-trindade/', 1)[1]}")

    return df_bronze
