"""Catálogo de skills: nome canônico -> (categoria, lista de apelidos/regex).

Os apelidos são regex aplicadas em texto minúsculo, com fronteiras que aceitam
símbolos (C#, .NET, Node.js). Para adicionar uma skill, basta incluir uma linha.
"""

import re

SKILLS: dict[str, tuple[str, list[str]]] = {
    # Linguagens
    "Python": ("Linguagens", [r"python"]),
    "SQL": ("Linguagens", [r"sql", r"t-sql", r"pl/sql", r"spark sql"]),
    "Scala": ("Linguagens", [r"scala"]),
    "Java": ("Linguagens", [r"java"]),
    "R": ("Linguagens", [r"linguagem r", r"r language", r"rstudio", r"r programming"]),
    "Go": ("Linguagens", [r"golang", r"go lang"]),
    "C#": ("Linguagens", [r"c#", r"\.net", r"dotnet"]),
    "JavaScript": ("Linguagens", [r"javascript", r"js"]),
    "TypeScript": ("Linguagens", [r"typescript"]),
    "Shell/Bash": ("Linguagens", [r"bash", r"shell script(ing)?", r"powershell"]),
    # Processamento / Big Data
    "Spark": ("Processamento", [r"spark", r"apache spark"]),
    "PySpark": ("Processamento", [r"pyspark"]),
    "Hadoop": ("Processamento", [r"hadoop", r"hdfs"]),
    "Hive": ("Processamento", [r"hive"]),
    "Kafka": ("Streaming", [r"kafka"]),
    "Flink": ("Streaming", [r"flink"]),
    "Kinesis": ("Streaming", [r"kinesis"]),
    "Streaming": ("Streaming", [r"streaming", r"real[- ]time", r"tempo real"]),
    "Pandas": ("Processamento", [r"pandas"]),
    "Polars": ("Processamento", [r"polars"]),
    "Trino/Presto": ("Processamento", [r"trino", r"presto"]),
    # Plataformas
    "Databricks": ("Plataformas de dados", [r"databricks"]),
    "Snowflake": ("Plataformas de dados", [r"snowflake"]),
    "BigQuery": ("Plataformas de dados", [r"bigquery", r"big query"]),
    "Redshift": ("Plataformas de dados", [r"redshift"]),
    "Synapse": ("Plataformas de dados", [r"synapse"]),
    "Microsoft Fabric": ("Plataformas de dados", [r"microsoft fabric", r"ms fabric"]),
    "Delta Lake": ("Plataformas de dados", [r"delta lake", r"delta tables?"]),
    "Apache Iceberg": ("Plataformas de dados", [r"iceberg"]),
    "Unity Catalog": ("Plataformas de dados", [r"unity catalog"]),
    # Orquestração / ingestão
    "Airflow": ("Orquestração", [r"airflow", r"mwaa", r"cloud composer"]),
    "dbt": ("Orquestração", [r"dbt"]),
    "Data Factory": ("Orquestração", [r"data factory", r"adf"]),
    "Prefect": ("Orquestração", [r"prefect"]),
    "Dagster": ("Orquestração", [r"dagster"]),
    "Airbyte": ("Orquestração", [r"airbyte"]),
    "Fivetran": ("Orquestração", [r"fivetran"]),
    "NiFi": ("Orquestração", [r"nifi"]),
    # Cloud
    "AWS": ("Cloud", [r"aws", r"amazon web services"]),
    "Azure": ("Cloud", [r"azure"]),
    "GCP": ("Cloud", [r"gcp", r"google cloud"]),
    "AWS Glue": ("Cloud", [r"glue"]),
    "AWS Lambda": ("Cloud", [r"lambda"]),
    "S3": ("Cloud", [r"s3"]),
    "EMR": ("Cloud", [r"emr"]),
    "Athena": ("Cloud", [r"athena"]),
    # Bancos de dados
    "PostgreSQL": ("Bancos de dados", [r"postgres(ql)?"]),
    "MySQL": ("Bancos de dados", [r"mysql"]),
    "SQL Server": ("Bancos de dados", [r"sql server", r"mssql"]),
    "Oracle": ("Bancos de dados", [r"oracle"]),
    "MongoDB": ("Bancos de dados", [r"mongo(db)?"]),
    "NoSQL": ("Bancos de dados", [r"nosql"]),
    "Cassandra": ("Bancos de dados", [r"cassandra"]),
    "DynamoDB": ("Bancos de dados", [r"dynamo(db)?"]),
    "Redis": ("Bancos de dados", [r"redis"]),
    "Elasticsearch": ("Bancos de dados", [r"elastic ?search", r"opensearch"]),
    # Conceitos
    "ETL/ELT": ("Conceitos", [r"etl", r"elt", r"pipelines? de dados", r"data pipelines?"]),
    "Modelagem de dados": ("Conceitos", [r"modelagem de dados", r"data model(l)?ing",
                                         r"modelagem dimensional", r"dimensional model(l)?ing",
                                         r"star schema", r"kimball", r"data vault"]),
    "Data Warehouse": ("Conceitos", [r"data ?warehouse", r"dw", r"dwh"]),
    "Data Lake/Lakehouse": ("Conceitos", [r"data ?lake", r"lakehouse", r"medallion"]),
    "Qualidade de dados": ("Conceitos", [r"qualidade de dados", r"data quality",
                                         r"great expectations", r"soda"]),
    "Governança de dados": ("Conceitos", [r"governança de dados", r"data governance",
                                          r"lgpd", r"gdpr", r"data catalog"]),
    "APIs REST": ("Conceitos", [r"apis?", r"rest(ful)?"]),
    "Estruturas de dados/Algoritmos": ("Conceitos", [r"estruturas? de dados", r"data structures",
                                                     r"algoritmos", r"algorithms"]),
    # DevOps
    "Git": ("DevOps", [r"git", r"github", r"gitlab", r"bitbucket"]),
    "CI/CD": ("DevOps", [r"ci/cd", r"ci ?cd", r"github actions", r"azure devops", r"jenkins"]),
    "Docker": ("DevOps", [r"docker", r"containers?"]),
    "Kubernetes": ("DevOps", [r"kubernetes", r"k8s", r"eks", r"aks", r"gke"]),
    "Terraform": ("DevOps", [r"terraform", r"iac", r"infra(structure)? as code"]),
    "Linux": ("DevOps", [r"linux", r"unix"]),
    # BI / Analytics
    "Power BI": ("BI/Analytics", [r"power ?bi", r"dax"]),
    "Tableau": ("BI/Analytics", [r"tableau"]),
    "Looker": ("BI/Analytics", [r"looker", r"looker studio", r"data studio"]),
    "Excel": ("BI/Analytics", [r"excel"]),
    "Estatística": ("BI/Analytics", [r"estat[íi]stica", r"statistics?"]),
    # ML / IA
    "Machine Learning": ("ML/IA", [r"machine learning", r"aprendizado de máquina", r"ml"]),
    "Scikit-learn": ("ML/IA", [r"scikit[- ]learn", r"sklearn"]),
    "TensorFlow": ("ML/IA", [r"tensorflow", r"keras"]),
    "PyTorch": ("ML/IA", [r"pytorch"]),
    "MLflow": ("ML/IA", [r"mlflow"]),
    "MLOps": ("ML/IA", [r"mlops"]),
    "IA Generativa/LLM": ("ML/IA", [r"llms?", r"genai", r"generative ai", r"ia generativa",
                                    r"rag", r"langchain"]),
    "NLP": ("ML/IA", [r"nlp", r"processamento de linguagem natural", r"natural language processing"]),
    # Métodos e idiomas
    "Metodologias ágeis": ("Métodos", [r"scrum", r"kanban", r"agile", r"ágil", r"metodologias? ágeis"]),
    "Inglês": ("Idiomas", [r"inglês", r"ingles", r"english"]),
    "Espanhol": ("Idiomas", [r"espanhol", r"spanish"]),
}

# Fronteira que funciona com "c#", ".net", "ci/cd": não pode haver letra/dígito colado.
_B_START = r"(?<![a-z0-9à-ú])"
_B_END = r"(?![a-z0-9à-ú])"


def _compile(aliases: list[str]) -> re.Pattern:
    body = "|".join(aliases)
    return re.compile(f"{_B_START}(?:{body}){_B_END}", re.IGNORECASE)


PATTERNS: dict[str, re.Pattern] = {name: _compile(a) for name, (_, a) in SKILLS.items()}


def category(skill: str) -> str:
    return SKILLS.get(skill, ("Outras", []))[0]


def add_custom_skills(names: list[str]) -> None:
    """Registra skills digitadas pelo usuário (match literal pelo próprio nome)."""
    for name in names:
        name = name.strip()
        if name and name not in PATTERNS:
            SKILLS[name] = ("Personalizadas", [re.escape(name.lower())])
            PATTERNS[name] = _compile([re.escape(name.lower())])


def extract_skills(text: str) -> set[str]:
    text = text.lower()
    return {name for name, pat in PATTERNS.items() if pat.search(text)}
