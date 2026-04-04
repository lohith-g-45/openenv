import os

import uvicorn

from api import app


def main() -> None:
    host = "0.0.0.0"
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run("server.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
