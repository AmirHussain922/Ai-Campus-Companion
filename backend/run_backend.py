import uvicorn
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    import os
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 8002)),
        log_level="debug",
        access_log=True
    )
