from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://127.0.0.1:5173",   # Vite dev server origin
    "http://localhost:5173",   # in case browser uses localhost
    # "http://localhost:8000", # add if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # set to ["*"] for quick dev, not recommended for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}