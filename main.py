from uvicorn import run
from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def root():
    return {"Hello": "World"}


if __name__ == "__main__":
    run("main:app", host="localhost", port=8000, reload=True)
