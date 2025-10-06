import os
import sys
import pandas as pd
from etl.extract_data import extract_data
from etl.transform_data import transform_data_silver, transform_data_gold
from etl.load_data import load_data
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
SILVER_DIR = os.path.join("data", "silver")
GOLD_DIR = os.path.join("data", "gold")
LOG_DIR = os.path.join("logs")

for folder in [BRONZE_DIR, SILVER_DIR, GOLD_DIR, LOG_DIR]:
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
    print("- Camada Silver - Transformando Dados...")
    print("----------------------------------------------")
    silver_path = os.path.join(SILVER_DIR, "lojas_silver.csv")
    df_silver = transform_data_silver(bronze_path)
    df_silver.to_csv(silver_path, index=False, sep=";", encoding="utf-8-sig")
    print(f"\nProcesso concluído. Arquivo salvo em: {silver_path}")

    print("\n----------------------------------------------")
    print("- Camada Gold - Padronizando Dados...")
    print("----------------------------------------------")
    gold_path = os.path.join(GOLD_DIR, "lojas_gold.csv")
    df_gold = transform_data_gold(gold_path)
    df_gold.to_csv(gold_path, index=False, sep=";", encoding="utf-8-sig")
    print(f"\nProcesso concluído. Arquivo salvo em: {gold_path}")

    print("\n----------------------------------------------")
    print("- Load - Carregando no Banco de Dados...")
    print("----------------------------------------------")
    df_gold['data_extracao'] = pd.to_datetime(df_gold['data_extracao'], errors='coerce').dt.date
    try:
        load_data()
        print("7. Dados carregados com sucesso no PostgreSQL.")
    except Exception as e:
        print("\nErro durante a etapa de carga:")
        print(e)


def run_test():
    gold_path = os.path.join(GOLD_DIR, "lojas_gold.csv")
    df_gold = pd.read_csv(gold_path, sep=";", encoding="utf-8-sig")

    print("\n----------------------------------------------")
    print("- Load - Carregando no Banco de Dados...")
    print("----------------------------------------------")

    df_gold['data_extracao'] = pd.to_datetime(df_gold['data_extracao'], errors='coerce').dt.date
    try:
        load_data()
        print("7. Dados carregados com sucesso no PostgreSQL.")
    except Exception as e:
        print("\nErro durante a etapa de carga:")
        print(e)


if __name__ == "__main__":
    main()
    #run_test()