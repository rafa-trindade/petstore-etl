import pandas as pd
from etl.utils import limpar_texto



def extract_data(url):
    df_bronze = pd.read_csv(url, sep=";", encoding="utf-8")
    
    cols_to_normalize = ["nome", "cidade", "endereco", "bairro"]
    
    for col in cols_to_normalize:
        if col in df_bronze.columns:
            df_bronze[col] = df_bronze[col].apply(limpar_texto)
    
    return df_bronze