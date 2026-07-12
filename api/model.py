"""
Camada de modelo do serviço de recomendação de canal.

Carrega os parâmetros do Thompson Sampling treinados na Etapa 3
(etapa3_results.json) e expõe uma função de recomendação para um
cliente individual, usando o mesmo contexto binário (prev_success)
definido nas etapas anteriores.
"""
import json
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "etapa3_results.json")


class ThompsonSamplingBandit:
    def __init__(self, arms, posterior_params):
        self.arms = arms
        self.params = {}
        for key, (alpha, beta_) in posterior_params.items():
            ctx_str, arm = key.split("_", 1)
            self.params[(int(ctx_str), arm)] = [alpha, beta_]

    def _mean(self, context, arm):
        alpha, beta_ = self.params[(context, arm)]
        return alpha / (alpha + beta_)

    def recommend(self, context):
        means = {arm: self._mean(context, arm) for arm in self.arms}
        best_arm = max(means, key=means.get)
        return best_arm, means


def load_model(path: str = MODEL_PATH) -> ThompsonSamplingBandit:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Arquivo de modelo não encontrado em '{path}'. "
            "Copie o 'etapa3_results.json' gerado na Etapa 3 para essa pasta."
        )
    with open(path, "r") as f:
        artifact = json.load(f)
    return ThompsonSamplingBandit(artifact["arms"], artifact["ts_posterior_params"])


def build_context(poutcome: str) -> int:
    """Deriva o contexto binário usado pelo modelo a partir do poutcome do cliente."""
    return 1 if poutcome == "success" else 0
