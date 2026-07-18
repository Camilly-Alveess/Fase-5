# Datathon - Postgraduate project
## Plataforma de Experimentação Adaptativa para Canal de Contato (Multi-Armed Bandit)

## Visão do problema

Uma instituição financeira digital precisa decidir, para cada cliente elegível, **qual canal usar para contatá-lo** (uma oferta/mensagem/próximo passo). Regras fixas e testes A/B longos desperdiçam tráfego e demoram a reagir a mudanças de contexto.

Este projeto implementa uma abordagem **adaptativa (multi-armed bandit)** sobre a base pública [Bank Marketing (Kaggle — henriqueyamahata)](https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing), usando a decisão de **canal de contato** (`cellular` vs `telephone`) como os braços do bandit e a **adesão ao produto** (`y`) como recompensa.

| Elemento do bandit | Mapeamento na base |
|---|---|
| **Braços (arms)** | Canal de contato: `cellular` vs `telephone` |
| **Contexto** | Se o cliente converteu em campanha anterior (`poutcome == success`) |
| **Recompensa** | `y` — cliente aderiu ao depósito a prazo (1) ou não (0) |

**Algoritmo escolhido:** Thompson Sampling (Beta-Bernoulli, contextual), comparado contra dois baselines determinísticos. Justificativa completa e resultados no notebook da Etapa 3.

**Resultado principal:** o agente adaptativo supera tanto o baseline legado ("sempre telephone", +6,5% relativo) quanto o baseline forte ("sempre o melhor braço histórico", +0,6% relativo), capturando valor extra ao identificar que, no segmento de clientes que já converteram antes, `telephone` performa ligeiramente melhor que `cellular`.

## Estrutura do repositório

```
datathon-7mlet-grupo-XX/
├── README.md                                  <- este arquivo
├── requirements.txt                            <- dependências do projeto (notebooks)
├── bank-full.csv                                <- base bruta (Kaggle/UCI Bank Marketing)
├── bank_treated.csv                             <- base tratada, gerada na Etapa 1
├── 01_eda_bank_marketing.ipynb                  <- Etapa 1: EDA e tratamento de dados
├── 02_03_baseline_thompson_sampling.ipynb       <- Etapas 2 e 3: preparação da base, baseline e Thompson Sampling
├── etapa3_results.json                          <- artefato do modelo treinado (parâmetros e métricas)
├── 04_avaliacao_golden_set.ipynb                <- Etapa 4: métricas de avaliação e Golden Set (5 casos de teste)
├── golden_set_resultado.csv                     <- saída do Golden Set
├── 07_mlflow_tracking.ipynb                     <- Etapa 7: registro de parâmetros/métricas no MLflow
├── mlflow.db                                     <- banco SQLite do MLflow (gerado ao rodar o notebook 07)
├── comparacao_politicas.png                      <- artefato gráfico registrado no MLflow
└── api/                                         <- Etapa 5: serviço demonstrável (API FastAPI)
    ├── app.py
    ├── model.py
    ├── test_api.py
    ├── requirements.txt
    ├── README.md
    └── etapa3_results.json
```

## Base de dados

- **Fonte:** [Bank Marketing Dataset — henriqueyamahata (Kaggle)](https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing), originalmente do UCI Machine Learning Repository (Moro, Cortez & Rita, 2014).
- **Arquivo usado:** `bank-full.csv` (45.211 linhas, 17 colunas).
- **Target (proxy de conversão):** coluna `y`.
- **Coluna removida por vazamento temporal:** `duration` (só é conhecida depois que a ligação já aconteceu).

> **Antes de rodar:** baixe o `bank-full.csv` diretamente do link do Kaggle acima e coloque na raiz do projeto. O arquivo que acompanha este repositório foi obtido de um mirror público com conteúdo idêntico, por limitação de acesso do ambiente de desenvolvimento usado para gerar os notebooks.

## Como executar

### 1. Pré-requisitos

- Python 3.10+ instalado (`python3 --version` no terminal para conferir).
- Recomendado usar um ambiente virtual, para não misturar dependências com o Python do sistema:

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Rodar os notebooks (nesta ordem)

```bash
jupyter notebook
```

