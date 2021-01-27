from fastapi import FastAPI
from routers import timer, category, message


app = FastAPI()

app.include_router(timer.router, prefix="/timer", tags=['timer'])
app.include_router(category.router, prefix="/category", tags=['category'])
app.include_router(message.router, prefix="/message", tags=['message'])
