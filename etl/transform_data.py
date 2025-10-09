import os
import re
import pandas as pd
import numpy as np
import time
from serpapi import GoogleSearch
from etl.utils import preenche_campos, normaliza_campos


IBGE_CSV = "data/utils/ibge_data.csv"

def transform_data_silver(csv_path):

    df_silver = pd.read_csv(csv_path, sep=";", encoding="utf-8")

    #df_silver = df_silver.tail(1)
    
    df_silver = preenche_campos(df_silver, IBGE_CSV)
    
    return df_silver



def transform_data_gold(csv_path):

    df_gold = pd.read_csv(csv_path, sep=";", encoding="utf-8")

    df_gold = normaliza_campos(df_gold)

    return df_gold