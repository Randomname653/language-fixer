#!/usr/bin/env python3
"""
Debug Script: Warum werden alle Anime-Titel erneut gescannt?

Analysiert mögliche Gründe warum die Skip-Logik nicht funktioniert.
"""

def analyze_potential_issues():
    """Analysiert potentielle Probleme."""
    print("🔍 WARUM WERDEN ALLE DATEIEN ERNEUT GESCANNT?")
    print("=" * 60)
    
    print("\n1. ❌ DRY_RUN=true Problem:")
    print("   Wenn DRY_RUN=true, werden Dateien NIEMALS als 'processed' markiert!")
    print("   Code: if not DRY_RUN: mark_file_as_processed(cursor, file_path, current_mtime)")
    print("   ✅ Lösung: DRY_RUN=false setzen")
    
    print("\n2. ❌ Database-Path Problem:")
    print("   Standard DB_PATH='/config/langfixer.db'")
    print("   Wenn /config/ nicht gemountet → DB geht bei Container-Restart verloren")
    print("   ✅ Lösung: Volume für /config korrekt mounten")
    
    print("\n3. ❌ File mtime (Änderungszeit) Änderung:")
    print("   Skip-Logik: if r and r[0] == mtime: return True")
    print("   Wenn Datei-Timestamp sich ändert → wird als 'neu' erkannt")
    print("   Ursachen: Dateisystem-Sync, Backup-Restore, Permissions-Change")
    print("   ✅ Lösung: Logs prüfen ob mtime-Mismatches geloggt werden")
    
    print("\n4. ❌ Database wird gelöscht/zurückgesetzt:")
    print("   Bei jedem Container-Restart neue DB")
    print("   ✅ Lösung: Persistent Volume verwenden")
    
    print("\n5. ❌ Code-Update löschte Database:")
    print("   Neue Version → alte DB kompatibel?")
    print("   ✅ Lösung: DB-Schema prüfen")

def check_docker_config():
    """Prüft typische Docker-Konfigurationsfehler."""
    print("\n\n🐳 DOCKER KONFIGURATION PRÜFEN")
    print("=" * 60)
    
    print("Prüfe deine docker-compose.yml:")
    print()
    
    print("❌ HÄUFIGER FEHLER - Volume nicht persistiert:")
    print("volumes:")
    print("  - /pfad/zu/config:/config  # ← MUSS persistent sein!")
    print()
    
    print("❌ HÄUFIGER FEHLER - DRY_RUN versehentlich auf true:")
    print("environment:")
    print("  - DRY_RUN=false  # ← MUSS false sein für Persistierung!")
    print()
    
    print("❌ HÄUFIGER FEHLER - Permissions:")
    print("  PUID/PGID müssen Schreibrechte auf /config haben")

def quick_diagnosis():
    """Schnelle Diagnose-Befehle."""
    print("\n\n🩺 SCHNELLE DIAGNOSE")
    print("=" * 60)
    
    print("1. Prüfe ob DB existiert:")
    print("   docker exec language-fixer ls -la /config/")
    print()
    
    print("2. Prüfe DB-Inhalt:")
    print("   docker exec language-fixer sqlite3 /config/langfixer.db \"SELECT COUNT(*) FROM processed_files;\"")
    print()
    
    print("3. Prüfe Container-Logs:")
    print("   docker logs language-fixer | grep -i \"überspringe\\|skip\\|processed\"")
    print()
    
    print("4. Prüfe DRY_RUN Setting:")
    print("   docker exec language-fixer env | grep DRY_RUN")

def immediate_fixes():
    """Sofortige Lösungsansätze."""
    print("\n\n⚡ SOFORTIGE LÖSUNGEN")
    print("=" * 60)
    
    print("1. 🔧 Container neustarten mit korrekter Config:")
    print("   - DRY_RUN=false")
    print("   - /config Volume persistent")
    print("   - Korrekte PUID/PGID")
    print()
    
    print("2. 🔧 Database-Status prüfen:")
    print("   python debug_database.py")
    print()
    
    print("3. 🔧 Logs analysieren:")
    print("   Suche nach:")
    print("   - '🚫 Überspringe' (sollte für bereits verarbeitete Dateien erscheinen)")
    print("   - 'DB Fehler' (zeigt Datenbankprobleme)")
    print("   - 'mark_file_as_processed' (zeigt erfolgreiche Markierung)")

def main():
    analyze_potential_issues()
    check_docker_config()
    quick_diagnosis()
    immediate_fixes()
    
    print("\n\n🎯 WAHRSCHEINLICHSTE URSACHE:")
    print("=" * 60)
    print("Entweder:")
    print("1. DRY_RUN=true (dann werden Dateien nie als processed markiert)")
    print("2. /config Volume nicht persistent (DB geht bei Restart verloren)")
    print("3. File mtime hat sich geändert (Dateisystem-Sync-Problem)")
    
    print("\n💡 ERSTE SCHRITTE:")
    print("1. docker logs language-fixer | tail -50")
    print("2. Prüfe docker-compose.yml Volume-Mapping")
    print("3. Führe debug_database.py aus")

if __name__ == "__main__":
    main()