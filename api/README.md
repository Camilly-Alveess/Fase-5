# Etapa 5 — Serviço de Recomendação de Canal

API FastAPI que recebe os dados de um cliente e retorna qual canal de
contato (`cellular` ou `telephone`) o modelo de Thompson Sampling (Etapa 3)
recomenda, junto com a taxa de conversão esperada.

## Arquivos

- `model.py` — carrega os parâmetros do bandit treinado (`etapa3_results.json`) e gera recomendações.
- `app.py` — API FastAPI (`/health` e `/recomendar`).
- `test_api.py` — script que sobe a API e testa os 5 casos do Golden Set (Etapa 4).
- `etapa3_results.json` — artefato do modelo treinado na Etapa 3 (copiar aqui após re-treinar, se necessário).

## Como rodar

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Documentação interativa (Swagger UI): http://localhost:8000/docs

## Exemplo de requisição

```bash
curl -X POST http://localhost:8000/recomendar \
  -H "Content-Type: application/json" \
  -d '{
    "age": 32,
    "job": "admin.",
    "marital": "married",
    "education": "secondary",
    "balance": 1229,
    "housing": "no",
    "loan": "no",
    "campaign": 1,
    "previous": 1,
    "poutcome": "success"
  }'
```

Resposta esperada:

```json
{
  "oferta_recomendada": "telephone",
  "conversao_esperada": 0.7273,
  "contexto_utilizado": "converteu antes",
  "medias_por_braco": {"cellular": 0.6733, "telephone": 0.7273}
}
```

## Testes

```bash
python test_api.py
```

Sobe a API automaticamente, roda os 5 casos do Golden Set e confere se as
recomendações batem com o notebook da Etapa 4.
