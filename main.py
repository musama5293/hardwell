#!/usr/bin/env python3
"""
FastAPI Underwriting Application
Modern web interface for real estate underwriting with dynamic uploads and progress tracking.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uuid
import json
import asyncio
import shutil
from datetime import datetime
import logging

# Import our existing components (with error handling)
try:
    from document_processor import DocumentProcessor
    from underwriting_analyzer import UnderwritingAnalyzer
    from underwriting_output import UnderwritingOutputGenerator
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Some components not available: {e}")
    COMPONENTS_AVAILABLE = False

# FastAPI app initialization
app = FastAPI(
    title="Real Estate Underwriting AI",
    description="Professional underwriting analysis with AI-powered document processing",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory storage for processing status (in production, use Redis/database)
processing_sessions = {}

# Models for API requests/responses
class ProcessingStatus(BaseModel):
    session_id: str
    status: str  # "waiting", "processing", "completed", "error"
    current_step: int
    total_steps: int
    step_name: str
    progress_percentage: float
    message: str
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class PropertyInfo(BaseModel):
    property_name: str
    property_address: str
    transaction_type: str = "refinance"
    is_bridge_loan: bool = False

class AnalysisResults(BaseModel):
    session_id: str
    property_info: PropertyInfo
    rent_roll_analysis: Dict[str, Any]
    t12_analysis: Dict[str, Any]
    underwriting_summary: Dict[str, Any]
    excel_path: str
    pdf_path: str
    flags_count: int

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main application page."""
    return FileResponse("templates/index.html")

