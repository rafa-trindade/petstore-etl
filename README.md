# 🐾 petstore-etl

Projeto responsável pela **extração, transformação e carga (ETL)** de dados coletados pelo projeto [`petstore-scraping`](https://github.com/rafa-trindade/petstore-scraping).  

Esta etapa compõe as camadas **Silver e Gold** da arquitetura de dados, realizando **limpeza, padronização, enriquecimento e carga no PostgreSQL**.

Os dados tratados e carregados no **PostgreSQL** nesse projeto serão consumidos pelo projeto [`petstore-bi`](https://github.com/rafa-trindade/petstore-bi) para BI e Dashboards.

---

## 📌 Descrição

O `petstore-etl` consome os dados brutos (camada Bronze) gerados pelo [`petstore-scraping`](https://github.com/rafa-trindade/petstore-scraping) e executa as seguintes camadas:

* **🟤 Extractc (Bronze):** coleta dos arquivos brutos disponibilizados pelo [`petstore-scraping`](https://github.com/rafa-trindade/petstore-scraping) via link público (raw).  
* **⚪ Transform (Silver):** limpeza, padronização e enriquecimento dos dados, incluindo preenchimento de endereços e coordenadas geográficas.
* **🟡 Load (Gold):** integração final e carga no banco de dados, preparando os dados para análise e visualização no [`petstore-bi`](https://github.com/rafa-trindade/petstore-bi).

---

## 📊 Estrutura dos Dados

As principais colunas tratadas e enriquecidas (incluindo latitude e longitude) são:

| id | empresa | nome | logradouro | bairro | cidade | estado | cep | latitude | longitude | data_extracao |
| -- | ------- | ---- | ---------- | ------ | ------ | ------ | --- | -------- | --------- | ------------- |

---

## 🧩 Fluxo de Dados

```mermaid
graph TD
    A[petstore-scraping<br>Bronze] --> B[[petstore-etl<br>Silver e Gold<br>PostgreSQL]]
    B --> C[petstore-bi<br>BI e Dashboards]
```

---

## 📊 Estrutura do Projeto Final

| Repositório | Função | Camada | Principais Tecnologias |
| ----------------- | ----------------------------- | ------------------ | -------------------------------------- |
| [`petstore-scraping`](https://github.com/rafa-trindade/petstore-scraping) | Coleta de Dados de Franquias | 🟤 Bronze | Selenium, BeautifulSoup4, lxml, pandas |
| [`petstore-etl`](https://github.com/rafa-trindade/petstore-etl) | Limpeza, Padronização e Carga | ⚪ Silver / 🟡 Gold | pandas, brazilcep, requests, numpy, tabulate, SQLAlchemy, psycopg2-binary, python-dotenv |
| [`petstore-bi`](https://github.com/rafa-trindade/petstore-bi) | BI e Dashboards | 📊 BI | Streamlit, Plotly, pandas |

---

## ⚙️ Tecnologias e Bibliotecas `petstore-etl`

* [**pandas**](https://pypi.org/project/pandas/) → manipulação e estruturação de dados tabulares  
* [**brazilcep**](https://pypi.org/project/brazilcep/) → padronização de logradouros, bairros, cidades e estados  
* [**requests**](https://pypi.org/project/requests/) → chamadas HTTP para APIs externas  
* [**numpy**](https://pypi.org/project/numpy/) → operações numéricas e vetoriais  
* [**tabulate**](https://pypi.org/project/tabulate/) → exibição de tabelas no terminal de forma legível  
* [**SQLAlchemy**](https://pypi.org/project/SQLAlchemy/) → conexão e manipulação de bancos de dados SQL de forma programática  
* [**psycopg2-binary**](https://pypi.org/project/psycopg2-binary/) → driver PostgreSQL para Python  
* [**python-dotenv**](https://pypi.org/project/python-dotenv/) → leitura de variáveis de ambiente a partir de arquivos `.env`


O projeto utiliza a API **Nominatim (OpenStreetMap)** para obter informações de **latitude e longitude**, além de preencher campos ausentes de endereço (logradouro, bairro, cidade, estado).  

> Identificação da aplicação: `USER_AGENT = "petstore-etl/1.0"`

---

## 🖥️ Log de Execução `petstore-etl`

```text
----------------------------------------------
- Camada Bronze - Extraindo Dados...
----------------------------------------------
Extraindo de petstore-scraping/main/data/bronze/lojas_bronze.csv

- Processo concluído. Arquivo salvo em: data\bronze\lojas_bronze.csv

----------------------------------------------
- Camada Silver - Transformando Dados...
----------------------------------------------
Processado 1/533: petz - Petz Abelardo Bueno
Processado 2/533: petz - Petz Aclimação
Processado 3/533: petz - Petz Afonso Pena
Processado 4/533: petz - Petz Agamenon
Processado 5/533: petz - Petz Águas Claras
...
Processo concluído. Arquivo salvo em: data\silver\lojas_silver.csv

----------------------------------------------
- Camada Gold - Padronizando Dados...
----------------------------------------------
>> type(df): <class 'pandas.core.frame.DataFrame'>
>> shape: (533, 9)
>> colunas: ['empresa', 'nome', 'logradouro', 'bairro', 'cidade', 'estado', 'cep', 'latitude', 'longitude']
>> colunas de endereço garantidas no DataFrame.
>> 515 CEP(s) únicos encontrados para consulta (ex.: ['22775-040' '01534-000' '79005-671' '50050-290' '71928-720'])
[1/515] 22775-040 -> {'logradouro': 'Avenida Embaixador Abelardo Bueno', 'bairro': 'Barra da Tijuca', 'cidade': 'Rio de Janeiro', 'estado': 'RJ'}
[2/515] 01534-000 -> {'logradouro': 'Rua Muniz de Sousa', 'bairro': 'Aclimação', 'cidade': 'São Paulo', 'estado': 'SP'}
[3/515] 79005-671 -> {'logradouro': 'Avenida Bandeirantes', 'bairro': 'Amambaí', 'cidade': 'Campo Grande', 'estado': 'MS'}
[4/515] 50050-290 -> {'logradouro': 'Avenida Governador Agamenon Magalhães', 'bairro': 'Boa Vista', 'cidade': 'Recife', 'estado': 'PE'}
[5/515] 71928-720 -> {'logradouro': 'Avenida Sibipiruna', 'bairro': 'Sul (Águas Claras)', 'cidade': 'Brasília', 'estado': 'DF'}
...
>> Campo 'logradouro' preenchido com base no CEP.
>> Campo 'bairro' preenchido com base no CEP.
>> Campo 'cidade' preenchido com base no CEP.
>> Campo 'estado' preenchido com base no CEP.
>> Preenchimento concluído com sucesso!
         cep                             logradouro                                    bairro          cidade estado
0  22775-040      Avenida Embaixador Abelardo Bueno                           Barra da Tijuca  Rio de Janeiro     RJ
1  01534-000                     Rua Muniz de Sousa                                 Aclimação       São Paulo     SP
2  79005-671                   Avenida Bandeirantes                                   Amambaí    Campo Grande     MS
3  50050-290  Avenida Governador Agamenon Magalhães                                 Boa Vista          Recife     PE
4  71928-720                     Avenida Sibipiruna                        Sul (Águas Claras)        Brasília     DF
5  01419-001                         Alameda Santos                           Cerqueira César       São Paulo     
...

Processo concluído. Arquivo salvo em: data\gold\lojas_gold.csv


----------------------------------------------
- Load - Carregando no Banco de Dados...
----------------------------------------------
1. Iniciando processo de carga...
2. Tabela 'lojas_gold' verificada/criada com sucesso.
3. Constraint única verificada/criada.
4. Dados carregados na tabela temporária 'lojas_gold_staging'.
5 Dados mesclados na tabela 'lojas_gold' com sucesso.
5. Processo de carga concluído com sucesso!
6. Dados carregados com sucesso no PostgreSQL.
```
🔗 [Ver log completo](https://raw.githubusercontent.com/rafa-trindade/petstore-etl/refs/heads/main/logs/log.txt)

---

## 🔗 Integração com Projeto de BI

Os dados carregados no **PostgreSQL** pelo **`petstore-etl`** devem ser consumidos pelo projeto **`petstore-bi`** para BI e Dashboards.

---

## 🗄️ Tabela Temporária `lojas_gold_staging`

- Durante o processo de carga, os dados do CSV são inseridos nessa tabela temporária.  
- Em seguida, é feito o **UPSERT** para a tabela principal `lojas_gold`, garantindo que não haja duplicatas.  
- Ao final da execução, a tabela `lojas_gold_staging` é **removida automaticamente**, garantindo que apenas os dados finais permaneçam na tabela principal.

---

## 🏪 Redes Suportadas

Atualmente, o projeto coleta e trata dados das seguintes redes:

* **Petz**
* **Cobasi**
* **Petlove**
