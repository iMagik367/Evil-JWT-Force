from typing import Dict, List, Tuple
import numpy as np
from sklearn.metrics import f1_score, roc_auc_score, precision_score, recall_score

def compute_metrics(y_true: List[int], y_pred: List[int], y_pred_proba: List[float]) -> Dict[str, float]:
    """Calcula várias métricas de avaliação."""
    metrics = {
        'f1': f1_score(y_true, y_pred),
        'roc_auc': roc_auc_score(y_true, y_pred_proba),
        'precision': precision_score(y_true, y_pred),
        'recall': recall_score(y_true, y_pred),
        'accuracy': np.mean(np.array(y_true) == np.array(y_pred))
    }
    return metrics

def format_metrics(metrics: Dict[str, float]) -> str:
    """Formata as métricas em uma string legível."""
    return "\n".join([f"{k}: {v:.4f}" for k, v in metrics.items()])
