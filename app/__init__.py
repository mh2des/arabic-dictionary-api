"""
Top level package for the Arabic dictionary backend.

Importing this package sets up the FastAPI application so that
``uvicorn backend.app.main:app`` can be used to start the server.
"""

from .main import app  # noqa
