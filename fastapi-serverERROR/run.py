import uvicorn

try:
    from pyngrok import ngrok
except ImportError:  # pragma: no cover
    ngrok = None


if __name__ == "__main__":
    port = 8000

    if ngrok:
        public_url = ngrok.connect(port).public_url
        print(f"ngrok tunnel created at: {public_url}")

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        reload=True,
        log_level="info",
    )
