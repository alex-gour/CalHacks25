import uvicorn
import logging
from pyngrok import ngrok, conf

if __name__ == "__main__":
    port = 8000

    # Configure super verbose logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Set all loggers to DEBUG
    logging.getLogger("uvicorn").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
    logging.getLogger("fastapi").setLevel(logging.DEBUG)

    # Set ngrok auth token
    ngrok.set_auth_token("34abJ97hitX0A69peBefRhaNkOj_25K46fhzJfnsqTE1TMyPL")

    # Create ngrok tunnel
    public_url = ngrok.connect(port).public_url
    print(f"\n{'='*60}")
    print(f"ngrok tunnel created at: {public_url}")
    print(f"{'='*60}\n")

    # Run the FastAPI application with maximum verbosity
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        reload=True,
        log_level="trace",  # Most verbose level
        access_log=True,
        use_colors=True,
    )
