from src.main import app, ensure_venv

if __name__ == "__main__":
	ensure_venv()
	app.launch()