"""
Script simples de teste da API da Etapa 5.
Sobe a API automaticamente (via subprocess), roda os 5 casos do Golden Set
contra o endpoint /recomendar e confere se as respostas batem com o que
foi obtido no notebook da Etapa 4.

Uso:
    python test_api.py
"""
import subprocess
import time
import sys

import requests

BASE_URL = "http://localhost:8000"

GOLDEN_SET_REQUESTS = [
    {
        "nome": "Cliente 1 - converteu antes",
        "payload": {
            "age": 32, "job": "admin.", "marital": "married", "education": "secondary",
            "balance": 1229, "housing": "no", "loan": "no",
            "campaign": 1, "previous": 1, "poutcome": "success",
        },
        "esperado": "telephone",
    },
    {
        "nome": "Cliente 2 - estudante, primeiro contato",
        "payload": {
            "age": 19, "job": "student", "marital": "single", "education": "secondary",
            "balance": 1803, "housing": "no", "loan": "no",
            "campaign": 1, "previous": 0, "poutcome": "unknown",
        },
        "esperado": "cellular",
    },
    {
        "nome": "Cliente 3 - aposentado, campanha anterior falhou",
        "payload": {
            "age": 66, "job": "retired", "marital": "married", "education": "secondary",
            "balance": 154, "housing": "no", "loan": "no",
            "campaign": 5, "previous": 2, "poutcome": "failure",
        },
        "esperado": "cellular",
    },
    {
        "nome": "Cliente 4 - financiamento e empréstimo ativos",
        "payload": {
            "age": 47, "job": "services", "marital": "married", "education": "secondary",
            "balance": -98, "housing": "yes", "loan": "yes",
            "campaign": 1, "previous": 0, "poutcome": "unknown",
        },
        "esperado": "cellular",
    },
    {
        "nome": "Cliente 5 - jovem, converteu antes",
        "payload": {
            "age": 25, "job": "blue-collar", "marital": "single", "education": "secondary",
            "balance": 303, "housing": "no", "loan": "no",
            "campaign": 1, "previous": 1, "poutcome": "success",
        },
        "esperado": "telephone",
    },
]


def main():
    print("Subindo a API em background...")
    proc = subprocess.Popen(
        ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(3)

        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200, "Health check falhou"
        print(f"Health check OK: {r.json()}\n")

        all_ok = True
        for case in GOLDEN_SET_REQUESTS:
            r = requests.post(f"{BASE_URL}/recomendar", json=case["payload"], timeout=5)
            r.raise_for_status()
            data = r.json()
            ok = data["oferta_recomendada"] == case["esperado"]
            all_ok &= ok
            status = "OK" if ok else "DIVERGIU"
            print(f"[{status}] {case['nome']}: recomendado={data['oferta_recomendada']} "
                  f"(esperado={case['esperado']}) | conversão esperada={data['conversao_esperada']}")

        print("\nTodos os casos bateram com o Golden Set." if all_ok else "\nAtenção: alguma recomendação divergiu do esperado.")
        sys.exit(0 if all_ok else 1)
    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    main()
