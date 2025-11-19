# dashboard_main.py
from dashboard import create_dashboard
from main import bot  # DEIN Bot aus main.py

import uvicorn

app = create_dashboard(bot)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
