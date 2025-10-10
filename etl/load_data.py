import pandas as pd
from sqlalchemy import text, types as sqltypes
from config.db_config import engine

table_name = "lojas_gold"

def load_data(csv_path):
    print("1. Iniciando processo de carga...")

    # --- Leitura do CSV e normalização ---
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    df.columns = [col.strip().lower() for col in df.columns]

    expected_columns = [
        'empresa', 'nome', 'logradouro', 'bairro', 'cidade', 'estado',
        'regiao', 'cep', 'populacao', 'latitude', 'longitude',
        'renda_domiciliar_per_capita', 'cod_cidade', 'data_extracao'
    ]

    for col in expected_columns:
        if col not in df.columns:
            df[col] = None  

    # --- Tratamento de tipos ---

    df['data_extracao'] = pd.to_datetime(df['data_extracao'], errors='coerce').dt.date

    # Coordenadas
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

    # População -> inteiro, remove pontos como separador de milhar
    df['populacao'] = df['populacao'].astype(str).str.replace('.', '', regex=False)
    df['populacao'] = pd.to_numeric(df['populacao'], errors='coerce').astype('Int64')

    # Renda
    df['renda_domiciliar_per_capita'] = pd.to_numeric(df['renda_domiciliar_per_capita'], errors='coerce')

    # Código IBGE -> texto (preserva zeros à esquerda)
    df['cod_cidade'] = df['cod_cidade'].astype(str).replace({'nan': None, 'None': None})

    # Normalização de strings
    df['nome'] = df['nome'].astype(str).str.strip().str.lower()
    df['logradouro'] = df['logradouro'].astype(str).str.strip().str.lower()

    # Remove duplicados
    df = df.drop_duplicates(subset=['nome', 'logradouro'])

    # --- Criação da tabela principal ---
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id SERIAL PRIMARY KEY,
        empresa VARCHAR(100),
        nome VARCHAR(255),
        logradouro VARCHAR(255),
        bairro VARCHAR(100),
        cidade VARCHAR(100),
        estado VARCHAR(50),
        regiao VARCHAR(50),
        cep VARCHAR(20),
        populacao BIGINT,
        latitude NUMERIC(10,6),
        longitude NUMERIC(10,6),
        renda_domiciliar_per_capita NUMERIC,
        cod_cidade VARCHAR(20),
        data_extracao DATE
    );
    """

    with engine.begin() as conn:
        conn.execute(text(create_table_query))
        print(f"2. Tabela '{table_name}' verificada/criada com sucesso.")

        # Constraint única
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

    # --- Carga na staging (tabela temporária) ---
    temp_table = f"{table_name}_staging"

    df.to_sql(
        temp_table,
        engine,
        if_exists="replace",
        index=False,
        dtype={
            'empresa': sqltypes.VARCHAR(100),
            'nome': sqltypes.VARCHAR(255),
            'logradouro': sqltypes.VARCHAR(255),
            'bairro': sqltypes.VARCHAR(100),
            'cidade': sqltypes.VARCHAR(100),
            'estado': sqltypes.VARCHAR(50),
            'regiao': sqltypes.VARCHAR(50),
            'cep': sqltypes.VARCHAR(20),
            'populacao': sqltypes.BIGINT,
            'latitude': sqltypes.NUMERIC(10,6),
            'longitude': sqltypes.NUMERIC(10,6),
            'renda_domiciliar_per_capita': sqltypes.NUMERIC,
            'cod_cidade': sqltypes.VARCHAR(20),
            'data_extracao': sqltypes.DATE
        }
    )

    print(f"4. Dados carregados na tabela temporária '{temp_table}'.")

    # --- Upsert (merge) ---
    upsert_query = f"""
    INSERT INTO {table_name} (
        empresa, nome, logradouro, bairro, cidade, estado,
        regiao, cep, populacao, latitude, longitude,
        renda_domiciliar_per_capita, cod_cidade, data_extracao
    )
    SELECT
        empresa, nome, logradouro, bairro, cidade, estado,
        regiao, cep, populacao, latitude, longitude,
        renda_domiciliar_per_capita, cod_cidade, data_extracao
    FROM {temp_table}
    ON CONFLICT (nome, logradouro) DO UPDATE
    SET
        empresa = EXCLUDED.empresa,
        bairro = EXCLUDED.bairro,
        cidade = EXCLUDED.cidade,
        estado = EXCLUDED.estado,
        regiao = EXCLUDED.regiao,
        cep = EXCLUDED.cep,
        populacao = EXCLUDED.populacao,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude,
        renda_domiciliar_per_capita = EXCLUDED.renda_domiciliar_per_capita,
        cod_cidade = EXCLUDED.cod_cidade,
        data_extracao = EXCLUDED.data_extracao;
    """

    with engine.begin() as conn:
        total_antes = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar()
        print(f"--- Registros antes da carga: {total_antes}")

        conn.execute(text(upsert_query))

        total_depois = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar()
        print(f"--- Registros depois da carga: {total_depois}")

        conn.execute(text(f"DROP TABLE IF EXISTS {temp_table};"))
        print(f"5. Dados mesclados na tabela '{table_name}' com sucesso.")

    print("6. Processo de carga concluído com sucesso!")


if __name__ == "__main__":
    load_data("dados.csv")
