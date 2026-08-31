from fastapi import FastAPI

app = FastAPI(title="Task API", version="1.0")


@app.get("/", summary="Describe the API")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Check whether the API is running")
def health():
    return {"status": "ok"}
