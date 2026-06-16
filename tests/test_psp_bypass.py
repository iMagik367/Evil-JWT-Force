import pytest
from utils.psp_bypass import simulate_psp_response


def test_psp_response_success():
    status, response = simulate_psp_response(
        jwt_token="jwt123",
        endpoint="https://d333bet.com/pix/confirm",
        valor=99.99,
        txid="TXIDTEST123",
        recebedor="EVIL LTDA"
    )
    assert status in [200, 201], f"Unexpected status code: {status}, response: {response}" 