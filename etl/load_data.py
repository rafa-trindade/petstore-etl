import pandas as pd
from sqlalchemy import text
from config.db_config import engine

csv_path = "data/gold/lojas_gold.csv"

table_name = "lojas_gold"

def load_data():
    print("1. Iniciando processo de carga...")

    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    df.columns = [col.strip().lower() for col in df.columns]

    df['data_extracao'] = pd.to_datetime(df['data_extracao'], errors='coerce').dt.date
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id SERIAL PRIMARY KEY,
        empresa VARCHAR(100),
        nome VARCHAR(255),
        logradouro VARCHAR(255),
        bairro VARCHAR(100),
        cidade VARCHAR(100),
        estado VARCHAR(50),
        cep VARCHAR(20),
        latitude NUMERIC(10,6),
        longitude NUMERIC(10,6),
        data_extracao DATE
    );
    """
    with engine.begin() as conn:
        conn.execute(text(create_table_query))
        print(f"2. Tabela '{table_name}' verificada/criada com sucesso.")

        conn.execute(text(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = '{table_name}_unique'
                ) THEN
                    ALTER TABLE {table_name}
                    ADD CONSTRAINT {table_name}_unique UNIQUE (nome, logradouro);
                END IF;
            END$$;
        """))
        print("3. Constraint única verificada/criada.")

    temp_table = f"{table_name}_staging"
    df.to_sql(temp_table, engine, if_exists="replace", index=False)
    print(f"4. Dados carregados na tabela temporária '{temp_table}'.")

    upsert_query = f"""
    INSERT INTO {table_name} (
        empresa, nome, logradouro, bairro, cidade, estado, cep,
        latitude, longitude, data_extracao
    )
    SELECT
        empresa, nome, logradouro, bairro, cidade, estado, cep,
        latitude, longitude, data_extracao
    FROM {temp_table}
    ON CONFLICT (nome, logradouro) DO UPDATE
    SET
        empresa = EXCLUDED.empresa,
        bairro = EXCLUDED.bairro,
        cidade = EXCLUDED.cidade,
        estado = EXCLUDED.estado,
        cep = EXCLUDED.cep,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude,
        data_extracao = EXCLUDED.data_extracao;
    """

    with engine.begin() as conn:
        conn.execute(text(upsert_query))
        conn.execute(text(f"DROP TABLE IF EXISTS {temp_table};"))
        print(f"5 Dados mesclados na tabela '{table_name}' com sucesso.")

    print("5. Processo de carga concluído com sucesso!")

if __name__ == "__main__":
    load_data()
