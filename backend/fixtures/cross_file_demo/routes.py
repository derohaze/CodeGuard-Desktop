from fastapi import FastAPI, Request

from service import run_job


app = FastAPI()


@app.post("/run")
async def run(request: Request):
    payload = await request.body()
    return run_job(payload.decode())
