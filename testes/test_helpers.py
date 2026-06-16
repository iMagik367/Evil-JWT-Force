from utils.helpers import (
    save_to_file,
    read_lines,
    write_lines,
    generate_nonce,
    get_current_timestamp,
    formatted_time,
    log_format,
    ensure_dir,
    clean_string,
    is_valid_url,
    safe_write_file,
    atomic_write,
    touch,
    remove_file,
    list_files,
    slugify,
    human_size
)

def test_atomic_write_and_read(tmp_path):
    file_path = tmp_path / "atomic.txt"
    content = "conteúdo atômico"
    assert atomic_write(str(file_path), content) is True
    assert read_lines(str(file_path)) == [content]

def test_touch_and_remove_file(tmp_path):
    file_path = tmp_path / "touch.txt"
    touch(file_path)
    assert file_path.exists()
    assert remove_file(file_path) is True
    assert not file_path.exists()

def test_list_files(tmp_path):
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file1.write_text("1")
    file2.write_text("2")
    files = list_files(tmp_path, "*.txt")
    assert str(file1) in files and str(file2) in files

def test_slugify():
    assert slugify("Texto Exemplo 123!") == "texto-exemplo-123"
    assert slugify("Árvore & Café") == "rvore-caf"

def test_human_size():
    assert human_size(0) == "0B"
    assert human_size(1024) == "1.0 KB"
    assert human_size(1048576) == "1.0 MB"