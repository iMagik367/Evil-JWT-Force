import pytest
from unittest.mock import patch, MagicMock
import sys
import io

# Supondo que o módulo wordlist_engine está em utils.wordlist_engine
from utils import wordlist_engine

@pytest.fixture
def base_words():
    return ["admin", "senha", "123456", "root"]

@pytest.fixture
def rules():
    return {
        "prefix": ["!", "#"],
        "suffix": ["2024", "@"],
        "capitalize": True,
        "leet": True
    }

def test_engine_generate_variants(base_words, rules):
    wordlist = wordlist_engine.generate_variants(base_words, rules)
    assert isinstance(wordlist, list)
    assert any(w.startswith("!") or w.startswith("#") for w in wordlist)
    assert any(w.endswith("2024") or w.endswith("@") for w in wordlist)
    assert any(w[0].isupper() for w in wordlist)
    assert any("@" in w or "4" in w for w in wordlist)  # leet

def test_engine_filter_duplicates():
    words = ["admin", "Admin", "admin", "ADMIN"]
    filtered = wordlist_engine.filter_duplicates(words)
    assert len(filtered) < len(words)
    assert "admin" in filtered or "Admin" in filtered

def test_engine_apply_custom_rules(base_words):
    custom_rules = {"reverse": True}
    wordlist = wordlist_engine.generate_variants(base_words, custom_rules)
    assert any(w[::-1] in base_words for w in wordlist)

def test_engine_save_and_load(tmp_path, base_words, rules):
    wordlist = wordlist_engine.generate_variants(base_words, rules)
    file_path = tmp_path / "engine_wordlist.txt"
    wordlist_engine.save_wordlist(wordlist, str(file_path))
    loaded = wordlist_engine.load_wordlist(str(file_path))
    assert set(wordlist) == set(loaded)

def test_engine_large_input_performance():
    base = [f"user{i}" for i in range(1000)]
    wordlist = wordlist_engine.generate_variants(base, {"capitalize": True})
    assert len(wordlist) > 1000

def test_engine_cli(monkeypatch, tmp_path):
    args = ["prog", "wordlist-engine", "--base", "admin,root", "--output", str(tmp_path / "out.txt"), "--rules", "capitalize,leet"]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("utils.wordlist_engine.generate_variants", MagicMock(return_value=["admin", "root", "Adm1n"]))
    monkeypatch.setattr("utils.wordlist_engine.save_wordlist", MagicMock(return_value=True))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        wordlist_engine.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "Wordlist gerada" in output or "admin" in output

def test_engine_error_handling(tmp_path):
    with patch("builtins.open", side_effect=PermissionError("Simulado")):
        with pytest.raises(PermissionError):
            wordlist_engine.save_wordlist(["admin"], str(tmp_path / "fail.txt"))

def test_engine_empty_base():
    wordlist = wordlist_engine.generate_variants([])
    assert wordlist == []

def test_engine_integration_with_wordlist_generator(monkeypatch, base_words):
    monkeypatch.setattr("utils.wordlist_generator.generate_wordlist", MagicMock(return_value=base_words))
    generated = wordlist_engine.generate_variants(base_words, {"capitalize": True})
    assert any(w[0].isupper() for w in generated)

if __name__ == "__main__":
    pytest.main()