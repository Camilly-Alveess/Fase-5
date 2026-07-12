"""
Etapa 5 — Serviço demonstrável (API)

Sobe uma API FastAPI que recebe os dados de um cliente e retorna qual
canal de contato (braço do bandit) deve ser usado, junto com a taxa
de conversão esperada segundo o modelo treinado na Etapa 3.

Rodar localmente:
    uvicorn app:app --reload --port 8000

Doc interativa (Swagger):
    http://localhost:8000/docs
"""
from enum import Enum
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from model import load_model, build_context

app = FastAPI(
    title="Datathon 7MLET — Recomendador de Canal (Bandit Adaptativo)",
    description=(
        "Serviço que decide, por cliente, qual canal de contato (cellular ou "
        "telephone) tende a gerar maior taxa de conversão, usando um agente "
        "de Thompson Sampling treinado sobre a base Bank Marketing."
    ),
    version="1.0.0",
)

model = load_model()


class PoutcomeEnum(str, Enum):
    success = "success"
    failure = "failure"
    other = "other"
    unknown = "unknown"


class ClienteRequest(BaseModel):
    age: int = Field(..., ge=18, le=100, description="Idade do cliente")
    job: str = Field(..., description="Profissão do cliente")
    marital: str = Field(..., description="Estado civil")
    education: str = Field(..., description="Nível de educação")
    balance: int = Field(..., description="Saldo médio anual (euros)")
    housing: Literal["yes", "no"] = Field(..., description="Possui financiamento imobiliário?")
    loan: Literal["yes", "no"] = Field(..., description="Possui empréstimo pessoal?")
    campaign: int = Field(1, ge=1, description="Nº de contatos nesta campanha")
    previous: int = Field(0, ge=0, description="Nº de contatos antes desta campanha")
    poutcome: PoutcomeEnum = Field(..., description="Resultado da campanha anterior")

    class Config:
        json_schema_extra = {
            "example": {
                "age": 32,
                "job": "admin.",
                "marital": "married",
                "education": "secondary",
                "balance": 1229,
                "housing": "no",
                "loan": "no",
                "campaign": 1,
                "previous": 1,
                "poutcome": "success",
            }
        }


class RecomendacaoResponse(BaseModel):
    oferta_recomendada: str
    conversao_esperada: float
    contexto_utilizado: str
    medias_por_braco: dict


@app.get("/health")
def health():
    return {"status": "ok", "modelo_carregado": True, "braços": model.arms}


@app.post("/recomendar", response_model=RecomendacaoResponse)
def recomendar(cliente: ClienteRequest):
    try:
        context = build_context(cliente.poutcome.value)
        arm, means = model.recommend(context)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar recomendação: {exc}")

    return RecomendacaoResponse(
        oferta_recomendada=arm,
        conversao_esperada=round(means[arm], 4),
        contexto_utilizado="converteu antes" if context == 1 else "não converteu antes",
        medias_por_braco={k: round(v, 4) for k, v in means.items()},
    )
