"""Entry point: python -m eplm"""

import uvicorn

from eplm.config import settings

uvicorn.run(
    "eplm.app:app",
    host="0.0.0.0",
    port=8000,
    reload=settings.debug,
)
