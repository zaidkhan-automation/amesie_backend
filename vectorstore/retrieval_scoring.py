import math

def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def compute_score(
    *,
    similarity: float,
    r_raw: float,
    p_raw: float,
    alpha: float = 0.6,
    gamma: float = 0.3,
    beta: float = 0.9,
) -> float:
    """
    similarity: cosine similarity (0..1)
    r_raw, p_raw: unbounded raw values
    """
    R = sigmoid(r_raw)
    P = sigmoid(p_raw)

    return alpha * similarity + gamma * R - beta * P
