from . import database 
try:
    database.setup_database()
except Exception as e:
    print(f"FATALER FEHLER beim Initialisieren der Datenbank: {e}") 

__all__ = ['database']