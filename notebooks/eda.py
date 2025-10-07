#%%
import pandas as pd
from utils import eda

#df = pd.read_csv("../data/silver/lojas_silver.csv", sep=";", encoding="utf-8")
df = pd.read_csv("../data/gold/lojas_gold.csv", sep=";", encoding="utf-8")

eda(df)