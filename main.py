#!/usr/bin/env python
"""Point d'entrée principal de l'API RAG."""

import uvicorn

from config import settings


def main():
    """Lance le serveur API."""
    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
