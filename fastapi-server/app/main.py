from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import json
import time

from app.api.routes import router as api_router

# Configure super verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Make sure all relevant loggers are verbose
for log_name in ["fastapi", "uvicorn", "uvicorn.access", "uvicorn.error"]:
    logging.getLogger(log_name).setLevel(logging.DEBUG)

class VerboseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log request details (using both print and logger for visibility)
        separator = "=" * 80
        print(f"\n{separator}")
        print(f"INCOMING REQUEST:")
        print(f"  Method: {request.method}")
        print(f"  URL: {request.url}")
        print(f"  Path: {request.url.path}")
        print(f"  Query Params: {dict(request.query_params)}")
        print(f"  Headers: {dict(request.headers)}")
        print(f"  Client: {request.client}")

        # Try to read and log body
        try:
            body = await request.body()
            if body:
                try:
                    body_str = body.decode()
                    print(f"  Body (raw length): {len(body_str)} chars")
                    print(f"  Body (raw): {body_str[:1000]}..." if len(body_str) > 1000 else f"  Body (raw): {body_str}")
                    try:
                        body_json = json.loads(body_str)
                        print(f"  Body (JSON):")
                        print(json.dumps(body_json, indent=2))
                    except Exception as je:
                        print(f"  JSON parse error: {je}")
                except Exception as de:
                    print(f"  Body decode error: {de}")
                    print(f"  Body (bytes): {body[:500]}...")
            else:
                print(f"  Body: <empty>")

            # Rebuild request with body
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive
        except Exception as e:
            print(f"  Error reading body: {e}")
            import traceback
            traceback.print_exc()

        # Process request
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            print(f"\nRESPONSE:")
            print(f"  Status Code: {response.status_code}")
            print(f"  Process Time: {process_time:.3f}s")
            print(f"  Headers: {dict(response.headers)}")
            print(f"{separator}\n")

            return response
        except Exception as e:
            print(f"\nEXCEPTION during request processing:")
            print(f"  {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            print(f"{separator}\n")
            raise


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

    # Add verbose logging middleware FIRST
    app.add_middleware(VerboseLoggingMiddleware)

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
