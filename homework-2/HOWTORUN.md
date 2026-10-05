# ▶️ How to Run

Python 3.9+ required. In-memory storage — data resets when the server restarts.

## 1. Install

```bash
cd homework-2
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Start the API

```bash
cd src
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

- API root: http://localhost:8000
- Interactive docs (Swagger): http://localhost:8000/docs

## 3. Open the front-end

Open `frontend/index.html` in your browser (double-click, or serve it):

```bash
# optional simple static server, from the homework-2/frontend folder
python3 -m http.server 5500
# then browse to http://localhost:5500
```

The API base URL field at the top of the page defaults to
`http://localhost:8000`. CORS is enabled so the page can call the API.

## 4. Try bulk import

In the UI click **⬆ Import** and pick one of the sample files in `demo/`
(`sample_tickets.csv`, `sample_tickets.json`, `sample_tickets.xml`), or via curl:

```bash
curl -X POST http://localhost:8000/tickets/import -F "file=@demo/sample_tickets.csv"
```

## 5. Run the tests

```bash
source .venv/bin/activate
python -m pytest --cov=src --cov-report=term-missing
```

To produce an HTML coverage report (for the screenshot deliverable):

```bash
python -m pytest --cov=src --cov-report=html
open htmlcov/index.html            # Linux: xdg-open ; Windows: start
```
