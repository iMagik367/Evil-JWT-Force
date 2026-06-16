import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import os
import json
from datetime import datetime
from loguru import logger

# Configuração de logs
logger.add("ai_system/logs/analysis_log_{time}.log", rotation="500 MB", level="INFO")
logger.add("ai_system/logs/analysis_error_{time}.log", rotation="500 MB", level="ERROR")

# Caminhos para dados
METRICS_PATH = "ai_system/data/metrics.csv"
ERRORS_PATH = "ai_system/data/errors.csv"
MODEL_PATH = "ai_system/analysis/error_predictor_model.pkl"

# Cria diretórios se não existirem
os.makedirs("ai_system/logs", exist_ok=True)
os.makedirs("ai_system/analysis", exist_ok=True)

# Função para carregar dados de métricas
def load_metrics():
    if not os.path.exists(METRICS_PATH):
        logger.error(f"Arquivo de métricas não encontrado em {METRICS_PATH}")
        return None
    try:
        df = pd.read_csv(METRICS_PATH)
        logger.info(f"Dados de métricas carregados com {len(df)} registros.")
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar métricas: {str(e)}")
        return None

# Função para carregar dados de erros
def load_errors():
    if not os.path.exists(ERRORS_PATH):
        logger.error(f"Arquivo de erros não encontrado em {ERRORS_PATH}")
        return None
    try:
        df = pd.read_csv(ERRORS_PATH)
        logger.info(f"Dados de erros carregados com {len(df)} registros.")
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar dados de erros: {str(e)}")
        return None

# Função para treinar modelo de previsão de erros
def train_error_predictor():
    metrics_df = load_metrics()
    errors_df = load_errors()
    
    if metrics_df is None or errors_df is None:
        logger.error("Não foi possível treinar o modelo devido à falta de dados.")
        return False
    
    # Preparar dados para treinamento (exemplo simplificado)
    # Aqui, associamos métricas a erros para prever falhas
    logger.info("Preparando dados para treinamento...")
    # Criar um dataset combinado (simulação: associar alta CPU a erros)
    metrics_df['Timestamp'] = pd.to_datetime(metrics_df['Timestamp'])
    errors_df['Timestamp'] = pd.to_datetime(errors_df['Timestamp'])
    
    # Juntar dados de métricas e erros por timestamp aproximado
    combined_df = pd.merge_asof(
        metrics_df.sort_values('Timestamp'),
        errors_df.sort_values('Timestamp'),
        on='Timestamp',
        tolerance=pd.Timedelta('1 minute'),
        direction='nearest'
    )
    
    # Criar variável alvo: 1 se houve erro, 0 se não
    combined_df['HasError'] = combined_df['ErrorType'].notna().astype(int)
    
    # Features para o modelo
    features = ['CPU_Percent', 'Memory_Usage_MB']
    X = combined_df[features].fillna(0)
    y = combined_df['HasError']
    
    if len(X) < 2:
        logger.error("Dados insuficientes para treinar o modelo.")
        return False
    
    # Dividir dados em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    # Treinar modelo
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Avaliar modelo
    predictions = model.predict(X_test)
    logger.info("Resultados do treinamento do modelo:")
    logger.info(classification_report(y_test, predictions))
    
    # Salvar modelo (requer joblib)
    try:
        import joblib
        joblib.dump(model, MODEL_PATH)
        logger.info(f"Modelo salvo em {MODEL_PATH}")
    except Exception as e:
        logger.error(f"Erro ao salvar modelo: {str(e)}")
    
    return True

# Função para prever erros com base em métricas atuais
def predict_errors(current_metrics=None):
    if not os.path.exists(MODEL_PATH):
        logger.error("Modelo de previsão não encontrado. Treine o modelo primeiro.")
        return None
    
    try:
        import joblib
        model = joblib.load(MODEL_PATH)
        if current_metrics is None:
            metrics_df = load_metrics()
            if metrics_df is None or len(metrics_df) == 0:
                return None
            current_metrics = metrics_df.tail(1)[['CPU_Percent', 'Memory_Usage_MB']].fillna(0)
        
        prediction = model.predict(current_metrics)
        probability = model.predict_proba(current_metrics)
        logger.info(f"Previsão de erro: {prediction}, Probabilidade: {probability}")
        return {
            'prediction': int(prediction[0]),
            'probability': probability[0].tolist()
        }
    except Exception as e:
        logger.error(f"Erro ao prever erros: {str(e)}")
        return None

if __name__ == "__main__":
    logger.info("Iniciando análise de dados para previsão de erros...")
    trained = train_error_predictor()
    if trained:
        prediction = predict_errors()
        if prediction:
            print(f"[PREVISÃO] Probabilidade de erro: {prediction['probability']}")
            if prediction['prediction'] == 1:
                print("[ALERTA] Um erro é provável. Verifique o sistema.")
    logger.info("Análise concluída.") 