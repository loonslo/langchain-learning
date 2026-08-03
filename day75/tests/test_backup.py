import sqlite3
from customer_support.backup import backup, integrity


def test_backup_is_actually_readable(tmp_path):
    source = tmp_path / "a.db"
    target = tmp_path / "b.db"
    with sqlite3.connect(source) as c:
        c.execute("CREATE TABLE x(id INTEGER)")
        c.execute("INSERT INTO x VALUES(1)")
    backup(source, target)
    assert integrity(target)
    with sqlite3.connect(target) as c:
        assert c.execute("SELECT count(*) FROM x").fetchone()[0] == 1
