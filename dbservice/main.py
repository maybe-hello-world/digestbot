from asyncio import get_event_loop

import uvicorn
from asyncpg.exceptions import PostgresError

from fastapi import FastAPI, Request, HTTPException

from dbprovider.engine import db_engine
from routers import timer, preset, message, ignore

app = FastAPI()
app.include_router(timer.router, prefix="/timer", tags=['timer'])
app.include_router(preset.router, prefix="/preset", tags=['preset'])
app.include_router(message.router, prefix="/message", tags=['message'])
app.include_router(ignore.router, prefix="/ignore", tags=["ignore"])


@app.on_event("startup")
async def startup():
    await db_engine.ainit()


@app.on_event("shutdown")
async def shutdown():
    await db_engine.close()


@app.exception_handler(PostgresError)
async def asyncpg_exception_handler(request: Request, exc: PostgresError):
    db_engine.logger.error(f"Error occurred during processing of the request: {request.url}")
    db_engine.logger.exception(exc)
    raise HTTPException(status_code=500, detail=str(exc))


if __name__ == '__main__':
    loop = get_event_loop()
    loop.run_until_complete(db_engine.check_or_create_database())
    loop.run_until_complete(db_engine.ainit())
    loop.run_until_complete(db_engine.check_or_create_tables())
    uvicorn.run(app, host="0.0.0.0", port=8000)
