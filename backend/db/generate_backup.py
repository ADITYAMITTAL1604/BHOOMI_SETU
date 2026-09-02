"""Generate a database dump of the known-good seeded demo database."""

import os
import sqlite3

def dump_db():
    db_path = "bhoomisetu.db"
    out_path = "db/demo_backup.sql"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} does not exist.")
        return
    
    con = sqlite3.connect(db_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("-- ====================================================================\n")
        f.write("-- BhoomiSetu Known-Good Seeded Demo Database Backup\n")
        f.write("-- Generated for Cold-Start Deployment & Instant Demo Recovery\n")
        f.write("-- ====================================================================\n\n")
        for line in con.iterdump():
            f.write(f"{line}\n")
    con.close()
    
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Successfully generated {out_path} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    dump_db()
