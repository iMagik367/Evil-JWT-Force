#!/usr/bin/env python3
"""
Testes para o módulo JWT Decryptor
"""

import os
import sys
import unittest
import json
from pathlib import Path

# Adiciona o diretório raiz ao sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.jwt_decryptor import JWTDecryptor

class TestJWTDecryptor(unittest.TestCase):
    """
    Testes unitários para o módulo JWT Decryptor
    """
    
    def setUp(self):
        """
        Configuração inicial para os testes
        """
        # Token de teste (HS256, chave: "secret")
        self.test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3RlIEpXVCBEZWNyeXB0b3IiLCJpYXQiOjE1MTYyMzkwMjJ9.iFVUdFGzrDhx2RqblgxJY3lpJJAdYPIVKScQL-T7kPQ"
        
        # Token expirado (expirou em 2020)
        self.expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1ODAwMDAwMDB9.JRkA4UBs3GCmNDLiLLjDmI-ptYQB0oEgEwgbzOq6yLw"
        
        # Token com privilégios admin
        self.admin_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkFkbWluIFVzZXIiLCJpYXQiOjE1MTYyMzkwMjIsImFkbWluIjp0cnVlfQ.KPq63-K9jVcTtUYwJ0vpwG-F_9CmGXwYFVgBgKm_Jj4"
        
        # Token com campo 'kid'
        self.kid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtleS0xMjMifQ.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QgVXNlciIsImlhdCI6MTUxNjIzOTAyMn0.QUixfgUjd5xNVQFpNQGh2oXkBtkBdVQ9pcOl-xrq-YA"
        
        # Chave secreta de teste
        self.test_key = "secret"
        
        # Inicializa o decriptador
        self.decryptor = JWTDecryptor(self.test_token)
        
        # Cria diretório de saída para testes se necessário
        self.output_dir = PROJECT_ROOT / "tests" / "output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def test_parse_token(self):
        """
        Testa a função de análise do token
        """
        token_parts = self.decryptor.parse_token()
        
        self.assertIsNotNone(token_parts)
        self.assertIn("header", token_parts)
        self.assertIn("payload", token_parts)
        self.assertIn("signature", token_parts)
        
        # Verifica o conteúdo do header
        self.assertEqual(token_parts["header"]["alg"], "HS256")
        self.assertEqual(token_parts["header"]["typ"], "JWT")
        
        # Verifica o conteúdo do payload
        self.assertEqual(token_parts["payload"]["sub"], "1234567890")
        self.assertEqual(token_parts["payload"]["name"], "Teste JWT Decryptor")
    
    def test_decrypt_with_key(self):
        """
        Testa a descriptografia com a chave correta
        """
        result = self.decryptor.decrypt_with_key(self.test_key)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["algorithm"], "HS256")
        self.assertEqual(result["key"], self.test_key)
        self.assertIn("decoded", result)
        self.assertEqual(result["decoded"]["name"], "Teste JWT Decryptor")
    
    def test_decrypt_with_wrong_key(self):
        """
        Testa a descriptografia com uma chave incorreta
        """
        result = self.decryptor.decrypt_with_key("wrong_key")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["key"], "wrong_key")
    
    def test_brute_force(self):
        """
        Testa o ataque de força bruta
        """
        # Cria uma lista de palavras que inclui a chave correta
        wordlist = ["test", "password", "key", self.test_key, "admin"]
        
        result = self.decryptor.brute_force(wordlist)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["key"], self.test_key)
        self.assertEqual(result["algorithm"], "HS256")
        self.assertEqual(result["attempts"], 4)  # A chave está na posição 4 (índice 3)
    
    def test_none_algorithm(self):
        """
        Testa a vulnerabilidade de algoritmo 'none'
        """
        result = self.decryptor.test_none_algorithm()
        
        # O resultado depende da biblioteca JWT e sua configuração de segurança
        # Normalmente, bibliotecas modernas não são vulneráveis
        self.assertIn("vulnerability", result)
        self.assertEqual(result["vulnerability"], "none_algorithm")
    
    def test_check_vulnerabilities_expired(self):
        """
        Testa a verificação de vulnerabilidades em token expirado
        """
        decryptor = JWTDecryptor(self.expired_token)
        vulnerabilities = decryptor.check_common_vulnerabilities()
        
        # Deve encontrar pelo menos a vulnerabilidade de expiração
        self.assertGreater(len(vulnerabilities), 0)
        
        # Verifica se a vulnerabilidade de expiração foi encontrada
        expired_vuln = next((v for v in vulnerabilities if v.get("type") == "expired_token"), None)
        self.assertIsNotNone(expired_vuln)
    
    def test_check_vulnerabilities_admin(self):
        """
        Testa a verificação de vulnerabilidades em token com privilégios admin
        """
        decryptor = JWTDecryptor(self.admin_token)
        vulnerabilities = decryptor.check_common_vulnerabilities()
        
        # Verifica se a vulnerabilidade de privilégios admin foi encontrada
        admin_vuln = next((v for v in vulnerabilities if v.get("type") == "admin_privileges"), None)
        self.assertIsNotNone(admin_vuln)
    
    def test_check_vulnerabilities_kid(self):
        """
        Testa a verificação de vulnerabilidades em token com campo 'kid'
        """
        decryptor = JWTDecryptor(self.kid_token)
        vulnerabilities = decryptor.check_common_vulnerabilities()
        
        # Verifica se a vulnerabilidade de campo 'kid' foi encontrada
        kid_vuln = next((v for v in vulnerabilities if v.get("type") == "kid_parameter"), None)
        self.assertIsNotNone(kid_vuln)
        self.assertEqual(kid_vuln["kid_value"], "key-123")
    
    def test_analyze_token(self):
        """
        Testa a análise completa do token
        """
        analysis = self.decryptor.analyze_token()
        
        self.assertTrue(analysis["success"])
        self.assertEqual(analysis["token"], self.test_token)
        self.assertIn("token_parts", analysis)
        self.assertIn("vulnerabilities", analysis)
        self.assertIn("timestamp", analysis)
    
    def test_save_results(self):
        """
        Testa a função de salvar resultados
        """
        output_file = self.output_dir / "test_results.json"
        success = self.decryptor.save_results(str(output_file))
        
        self.assertTrue(success)
        self.assertTrue(output_file.exists())
        
        # Verifica se o arquivo contém um JSON válido
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn("token", data)
        self.assertIn("token_parts", data)
        self.assertIn("vulnerabilities", data)

if __name__ == "__main__":
    unittest.main() 