import os
import sys
import pandas as pd
from etl.extract_data import extract_data
from etl.transform_data import transform_data_silevr_gold
from etl.load_data import load_data
from etl.utils import preencher_coordenadas
from datetime import datetime

class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()


BRONZE_DIR = os.path.join("data", "bronze")
GOLD_DIR = os.path.join("data", "gold")
LOG_DIR = os.path.join("logs")

for folder in [BRONZE_DIR, GOLD_DIR, LOG_DIR]:
    os.makedirs(folder, exist_ok=True)

log_path = os.path.join(LOG_DIR, "log.txt")
sys.stdout = Logger(log_path)
sys.stderr = sys.stdout 

def main():
    print("----------------------------------------------")
    print("- Camada Bronze - Extraindo Dados...")
    print("----------------------------------------------")
    url = "https://raw.githubusercontent.com/rafa-trindade/petstore-scraping/main/data/bronze/lojas_bronze.csv"
    df_bronze = extract_data(url)
    bronze_path = os.path.join(BRONZE_DIR, "lojas_bronze.csv")
    df_bronze.to_csv(bronze_path, index=False, sep=";", encoding="utf-8-sig")
    print(f"\n- Processo concluído. Arquivo salvo em: {bronze_path}")

    print("\n----------------------------------------------")
    print("- Camada Silver / Gold - Padronizando Dados...")
    print("----------------------------------------------")
    gold_path = os.path.join(GOLD_DIR, "lojas_gold.csv")
    df_gold = transform_data_silevr_gold(bronze_path)
    df_gold.to_csv(gold_path, index=False, sep=";", encoding="utf-8-sig")
    print(f"\nProcesso concluído. Arquivo salvo em: {gold_path}")

    print("\n----------------------------------------------")
    print("- Load - Carregando no Banco de Dados...")
    print("----------------------------------------------")
    df_gold['data_extracao'] = pd.to_datetime(df_gold['data_extracao'], errors='coerce').dt.date
    try:
        load_data(gold_path)
        print("7. Dados carregados com sucesso no PostgreSQL.")
    except Exception as e:
        print("\nErro durante a etapa de carga:")
        print(e)


def data_gold():
    print("\n----------------------------------------------")
    print("- Load - Carregando no Banco de Dados...")
    print("----------------------------------------------")
    try:
        gold_copy_path = os.path.join(GOLD_DIR, "lojas_gold_copy.csv")

        df_gold_final = pd.read_csv(gold_copy_path, sep=";", encoding="utf-8")
        df_gold_final = preencher_coordenadas(df_gold_final)

        gold_copy_final_path = os.path.join(GOLD_DIR, "lojas_gold_final.csv")
        df_gold_final.to_csv(gold_copy_final_path, index=False, sep=";", encoding="utf-8-sig")

        load_data(gold_copy_final_path)

        print("7. Dados carregados com sucesso no PostgreSQL.")
    except Exception as e:
        print("\nErro durante a etapa de carga:")
        print(e)


if __name__ == "__main__":
    main()
    #data_gold()