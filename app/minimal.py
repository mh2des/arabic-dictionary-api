"""
Minimal FastAPI app for Railway deployment testing.
This strips out all complex dependencies to isolate startup issues.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create minimal app
app = FastAPI(
    title="Arabic Dictionary API - Minimal",
    description="Minimal version for Railway deployment testing",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Ultra-simple health check."""
    return {"status": "healthy", "service": "arabic-dictionary-api-minimal"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Arabic Dictionary API - Minimal Version",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/test")
async def test():
    """Test endpoint."""
    return {"test": "success", "message": "API is working"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
