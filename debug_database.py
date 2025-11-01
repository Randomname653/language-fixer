#!/usr/bin/env python3
"""
Database Debug Tool für Language-Fixer

Analysiert die SQLite Datenbank und zeigt an:
- Wie viele Dateien als "processed" markiert sind
- Welche Dateien übersprungen werden sollten
- Ob die Skip-Logik korrekt funktioniert
"""

import os
import sqlite3
import sys
from pathlib import Path

def analyze_database():
    """Analysiert die Language-Fixer Datenbank."""
    
    # DB_PATH aus Environment oder Standard
    db_path = os.getenv("DB_PATH", "/config/langfixer.db")
    
    print("🔍 LANGUAGE-FIXER DATABASE ANALYSE")
    print("=" * 60)
    print(f"Datenbank Pfad: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ PROBLEM: Datenbank existiert nicht!")
        print("   Die Datenbank sollte beim ersten Start erstellt werden.")
        print("   Mögliche Ursachen:")
        print("   - DB_PATH Umgebungsvariable falsch gesetzt")
        print("   - Keine Schreibrechte auf /config/")
        print("   - Container-Volume nicht gemountet")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Prüfe Tabellen
            print("\n📊 TABELLEN:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table in tables:
                print(f"  ✅ {table[0]}")
            
            # Processed Files
            print("\n📁 VERARBEITETE DATEIEN:")
            cursor.execute("SELECT COUNT(*) FROM processed_files")
            processed_count = cursor.fetchone()[0]
            print(f"  Anzahl: {processed_count}")
            
            if processed_count > 0:
                print("\n  Letzte 5 verarbeitete Dateien:")
                cursor.execute("SELECT filepath, datetime(mtime, 'unixepoch') FROM processed_files ORDER BY mtime DESC LIMIT 5")
                for filepath, date in cursor.fetchall():
                    filename = os.path.basename(filepath)
                    print(f"    📄 {filename} ({date})")
            
            # Failed Files
            print("\n❌ FEHLGESCHLAGENE DATEIEN:")
            cursor.execute("SELECT COUNT(*) FROM failed_files")
            failed_count = cursor.fetchone()[0]
            print(f"  Anzahl: {failed_count}")
            
            if failed_count > 0:
                print("\n  Fehlgeschlagene Dateien:")
                cursor.execute("SELECT filepath, fail_count, datetime(mtime, 'unixepoch') FROM failed_files ORDER BY fail_count DESC LIMIT 5")
                for filepath, fail_count, date in cursor.fetchall():
                    filename = os.path.basename(filepath)
                    print(f"    ❌ {filename} (Fehler: {fail_count}, {date})")
            
            # Stats
            print("\n📈 STATISTIKEN:")
            cursor.execute("SELECT key, value FROM cumulative_stats WHERE value > 0")
            stats = cursor.fetchall()
            for key, value in stats:
                print(f"  {key}: {value}")
    
    except sqlite3.Error as e:
        print(f"❌ DATENBANKFEHLER: {e}")

def test_skip_logic():
    """Testet die Skip-Logik mit einer Beispiel-Datei."""
    print("\n\n🧪 SKIP-LOGIK TEST")
    print("=" * 60)
    
    # Simuliere eine Beispiel-Datei
    test_file = "/media/AnimeShows/Test Anime/episode.mkv"
    
    db_path = os.getenv("DB_PATH", "/config/langfixer.db")
    
    if not os.path.exists(db_path):
        print("❌ Kann Skip-Test nicht durchführen: Datenbank fehlt")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print(f"Teste Datei: {test_file}")
            
            # Prüfe ob in processed_files
            cursor.execute("SELECT mtime FROM processed_files WHERE filepath = ?", (test_file,))
            result = cursor.fetchone()
            
            if result:
                print(f"  ✅ In processed_files gefunden (mtime: {result[0]})")
                print("  → Datei SOLLTE übersprungen werden")
            else:
                print("  ❌ NICHT in processed_files")
                print("  → Datei WIRD verarbeitet")
            
            # Prüfe failed_files
            cursor.execute("SELECT fail_count, mtime FROM failed_files WHERE filepath = ?", (test_file,))
            result = cursor.fetchone()
            
            if result:
                fail_count, mtime = result
                max_failures = 3  # Standard MAX_FAILURES
                if fail_count >= max_failures:
                    print(f"  ❌ In failed_files: {fail_count} Fehler (≥{max_failures})")
                    print("  → Datei SOLLTE übersprungen werden")
                else:
                    print(f"  ⚠️  In failed_files: {fail_count} Fehler (<{max_failures})")
                    print("  → Datei WIRD nochmal versucht")
    
    except sqlite3.Error as e:
        print(f"❌ FEHLER beim Skip-Test: {e}")

def check_common_issues():
    """Prüft häufige Probleme."""
    print("\n\n🔧 HÄUFIGE PROBLEME")
    print("=" * 60)
    
    issues = []
    
    # 1. DRY_RUN Mode
    dry_run = os.getenv("DRY_RUN", "false").lower() in ('true', '1', 't')
    if dry_run:
        issues.append("⚠️  DRY_RUN=true - Dateien werden NICHT als processed markiert!")
    
    # 2. DB_PATH
    db_path = os.getenv("DB_PATH", "/config/langfixer.db")
    if not os.path.exists(os.path.dirname(db_path)):
        issues.append(f"❌ DB Directory existiert nicht: {os.path.dirname(db_path)}")
    
    # 3. Permissions
    if os.path.exists(db_path):
        if not os.access(db_path, os.R_OK | os.W_OK):
            issues.append(f"❌ Keine Schreib/Lese-Rechte auf: {db_path}")
    
    if issues:
        print("Gefundene Probleme:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ Keine offensichtlichen Probleme gefunden")

def main():
    """Hauptfunktion."""
    analyze_database()
    test_skip_logic()
    check_common_issues()
    
    print("\n\n💡 LÖSUNGSANSÄTZE")
    print("=" * 60)
    print("Falls alle Dateien neu gescannt werden:")
    print("1. Prüfe DRY_RUN=false in Docker-Compose")
    print("2. Prüfe DB_PATH Volume-Mount korrekt")
    print("3. Prüfe Schreibrechte auf /config/")
    print("4. Logs nach DB-Fehlern durchsuchen")
    print("5. Container neu starten nach Config-Änderungen")

if __name__ == "__main__":
    main()