@app.post("/api/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    property_name: str,
    property_address: str,
    transaction_type: str = "refinance",
    is_bridge_loan: bool = False,
    files: List[UploadFile] = File(...)
):
    """
    Upload documents and start processing in background.
    Returns session ID for tracking progress.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Create session directory
    session_dir = f"uploads/{session_id}"
    os.makedirs(session_dir, exist_ok=True)
    
    # Save uploaded files
    uploaded_files = []
    for file in files:
        if file.filename:
            file_path = os.path.join(session_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(file_path)
    
    # Initialize processing status
    processing_sessions[session_id] = ProcessingStatus(
        session_id=session_id,
        status="waiting",
        current_step=0,
        total_steps=7,
        step_name="Initializing...",
        progress_percentage=0.0,
        message="Preparing to process documents"
    )
    
    # Property information
    property_info = PropertyInfo(
        property_name=property_name,
        property_address=property_address,
        transaction_type=transaction_type,
        is_bridge_loan=is_bridge_loan
    )
    
    # Start background processing
    background_tasks.add_task(
        process_documents_background,
        session_id,
        uploaded_files,
        property_info
    )
    
    return {"session_id": session_id, "message": "Processing started", "files_uploaded": len(uploaded_files)}

@app.get("/api/status/{session_id}")
async def get_processing_status(session_id: str):
    """Get current processing status for a session."""
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return processing_sessions[session_id]

@app.get("/api/results/{session_id}")
async def get_results(session_id: str):
    """Get final results for completed session."""
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = processing_sessions[session_id]
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Processing not completed")
    
    return session.results

@app.get("/api/download/{session_id}/{file_type}")
async def download_file(session_id: str, file_type: str):
    """Download generated files (excel or pdf)."""
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = processing_sessions[session_id]
    if session.status != "completed" or not session.results:
        raise HTTPException(status_code=400, detail="No files available")
    
    if file_type == "excel":
        file_path = session.results.get("excel_path")
    elif file_type == "pdf":
        file_path = session.results.get("pdf_path")
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=os.path.basename(file_path)
    )

async def process_documents_background(
    session_id: str,
    uploaded_files: List[str],
    property_info: PropertyInfo
):
    """
    Background task for processing documents with progress updates.
    """
    try:
        if not COMPONENTS_AVAILABLE:
            raise Exception("Document processing components not available")
            
        session = processing_sessions[session_id]
        session.status = "processing"
        
        # Step 1: Document Processing
        update_progress(session_id, 1, "Document Processing", "Extracting data from uploaded documents...")
        await asyncio.sleep(0.5)  # Small delay for UI responsiveness
        
        processor = DocumentProcessor(debug=True)
        rent_roll_data = None
        t12_data = None
        
        for file_path in uploaded_files:
            filename = os.path.basename(file_path).lower()
            if 'rent' in filename or 'rr_' in filename:
                rent_roll_data = processor.process_document(file_path, doc_type="RENT_ROLL")
            elif 't12' in filename or 'income' in filename:
                t12_data = processor.process_document(file_path, doc_type="T12")
        
        # Step 2: Data Analysis Setup
        update_progress(session_id, 2, "Data Analysis Setup", "Initializing underwriting analyzer...")
        await asyncio.sleep(0.3)
        
        analyzer = UnderwritingAnalyzer(debug=True)
        analyzer.set_property_info(
            property_name=property_info.property_name,
            property_address=property_info.property_address,
            unit_count=100,  # Would be extracted from documents
            transaction_type=property_info.transaction_type
        )
        
        # Step 3: Rent Roll Analysis
        update_progress(session_id, 3, "Rent Roll Analysis", "Analyzing rental income and unit data...")
        await asyncio.sleep(0.4)
        
        rent_roll_analysis = {}
        if rent_roll_data:
            rent_roll_analysis = analyzer.analyze_rent_roll(rent_roll_data)
        
        # Step 4: T12 Analysis
        update_progress(session_id, 4, "T12 Analysis", "Processing operating statement and expenses...")
        await asyncio.sleep(0.4)
        
        t12_analysis = {}
        if t12_data:
            t12_analysis = analyzer.analyze_t12(t12_data)
        
        # Step 5: Underwriting Summary
        update_progress(session_id, 5, "Underwriting Summary", "Generating comprehensive analysis...")
        await asyncio.sleep(0.3)
        
        underwriting_summary = analyzer.generate_underwriting_summary()
        
        # Step 6: Excel Generation
        update_progress(session_id, 6, "Excel Generation", "Creating professional underwriting package...")
        await asyncio.sleep(0.5)
        
        output_generator = UnderwritingOutputGenerator(debug=True)
        output_generator.load_analysis_data(
            rent_roll_analysis, t12_analysis, 
            analyzer.property_info, underwriting_summary
        )
        
        if property_info.is_bridge_loan:
            output_generator.set_bridge_loan_mode(True)
        
        excel_path = output_generator.export_to_excel()
        
        # Step 7: PDF Generation
        update_progress(session_id, 7, "PDF Generation", "Creating lender-ready PDF package...")
        await asyncio.sleep(0.4)
        
        pdf_path = output_generator.generate_pdf_package(excel_path)
        
        # Complete processing
        session.status = "completed"
        session.current_step = 7
        session.progress_percentage = 100.0
        session.step_name = "Processing Complete"
        session.message = "All documents processed successfully!"
        
        # Store results
        session.results = {
            "session_id": session_id,
            "property_info": property_info.dict(),
            "rent_roll_analysis": rent_roll_analysis,
            "t12_analysis": t12_analysis,
            "underwriting_summary": underwriting_summary,
            "excel_path": excel_path,
            "pdf_path": pdf_path,
            "flags_count": len(underwriting_summary.get('flags_and_recommendations', [])),
            "processing_time": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Processing completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Processing failed for session {session_id}: {str(e)}")
        session = processing_sessions[session_id]
        session.status = "error"
        session.error_message = str(e)
        session.message = f"Processing failed: {str(e)}"

def update_progress(session_id: str, step: int, step_name: str, message: str):
    """Update processing progress for a session."""
    if session_id in processing_sessions:
        session = processing_sessions[session_id]
        session.current_step = step
        session.total_steps = 7
        session.step_name = step_name
        session.progress_percentage = (step / 7) * 100
        session.message = message
        logger.info(f"📊 Session {session_id}: Step {step}/7 - {step_name}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Cleanup endpoint for development
@app.delete("/api/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up session data (development only)."""
    if session_id in processing_sessions:
        del processing_sessions[session_id]
        
        # Clean up files
        session_dir = f"uploads/{session_id}"
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        
        return {"message": f"Session {session_id} cleaned up"}
    
    raise HTTPException(status_code=404, detail="Session not found")

if __name__ == "__main__":
    import uvicorn
    
    # Ensure required directories exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    print("🚀 Starting Real Estate Underwriting AI Server...")
    print("📊 Access the application at: http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
