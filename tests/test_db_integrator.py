import unittest
import os
from modules import db_integrator
import json

class TestDBIntegrator(unittest.TestCase):
    def test_search_cnpj_receitaws(self):
        result = db_integrator.search_cnpj_receitaws("00000000000191")  # CNPJ de teste
        self.assertIsInstance(result, dict)

    def test_query_brasilapi_cpf(self):
        result = db_integrator.query_brasilapi_cpf("00000000191")  # CPF de teste
        self.assertIsInstance(result, dict)

    def test_fetch_data_bacen_json(self):
        # Ensure API file exists
        os.makedirs('APIs', exist_ok=True)
        with open('APIs/camara_deputados_2025.json', 'w', encoding='utf-8') as f:
            f.write('[]')
        data = db_integrator.fetch_data_bacen_json("camara_deputados_2025.json")
        self.assertIsInstance(data, list)

    def test_search_camara_deputados(self):
        # Setup sample data
        sample = [{"name": "Maria"}, {"name": "João"}]
        with open('APIs/camara_deputados_2025.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(sample))
        results = db_integrator.search_camara_deputados("Maria")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)

    def test_query_census(self):
        result = db_integrator.query_census("New York")
        self.assertTrue(isinstance(result, dict) or isinstance(result, list))

    def test_check_phone_veriphone(self):
        result = db_integrator.check_phone_veriphone("+5511999999999")
        self.assertIsInstance(result, dict)

    def test_check_leaks_hibp(self):
        result = db_integrator.check_leaks_hibp("test@example.com")
        self.assertTrue(isinstance(result, list) or isinstance(result, dict))

    def test_scrape_integration_hri_fi(self):
        with open('APIs/hri_fi_integration.json', 'w', encoding='utf-8') as f:
            f.write('[]')
        results = db_integrator.scrape_integration_hri_fi("test")
        self.assertIsInstance(results, list)

    def test_get_kijang_bank_data(self):
        with open('APIs/kijang_bnm_api.json', 'w', encoding='utf-8') as f:
            f.write('[]')
        results = db_integrator.get_kijang_bank_data("test")
        self.assertIsInstance(results, list)

    def test_explore_data_gov_tw(self):
        with open('APIs/data_gov_tw_datasets.json', 'w', encoding='utf-8') as f:
            f.write('[]')
        results = db_integrator.explore_data_gov_tw("test")
        self.assertIsInstance(results, list)

if __name__ == '__main__':
    unittest.main() 