import pandas as pd

def extract_data(url):
    
    df_bronze = pd.read_csv(url, sep=";", encoding="utf-8")

    return df_bronze
