import uvicorn
import sys
import os

# Ensure backend package is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    is_prod = (
        os.environ.get("ENVIRONMENT", "").lower() == "production"
        or os.environ.get("RAILWAY_ENVIRONMENT") is not None
    )
    reload = not is_prod

    print("==================================================================")
    print("  FloodResQ — AI Flood Monitoring & Emergency Response Platform")
    print("==================================================================")
    print(f"  Server starting at: http://{host}:{port}")
    print(f"  API Docs available at: http://{host}:{port}/docs")
    print(f"  Report page at: http://{host}:{port}/report.html")
    print("==================================================================")
    uvicorn.run("backend.main:app", host=host, port=port, reload=reload)
