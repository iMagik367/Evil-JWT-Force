import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

@dataclass
class TrainingConfig:
    """Configuração para treinamento do modelo."""
    batch_size: int = 32
    learning_rate: float = 0.001
    epochs: int = 10
    train_split: float = 0.8
    validation_split: float = 0.1
    test_split: float = 0.1
    model_save_path: str = "models/jwt_analyzer.pt"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"

class JWTDataset(Dataset):
    """Dataset para tokens JWT."""
    
    def __init__(self, tokens: List[str], labels: List[int]):
        self.tokens = tokens
        self.labels = labels
        
    def __len__(self):
        return len(self.tokens)
    
    def __getitem__(self, idx):
        return self.tokens[idx], self.labels[idx]

class JWTModel(nn.Module):
    """Modelo de IA para análise de tokens JWT."""
    
    def __init__(self, input_size: int, hidden_size: int = 128):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        x = self.encoder(x)
        return self.classifier(x)

class JWTModelTrainer:
    """Treinador do modelo de análise de JWT."""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.optimizer = None
        self.criterion = nn.BCELoss()
        
    def prepare_data(self, data_file: str) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """Prepara os dados para treinamento."""
        try:
            # Carrega os dados
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            # Extrai tokens e labels
            tokens = [self._token_to_features(sample) for sample in data]
            labels = [1 if sample['is_vulnerable'] else 0 for sample in data]
            
            # Divide os dados
            X_train, X_temp, y_train, y_temp = train_test_split(
                tokens, labels, 
                test_size=(1 - self.config.train_split),
                random_state=42
            )
            
            X_val, X_test, y_val, y_test = train_test_split(
                X_temp, y_temp,
                test_size=self.config.test_split / (self.config.test_split + self.config.validation_split),
                random_state=42
            )
            
            # Cria datasets
            train_dataset = JWTDataset(X_train, y_train)
            val_dataset = JWTDataset(X_val, y_val)
            test_dataset = JWTDataset(X_test, y_test)
            
            # Cria dataloaders
            train_loader = DataLoader(
                train_dataset, 
                batch_size=self.config.batch_size,
                shuffle=True
            )
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.config.batch_size
            )
            test_loader = DataLoader(
                test_dataset,
                batch_size=self.config.batch_size
            )
            
            return train_loader, val_loader, test_loader
            
        except Exception as e:
            self.logger.error(f"Erro ao preparar dados: {e}")
            raise
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader):
        """Treina o modelo."""
        try:
            # Inicializa o modelo
            input_size = len(train_loader.dataset[0][0])
            self.model = JWTModel(input_size).to(self.config.device)
            self.optimizer = torch.optim.Adam(
                self.model.parameters(),
                lr=self.config.learning_rate
            )
            
            # Loop de treinamento
            best_val_loss = float('inf')
            for epoch in range(self.config.epochs):
                # Treinamento
                self.model.train()
                train_loss = 0
                for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{self.config.epochs}"):
                    tokens, labels = batch
                    tokens = tokens.to(self.config.device)
                    labels = labels.to(self.config.device)
                    
                    self.optimizer.zero_grad()
                    outputs = self.model(tokens)
                    loss = self.criterion(outputs, labels.float().unsqueeze(1))
                    loss.backward()
                    self.optimizer.step()
                    
                    train_loss += loss.item()
                
                # Validação
                val_loss = self._validate(val_loader)
                
                # Log
                self.logger.info(
                    f"Epoch {epoch+1}/{self.config.epochs} - "
                    f"Train Loss: {train_loss/len(train_loader):.4f} - "
                    f"Val Loss: {val_loss:.4f}"
                )
                
                # Salva o melhor modelo
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    self._save_model()
            
        except Exception as e:
            self.logger.error(f"Erro durante o treinamento: {e}")
            raise
    
    def evaluate(self, test_loader: DataLoader) -> Dict:
        """Avalia o modelo no conjunto de teste."""
        try:
            self.model.eval()
            predictions = []
            actual = []
            
            with torch.no_grad():
                for batch in test_loader:
                    tokens, labels = batch
                    tokens = tokens.to(self.config.device)
                    outputs = self.model(tokens)
                    predictions.extend(outputs.cpu().numpy())
                    actual.extend(labels.numpy())
            
            # Calcula métricas
            predictions = np.array(predictions) > 0.5
            actual = np.array(actual)
            
            accuracy = np.mean(predictions == actual)
            precision = np.sum((predictions == 1) & (actual == 1)) / np.sum(predictions == 1)
            recall = np.sum((predictions == 1) & (actual == 1)) / np.sum(actual == 1)
            f1 = 2 * (precision * recall) / (precision + recall)
            
            return {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1
            }
            
        except Exception as e:
            self.logger.error(f"Erro durante a avaliação: {e}")
            raise
    
    def _token_to_features(self, sample: Dict) -> List[float]:
        """Converte um token JWT em features para o modelo."""
        features = []
        
        # Features do header
        header = sample['header']
        features.extend([
            1 if header.get('alg') == 'none' else 0,
            1 if 'kid' in header else 0,
            1 if 'jku' in header else 0,
            1 if 'x5u' in header else 0
        ])
        
        # Features do payload
        payload = sample['payload']
        features.extend([
            1 if 'exp' not in payload else 0,
            1 if payload.get('exp', 0) < datetime.now().timestamp() else 0,
            len(payload) / 10  # Normalizado
        ])
        
        # Features da assinatura
        signature = sample['signature']
        features.append(len(signature) / 100)  # Normalizado
        
        return features
    
    def _validate(self, val_loader: DataLoader) -> float:
        """Valida o modelo."""
        self.model.eval()
        val_loss = 0
        
        with torch.no_grad():
            for batch in val_loader:
                tokens, labels = batch
                tokens = tokens.to(self.config.device)
                labels = labels.to(self.config.device)
                
                outputs = self.model(tokens)
                loss = self.criterion(outputs, labels.float().unsqueeze(1))
                val_loss += loss.item()
        
        return val_loss / len(val_loader)
    
    def _save_model(self):
        """Salva o modelo."""
        try:
            save_path = Path(self.config.model_save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict()
            }, save_path)
            
            self.logger.info(f"Modelo salvo em {save_path}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar modelo: {e}")
            raise 