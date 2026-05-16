from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent/".env"
load_dotenv(dotenv_path=env_path)
from app.routers import analysis_router, upload_router, visualization_router, report_router, Ai_router
from app.routes.auth import router as auth_router

# Serve frontend files from the parent (gpp) directory
FRONTEND_DIR = Path(__file__).parent.parent.parent


Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Data Wizard API",
    description="Your magical data analysis companion - Transform raw data into insights!",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router.router, prefix="/upload", tags=["Upload"])
app.include_router(analysis_router.router, prefix="/analysis", tags=["Analysis"])
app.include_router(visualization_router.router, prefix="/visualization", tags=["Visualization"])
app.include_router(report_router.router, prefix="/reports", tags=["Reports"])
app.include_router(Ai_router.router, prefix="/ai", tags=["AI Business Insights"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Mount frontend static files (must be AFTER all API routers)
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

@app.get("/")
async def root():
    return {
        "spell": "Data Wizard is ready!",
        "magic_level": "100%",
        "grimoire": "/docs",
        "spells": {
            "upload_spell": "/upload/uploadfile/",
            "analysis_spell": "/analysis/analyze/{file_id}",
            "advanced_magic": "/analysis/advanced/{file_id}",
            "visualization_spell": "/visualization/{file_id}",
            "full_report": "/reports/{file_id}",
            "quick_report": "/reports/{file_id}/quick",
            "list_reports": "/reports/{file_id}/list",
            "download_report": "/reports/download/{file_id}?analysis_type=advanced",
            "delete_report": "/reports/{file_id}?analysis_type=advanced"
        },
        "message": "Your data is about to experience magic!"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "The Wizard is awake and ready!",
        "mana": "∞",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }