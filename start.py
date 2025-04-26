import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:application",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        lifespan="on",
        access_log=False,
        reload=True,
        timeout_graceful_shutdown=0,
    )
