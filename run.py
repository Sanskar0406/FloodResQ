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
    print("==================================================================")
    print("  FloodResQ — AI Flood Monitoring & Emergency Response Platform")
    print("==================================================================")
    print("  Server starting at: http://127.0.0.1:8000")
    print("  API Docs available at: http://127.0.0.1:8000/docs")
    print("  Report page at: http://127.0.0.1:8000/report.html")
    print("==================================================================")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