1. `01_eda_bank_marketing.ipynb` — carrega `bank-full.csv`, faz EDA e tratamento, gera `bank_treated.csv`.
2. `02_03_baseline_thompson_sampling.ipynb` — usa `bank_treated.csv`, treina o Thompson Sampling, compara com os baselines, gera `etapa3_results.json`.
3. `04_avaliacao_golden_set.ipynb` — usa `etapa3_results.json`, consolida métricas e roda o Golden Set, gera `golden_set_resultado.csv`.

Cada notebook depende do arquivo gerado pelo anterior — rodar fora de ordem vai dar erro de arquivo não encontrado.

### 4. Rodar a API (Etapa 5)

```bash
cd api
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Acesse a documentação interativa em **http://localhost:8000/docs** para testar o endpoint `/recomendar` diretamente pelo navegador.

Para rodar os testes automatizados (confere se as recomendações da API batem com o Golden Set da Etapa 4):

```bash
python test_api.py
```

Instruções detalhadas da API em [`api/README.md`](api/README.md).

## Arquitetura-alvo em nuvem

Para colocar este projeto no ar, usaríamos a **AWS**, separando o pipeline em dois fluxos independentes. No **treino (offline)**, os dados brutos ficam versionados no **S3**, o pré-processamento e o treino do bandit rodam em notebooks/jobs do **SageMaker**, os experimentos (parâmetros e métricas) são registrados no **MLflow** — a mesma ferramenta usada localmente na Etapa 7, hospedada em uma instância gerenciada ou em um pequeno servidor dedicado — e o artefato final do modelo (`etapa3_results.json`) é salvo de volta no S3, versionado por data/execução.

No **serviço (online)**, a API FastAPI da Etapa 5 seria empacotada em um container Docker e publicada no **ECS Fargate** (sem gerenciar servidores), exposta por um **API Gateway** que cuida de autenticação, throttling e roteamento das chamadas dos canais digitais até o serviço. A cada nova recomendação servida, logs e métricas de negócio (taxa de conversão, latência, distribuição de braços escolhidos) vão para o **CloudWatch**, permitindo alertar sobre degradação do modelo ou picos de erro. Esse desenho separa claramente o ciclo de "aprender" do ciclo de "servir", permitindo re-treinar e publicar novas versões do modelo sem tirar o serviço do ar.

## Ciclo de vida MLOps

O tracking de experimentos é feito com **MLflow**, rodando localmente com backend SQLite (`mlflow.db`) — sem depender de nenhum servidor externo. O notebook `07_mlflow_tracking.ipynb` registra, em uma run nomeada (`thompson_sampling_contextual_v1`), tudo que descreve o experimento da Etapa 3:

- **Parâmetros:** algoritmo, braços, variável de contexto, priors (`alpha=1, beta=1`), melhor braço histórico, política final aprendida, estratégia de split e de avaliação.
- **Métricas:** taxas de conversão de cada política (baseline legado, baseline forte, Thompson Sampling), ganhos em pontos percentuais e relativos, e os parâmetros posteriores finais (α, β) de cada par contexto/braço.
- **Artefatos:** o `etapa3_results.json` completo e um gráfico comparativo das políticas.

Para rodar o notebook e depois explorar os resultados na interface visual do MLflow:

```bash
jupyter notebook 07_mlflow_tracking.ipynb   # roda a run e grava em mlflow.db
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Acesse **http://localhost:5000** (pode levar ~10-15s para a interface ficar disponível após o comando).

## Limitações conhecidas

- O contexto do bandit é simplificado (binário, baseado só em `poutcome`); a EDA da Etapa 1 identificou outros sinais de contexto (ex.: profissão) que poderiam enriquecer uma versão futura com um bandit contextual mais robusto.
- A avaliação é feita de forma offline (dados logados/históricos), com estimador estratificado para reduzir viés; o ideal é validar o ganho real com um piloto controlado antes de um rollout completo.
- Este projeto usa apenas dados públicos do Kaggle como proxy factual — nenhum dado real de clientes, identificador, renda ou regra comercial privada foi utilizado.

## Autores

Camilly Alves — Pós Tech em Machine Learning Engineering (FIAP)
