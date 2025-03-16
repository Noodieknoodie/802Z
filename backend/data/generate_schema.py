import sqlite3

source_db = r"C:\CODING\802Z\backend\data\401k_payments.db"
schema_file = r"C:\CODING\802Z\backend\data\schema.sql"
sample_data_file = r"C:\CODING\802Z\backend\data\example_data.txt"

conn = sqlite3.connect(source_db)
cursor = conn.cursor()

# Generate schema.sql
schema_parts = {"table": [], "view": [], "trigger": [], "index": []}

cursor.execute("""
    SELECT type, name, sql FROM sqlite_master
    WHERE name NOT LIKE 'sqlite_%' AND sql IS NOT NULL
    ORDER BY type, name;
""")

for obj_type, name, sql in cursor.fetchall():
    header = f'----------------\n-- {obj_type.upper()}: {name}\n----------------\n'
    schema_parts[obj_type].append(f"{header}{sql.strip().rstrip(';')};\n")

with open(schema_file, 'w', encoding='utf-8') as f:
    for category in ["table", "view", "trigger", "index"]:
        if schema_parts[category]:
            f.write('\n'.join(schema_parts[category]) + '\n')

with open(schema_file, 'r', encoding='utf-8') as file:
    lines = file.readlines()

with open(schema_file, 'w', encoding='utf-8') as file:
    file.writelines(line for line in lines if line.strip())

# Generate example_data.txt
cursor.execute("""
    SELECT type, name FROM sqlite_master 
    WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'
    ORDER BY type, name;
""")
objects = cursor.fetchall()

with open(sample_data_file, 'w', encoding='utf-8') as f:
    f.write("----------------\nSAMPLE DATA\n----------------\n\n")

    for obj_type, name in objects:
        cursor.execute(f'SELECT COUNT(*) FROM "{name}"')
        count = cursor.fetchone()[0]
        if count == 0:
            continue

        positions = set(range(3)) | \
                    set(range(max(0, count//2 - 1), min(count//2 + 2, count))) | \
                    set(range(max(count - 3, 0), count))
        positions = sorted(positions)

        cursor.execute(f'SELECT * FROM "{name}" LIMIT 1')
        headers = [desc[0] for desc in cursor.description]

        f.write(f"-- {obj_type.upper()}: {name}\n")
        f.write(", ".join(headers) + "\n")

        for pos in positions:
            cursor.execute(f'SELECT * FROM "{name}" LIMIT 1 OFFSET ?', (pos,))
            row = cursor.fetchone()
            if row:
                row_display = ", ".join('NULL' if v is None else str(v) for v in row)
                f.write(row_display + '\n')

        f.write('\n')

with open(sample_data_file, 'r', encoding='utf-8') as file:
    lines = file.readlines()

with open(sample_data_file, 'w', encoding='utf-8') as file:
    file.writelines(line for line in lines if line.strip())

conn.close()
