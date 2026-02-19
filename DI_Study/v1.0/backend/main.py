from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import data_loader
import etl_service
import os
import shutil
from dotenv import load_dotenv

from fastapi.staticfiles import StaticFiles

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = FastAPI()

# Mount frontend directory for static files
# We mount it at /static or directly at /? 
# Usually mount at / and serve index.html
from os.path import dirname, join
frontend_path = join(dirname(dirname(__file__)), 'frontend')
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse(join(frontend_path, 'index.html'))


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins
    allow_credentials=False, # Disable credentials to allow wildcard origin
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/insight")
def get_insight_data(country: str = Query("US", description="Country Code"), month: str = Query(None, description="Report Month (YYYY-MM)")):
    try:
        data = data_loader.load_insight_data(country_code=country, year_month=month)
        return data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/available_months")
def get_available_months(country: str = Query("US")):
    try:
        months = data_loader.get_available_months(country_code=country)
        return {"months": months}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/analyze/{section}")
def analyze_section(section: str, country: str = Query("US"), month: str = Query(None)):
    try:
        data = data_loader.load_insight_data(country_code=country, year_month=month)
        
        # Validate section
        if section not in ['market', 'product', 'size', 'price']:
             return JSONResponse(status_code=400, content={"error": "Invalid section"})
             
        import llm_analysis
        insights = llm_analysis.generate_analysis(section, data)
        return {"insights": insights}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    country: str = Form(...),
    month: str = Form(...) # '2025-10'
):
    try:
        # Save temp file
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Run ETL
        success = etl_service.process_excel_to_db(temp_path, country, month)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if success:
            return {"message": "File processed and DB updated successfully"}
        else:
            return JSONResponse(status_code=500, content={"error": "ETL Processing Failed"})
            
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
