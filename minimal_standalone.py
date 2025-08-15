"""
Standalone minimal FastAPI app for Railway deployment testing.
No imports from app package to avoid complex dependencies.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create minimal app
app = FastAPI(
    title="Arabic Dictionary API - Standalone",
    description="Standalone minimal version for Railway deployment testing",
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
    return {"status": "healthy", "service": "arabic-dictionary-api-standalone"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Arabic Dictionary API - Standalone Minimal Version",
        "status": "running",
        "version": "1.0.0",
        "note": "This is a minimal version to test Railway deployment",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "test": "/test"
        }
    }

@app.get("/test")
async def test():
    """Test endpoint."""
    return {"test": "success", "message": "Standalone API is working perfectly"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
