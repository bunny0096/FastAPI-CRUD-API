from fastapi import FastAPI

app = FastAPI(title="Task API", version="1.0")


@app.get("/", summary="Show a welcome message")
def root():
    return {"message": "Hello, server"}
