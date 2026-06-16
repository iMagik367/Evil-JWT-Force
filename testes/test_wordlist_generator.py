import pytest
from unittest.mock import patch, MagicMock
import sys
import io

# Supondo que o módulo wordlist_generator está em utils.wordlist_generator
from core import wordlist_generator

@pytest.fixture
def base_words():
    return ["admin", "senha", "123456", "root"]

def test_generate_basic_wordlist(base_words):
    wordlist = wordlist_generator.generate_wordlist(base_words)
    assert isinstance(wordlist, list)
    assert "admin" in wordlist
    assert "senha" in wordlist

def test_generate_wordlist_with_mutations(base_words):
    wordlist = wordlist_generator.generate_wordlist(base_words, mutations=True)
    assert any(w != "admin" for w in wordlist)
    assert any(w.endswith("123") for w in wordlist) or any(w.isupper() for w in wordlist)

def test_generate_wordlist_with_custom_rules(base_words):
    rules = {"prefix": "!", "suffix": "2024", "capitalize": True}
    wordlist = wordlist_generator.generate_wordlist(base_words, rules=rules)
    assert any(w.startswith("!") for w in wordlist)
    assert any(w.endswith("2024") for w in wordlist)
    assert any(w[0].isupper() for w in wordlist)

def test_save_and_load_wordlist(tmp_path, base_words):
    wordlist = wordlist_generator.generate_wordlist(base_words)
    file_path = tmp_path / "wordlist.txt"
    wordlist_generator.save_wordlist(wordlist, str(file_path))
    loaded = wordlist_generator.load_wordlist(str(file_path))
    assert set(wordlist) == set(loaded)

def test_generate_large_wordlist_performance():
    base = [f"user{i}" for i in range(1000)]
    wordlist = wordlist_generator.generate_wordlist(base, mutations=True)
    assert len(wordlist) > 1000

def test_wordlist_generator_cli(monkeypatch, tmp_path):
    args = ["prog", "wordlist-gen", "--base", "admin,root", "--output", str(tmp_path / "out.txt"), "--mutations"]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("utils.wordlist_generator.generate_wordlist", MagicMock(return_value=["admin", "root", "Admin123"]))
    monkeypatch.setattr("utils.wordlist_generator.save_wordlist", MagicMock(return_value=True))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        wordlist_generator.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "Wordlist gerada" in output or "admin" in output

def test_wordlist_generator_error_handling(tmp_path):
    with patch("builtins.open", side_effect=PermissionError("Simulado")):
        with pytest.raises(PermissionError):
            wordlist_generator.save_wordlist(["admin"], str(tmp_path / "fail.txt"))

def test_generate_wordlist_from_file(tmp_path):
    file_path = tmp_path / "base.txt"
    file_path.write_text("admin\nroot\nsenha\n")
    base = wordlist_generator.load_wordlist(str(file_path))
    wordlist = wordlist_generator.generate_wordlist(base)
    assert "admin" in wordlist and "root" in wordlist

def test_generate_wordlist_with_empty_base():
    wordlist = wordlist_generator.generate_wordlist([])
    assert wordlist == []

if __name__ == "__main__":
    pytest.main()