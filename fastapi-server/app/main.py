from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Spectacles Reorder Assistant",
        description=(
            "Backend for hands-free auto-replenishment."
            " Accepts detection events from Spectacles, manages prompt intents," 
            " and submits commerce orders once the user confirms."
        ),
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "message": "PiercePuppy reorder backend wagging happily",
            "docs": "/docs",
        }

    app.include_router(api_router)
    return app


app = create_app()
