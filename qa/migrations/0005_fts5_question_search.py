# Generated manually for FTS5 full-text search on Question (SQLite).
#
# Where to see qa_question_search:
#   - Django shell: from django.db import connection; c = connection.cursor(); c.execute("SELECT rowid, title, body FROM qa_question_search LIMIT 5"); c.fetchall()
#   - SQLite CLI: sqlite3 db.sqlite3 → .tables → SELECT * FROM qa_question_search LIMIT 5;
#   - DB Browser for SQLite: open db.sqlite3 → Browse Data → table qa_question_search

from django.db import migrations


# FTS5 virtual table name; use qa_ prefix to match app and avoid clashes.
FTS_TABLE = "qa_question_search"
QUESTION_TABLE = "qa_question"
TRIGGER_AI = "qa_question_fts_ai"
TRIGGER_AD = "qa_question_fts_ad"
TRIGGER_AU = "qa_question_fts_au"


def create_fts5(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_TABLE} USING fts5(title, body)"
        )
        # Use qa_question's internal rowid so FTS rowid stays in sync (Question uses UUID pk).
        cursor.execute(
            f"""
            INSERT INTO {FTS_TABLE}(rowid, title, body)
            SELECT rowid, title, body FROM {QUESTION_TABLE}
            """
        )
        cursor.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {TRIGGER_AI} AFTER INSERT ON {QUESTION_TABLE} BEGIN
            INSERT INTO {FTS_TABLE}(rowid, title, body)
            VALUES (new.rowid, new.title, new.body);
            END;
            """
        )
        cursor.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {TRIGGER_AD} AFTER DELETE ON {QUESTION_TABLE} BEGIN
            INSERT INTO {FTS_TABLE}({FTS_TABLE}, rowid, title, body)
            VALUES('delete', old.rowid, old.title, old.body);
            END;
            """
        )
        cursor.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {TRIGGER_AU} AFTER UPDATE ON {QUESTION_TABLE} BEGIN
            INSERT INTO {FTS_TABLE}({FTS_TABLE}, rowid, title, body)
            VALUES('delete', old.rowid, old.title, old.body);
            INSERT INTO {FTS_TABLE}(rowid, title, body)
            VALUES (new.rowid, new.title, new.body);
            END;
            """
        )


def drop_fts5(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"DROP TRIGGER IF EXISTS {TRIGGER_AU}")
        cursor.execute(f"DROP TRIGGER IF EXISTS {TRIGGER_AD}")
        cursor.execute(f"DROP TRIGGER IF EXISTS {TRIGGER_AI}")
        cursor.execute(f"DROP TABLE IF EXISTS {FTS_TABLE}")


class Migration(migrations.Migration):

    dependencies = [
        ("qa", "0002_followup"),
    ]

    operations = [
        migrations.RunPython(create_fts5, drop_fts5),
    ]
