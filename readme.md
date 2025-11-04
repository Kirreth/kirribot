```
  _  _______ _____  _____  _____ ____   ____ _______ 
 | |/ /_   _|  __ \|  __ \|_   _|  _ \ / __ \__   __|
 | ' /  | | | |__) | |__) | | | | |_) | |  | | | |   
 |  <   | | |  _  /|  _  /  | | |  _ <| |  | | | |   
 | . \ _| |_| | \ \| | \ \ _| |_| |_) | |__| | | |   
 |_|\_\_____|_|  \_\_|  \_\_____|____/ \____/  |_|   
```
 
## Ein robuster, multiserverfähiger Discord-Bot mit Fokus auf Community-Management, spezialisierten Tools und interaktiver Unterhaltung.

**🌟 Über das Projekt**

Kirribot ist eine vielseitige Discord-Anwendung, die entwickelt wurde, um Entwickler-Communities und allgemeine Server gleichermaßen zu unterstützen. Der Bot bietet spezialisierte Funktionen wie ein Coder-Qualifikationsquiz, einen Musik-Link-Konverter und ein modernes, grafisches Levelsystem (realisiert mit Pillow).

Der Kirribot ist von Grund auf multiserverfähig konzipiert. Alle Konfigurationen, Warnungen und Benutzerfortschritte (Level) werden persistent in einer Datenbank gespeichert.
```
======================================================================================================================================
| KATEGORIE       | FUNKTION (COG)        | BESCHREIBUNG                                                                             |
======================================================================================================================================
| Community       | Levelsystem           | Fortschrittliches Levelsystem, das die Aktivität der Benutzer belohnt und grafische      |
|                 |                       | Levelkarten generiert (nutzt Pillow).                                                    |
|                 +-----------------------+------------------------------------------------------------------------------------------+
|                 | Geburtstagserinnerung | Automatische Benachrichtigung bei Geburtstagen der Community-Mitglieder.                 |
======================================================================================================================================
| Sprachkanäle    | DynamicVoice          | Automatisches Erstellen und Löschen von temporären Voice-Channels. Garantiert, dass der  |
|                 |                       | "Join to Create"-Starter-Channel nach dem Löschen sofort neu erstellt wird, um ständige  |
|                 |                       | Verfügbarkeit zu gewährleisten.                                                          |
======================================================================================================================================
| Moderation      | Moderatoren-Tools     | Essenzielle Funktionen zur Serverkontrolle: mute, warn, und bann.                        |
|                 +-----------------------+------------------------------------------------------------------------------------------+
|                 | Bumperinnerung        | Erinnert an das Bumping des Servers auf Discord-Listen (z.B. Disboard).                  |
======================================================================================================================================
| Quiz & Games    | CoderQuiz             | Ein Qualifikationsquiz, das anhand von Fragen zu Basiswissen (z.B. Indexierung,          |
|                 |                       | Datenformate) die Eignung als Entwickler prüft.                                          |
|                 +-----------------------+------------------------------------------------------------------------------------------+
|                 | PartyQuiz             | Ein einfaches Allgemeinwissen-Quiz zum Zeitvertreib, spielbar alleine oder gegen         |
|                 |                       | andere Mitspieler.                                                                       |
======================================================================================================================================
| Tools           | LinkConverter         | Einzigartiges Tool, das Musik-Links zwischen Anbietern (Spotify, Apple Music, YouTube,   |
|                 |                       | Deezer) konvertiert.                                                                     |
|                 +-----------------------+------------------------------------------------------------------------------------------+
|                 | TextFormatter         | Wandelt reinen Text in formatierte Discord-Codeblöcke um.                                |
======================================================================================================================================
```
🚀 Setup und Installation
Voraussetzungen
Python 3.10+ (oder höher)

Ein Discord Bot Token und die aktivierten Intents (intents.members und intents.voice_states sind erforderlich).

Eine Datenbank-Instanz (z.B. PostgreSQL oder SQLite) zur Speicherung der Multiserver-Daten.

Die Pillow-Bibliothek zur Erzeugung der Level-Grafiken (muss systemweit oder in der virtuellen Umgebung korrekt installiert sein).

Kernfunktionen des Bots
```
Befehl                          |   Modul        | Beschreibung

/setup channel voice <channel>	|   DynamicVoice |	Definiert den Sprachkanal, der zum Erstellen neuer, temporärer Kanäle dient.
/level [user]	                |   Levelsystem  |	Zeigt das Level des Benutzers oder eines markierten Mitglieds an.
/warn <user> <reason>	        |   Moderation	 |  Erteilt einem Benutzer eine Verwarnung.
/quiz start coder	            |   CoderQuiz    |	Startet das Coder-Qualifikationsquiz zur Wissensprüfung.
/quiz start party	            |   PartyQuiz    |	Startet eine allgemeine Wissensrunde.
```

📧 Kontakt
Bei Fragen, Problemen oder Funktionswünschen wenden Sie sich bitte an:

Discord: kirreth