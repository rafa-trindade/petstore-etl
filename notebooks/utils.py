import pandas as pd
from tabulate import tabulate

def eda(df, coluna_cat=None):
    """
    Executa uma Análise Exploratória de Dados (EDA) inicial em um DataFrame.
    Inclui listagem completa de colunas por tipo, contagem de nulos, duplicados,
    estatísticas descritivas, variáveis binárias e resumo final.

    Parâmetros:
        df (pd.DataFrame): dataset a ser analisado.
        coluna_cat (str, opcional): nome de uma coluna categórica para exibir gráfico de contagem.

    Retorno:
        None - imprime resultados.
    """

    total_linhas = df.shape[0]
    total_cols = df.shape[1]

    print("="*60)
    print("📊 METADADOS DO DATASET")
    print("="*60)
    print(f"Dimensão: {total_linhas} linhas x {total_cols} colunas\n")

    # =================== LISTAGEM DE COLUNAS POR TIPO ===================
    tipos_colunas = {
        "Numéricas": df.select_dtypes(include=['int64', 'float64']).columns.tolist(),
        "Categóricas (object/category)": df.select_dtypes(include=['object', 'category']).columns.tolist(),
        "Booleanas": df.select_dtypes(include=['bool']).columns.tolist(),
        "Datas": df.select_dtypes(include=['datetime64[ns]']).columns.tolist(),
        "Períodos": [c for c in df.columns if pd.api.types.is_period_dtype(df[c])],
        "Timedeltas": df.select_dtypes(include=['timedelta64[ns]']).columns.tolist(),
        "Outros tipos": [c for c in df.columns if c not in 
                        df.select_dtypes(include=['int64','float64','object','category','bool','datetime64[ns]','timedelta64[ns]']).columns.tolist()]
    }

    # Detectar variáveis binárias (2 valores únicos)
    binarias = []
    for col in df.columns:
        if df[col].nunique(dropna=True) == 2:
            binarias.append(col)

    # Remover binárias de Numéricas e Categóricas
    tipos_colunas["Numéricas"] = [c for c in tipos_colunas["Numéricas"] if c not in binarias]
    tipos_colunas["Categóricas (object/category)"] = [c for c in tipos_colunas["Categóricas (object/category)"] if c not in binarias]
    tipos_colunas["Binárias"] = binarias

    # Mostrar apenas tipos com pelo menos uma coluna
    for tipo, cols in tipos_colunas.items():
        if cols:  
            print(f"🔹 {tipo} ({len(cols)} colunas):")
            print(cols, "\n")

    # =================== TIPOS DE VARIÁVEIS ===================
    tipos = df.dtypes.value_counts().reset_index()
    tipos.columns = ["Tipo", "Quantidade"]
    print("Tipos de variáveis:")
    print(tabulate(tipos, headers="keys", tablefmt="github"))
    print("\n")

    # =================== VALORES NULOS ===================
    nulos = df.isnull().sum().reset_index()
    nulos.columns = ["Coluna", "Nulos"]
    nulos = nulos[nulos["Nulos"] > 0]
    if not nulos.empty:
        nulos["% Nulos"] = (nulos["Nulos"] / total_linhas * 100).round(2).astype(str) + "%"
        print("Valores nulos por coluna:")
        print(tabulate(nulos, headers="keys", tablefmt="github"))
    else:
        print("Nenhuma coluna possui valores nulos.")
    print("\n")

    # =================== DUPLICADOS ===================
    qtd_dup = df.duplicated().sum()
    perc_dup = round((qtd_dup / total_linhas) * 100, 2)
    print(f"Duplicados: {qtd_dup} registros ({perc_dup}%)\n")

    # =================== ESTATÍSTICAS DESCRITIVAS ===================
    print("="*60)
    print("📈 ESTATÍSTICAS DESCRITIVAS")
    print("="*60)

    num_desc = df.describe().T.reset_index()
    num_desc = num_desc.round(2)
    if not num_desc.empty:
        print("\nNuméricas:")
        print(tabulate(num_desc, headers="keys", tablefmt="github"))

    cat_desc = df.describe(include=['object', 'category']).T.reset_index()
    if not cat_desc.empty:
        print("\nCategóricas:")
        print(tabulate(cat_desc, headers="keys", tablefmt="github"))

    date_cols = df.select_dtypes(include=['datetime64[ns]']).columns
    if len(date_cols) > 0:
        print("\nDatas (mínimo e máximo):")
        datas_info = []
        for col in date_cols:
            datas_info.append([col, df[col].min(), df[col].max()])
        print(tabulate(datas_info, headers=["Coluna", "Mínimo", "Máximo"], tablefmt="github"))

    # =================== DASHBOARD RESUMO ===================
    print("\n")
    print("="*60)
    print("📋 RESUMO FINAL DO DATASET")
    print("="*60)

    resumo = [
        ["Linhas", total_linhas, "100%"],
        ["Colunas", total_cols, "100%"]
    ]

    for tipo in ["Numéricas", "Categóricas (object/category)", "Booleanas", "Binárias",
                 "Datas", "Períodos", "Timedeltas", "Outros tipos"]:
        qtd = len(tipos_colunas.get(tipo, []))
        if qtd > 0:
            resumo.append([tipo, qtd, f"{round(qtd/total_cols*100,2)}%"])

    resumo.append(["Duplicados", qtd_dup, f"{perc_dup}%"])
    resumo.append(["Valores nulos (total)", df.isnull().sum().sum(), f"{round(df.isnull().sum().sum()/(total_linhas*total_cols)*100,2)}%"])

    print(tabulate(resumo, headers=["Métrica", "Valor", "%"], tablefmt="github"))

    nulos_col = df.isnull().sum()
    if nulos_col.sum() > 0:
        mais_nulos = nulos_col.idxmax(), nulos_col.max(), round((nulos_col.max()/total_linhas)*100,2)
        menos_nulos = nulos_col[nulos_col > 0].idxmin(), nulos_col[nulos_col > 0].min(), round((nulos_col[nulos_col>0].min()/total_linhas)*100,2)
        tabela_nulos = [
            ["Mais nulos", mais_nulos[0], mais_nulos[1], f"{mais_nulos[2]}%"],
            ["Menos nulos", menos_nulos[0], menos_nulos[1], f"{menos_nulos[2]}%"]
        ]
        print("\nColunas com mais e menos nulos:")
        print(tabulate(tabela_nulos, headers=["Tipo", "Coluna", "Qtd", "%"], tablefmt="github"))
