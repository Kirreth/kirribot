# dashboard_runner.py
from dashboard_main import create_dashboard

app = create_dashboard(bot=None)  # bot=None, wird intern nur für Discord API genutzt

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
