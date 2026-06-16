import numpy as np
import torch
from sklearn.model_selection import KFold
from sklearn.metrics import f1_score, roc_auc_score
from torch.optim.lr_scheduler import ReduceLROnPlateau
from tqdm import tqdm
from typing import Dict, List, Tuple

from model_trainer import JWTModelTrainer, TrainingConfig

class EnhancedJWTModelTrainer(JWTModelTrainer):
    def __init__(self, config: TrainingConfig):
        super().__init__(config)
        self.scheduler = None
        self.best_metrics = {'f1': 0.0, 'roc_auc': 0.0, 'loss': float('inf')}
        self.early_stopping_counter = 0
        self.patience = 5

    def train_with_cross_validation(self, train_loader: DataLoader, val_loader: DataLoader, k_folds: int = 5) -> Dict:
        metrics_history = {'train_loss': [], 'val_loss': [], 'f1': [], 'roc_auc': []}
        kfold = KFold(n_splits=k_folds, shuffle=True)

        X = []
        y = []
        for batch in train_loader:
            X.extend(batch[0])
            y.extend(batch[1])

        for fold, (train_idx, val_idx) in enumerate(kfold.split(X, y)):
            print(f"\nFold {fold + 1}/{k_folds}")

            train_dataset = JWTDataset(
                [X[i] for i in train_idx],
                [y[i] for i in train_idx]
            )
            val_dataset = JWTDataset(
                [X[i] for i in val_idx],
                [y[i] for i in val_idx]
            )

            self.model = JWTModel(self.config.input_size).to(self.config.device)
            self.optimizer = torch.optim.Adam(
                self.model.parameters(),
                lr=self.config.learning_rate
            )
            self.scheduler = ReduceLROnPlateau(
                self.optimizer,
                mode='min',
                factor=0.1,
                patience=2,
                verbose=True
            )

            fold_metrics = self._train_fold(
                DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True),
                DataLoader(val_dataset, batch_size=self.config.batch_size),
                fold
            )

            for key, value in fold_metrics.items():
                metrics_history[key].append(value)

        avg_metrics = {k: np.mean(v) for k, v in metrics_history.items()}
        return avg_metrics

    def _train_fold(self, train_loader: DataLoader, val_loader: DataLoader, fold: int) -> Dict:
        for epoch in range(self.config.epochs):
            train_loss = self._train_epoch(train_loader)
            val_metrics = self._validate(val_loader)

            self.scheduler.step(val_metrics['loss'])

            if val_metrics['loss'] < self.best_metrics['loss']:
                self.best_metrics = val_metrics
                self.early_stopping_counter = 0
                self._save_model(f"jwt_analyzer_fold_{fold}.pt")
            else:
                self.early_stopping_counter += 1

            if self.early_stopping_counter >= self.patience:
                print(f"Early stopping at epoch {epoch + 1}")
                break

            print(f"Epoch {epoch + 1}/{self.config.epochs}")
            print(f"Train Loss: {train_loss:.4f}")
            print(f"Val Loss: {val_metrics['loss']:.4f}")
            print(f"Val F1: {val_metrics['f1']:.4f}")
            print(f"Val ROC-AUC: {val_metrics['roc_auc']:.4f}")

        return val_metrics

    def _train_epoch(self, train_loader: DataLoader) -> float:
        self.model.train()
        total_loss = 0

        for batch in tqdm(train_loader, desc="Training"):
            inputs, labels = batch
            inputs = inputs.to(self.config.device)
            labels = labels.to(self.config.device)

            self.optimizer.zero_grad()
            outputs = self.model(inputs)
            loss = self.criterion(outputs, labels)
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

        return total_loss / len(train_loader)

    def _validate(self, val_loader: DataLoader) -> Dict:
        self.model.eval()
        all_preds = []
        all_labels = []
        total_loss = 0

        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validation"):
                inputs, labels = batch
                inputs = inputs.to(self.config.device)
                labels = labels.to(self.config.device)

                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)
                total_loss += loss.item()

                preds = torch.round(outputs)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        metrics = {
            'loss': total_loss / len(val_loader),
            'f1': f1_score(all_labels, all_preds),
            'roc_auc': roc_auc_score(all_labels, all_preds)
        }

        return metrics
