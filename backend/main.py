from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pbix_connector import save_api_key, load_api_key, get_pbix_metadata
from openai import OpenAI
import uvicorn

app = FastAPI()

# Allow frontend (opened in browser) to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- API KEY -----------------
@app.post("/save-key")
async def save_key(request: Request):
    try:
        data = await request.json()
        key = data.get("key")
        if not key:
            return JSONResponse(
                {"status": "error", "message": "No key provided"}, 
                status_code=400
            )
        save_api_key(key)
        return {"status": "ok", "message": "API key saved successfully!"}
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": f"Error saving key: {str(e)}"}, 
            status_code=500
        )

@app.get("/load-key")
async def get_key():
    try:
        key = load_api_key()
        if not key:
            return {"status": "error", "message": "No API key saved"}
        return {"status": "ok", "key": key}
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": f"Error loading key: {str(e)}"}, 
            status_code=500
        )

# ----------------- PBIX MODEL -----------------
@app.get("/get-model")
async def get_model():
    try:
        model = get_pbix_metadata()
        if not model:
            return {
                "status": "error", 
                "message": "No Power BI instance found or no tables available",
                "model": []
            }
        return {"status": "ok", "model": model}
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": f"Error loading model: {str(e)}", "model": []}, 
            status_code=500
        )

# ----------------- ASK OPENAI -----------------
@app.post("/ask")
async def ask_openai(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        selected_data = data.get("selected_data", [])

        if not prompt:
            return {"answer": "❌ No prompt provided."}
        
        if not selected_data:
            return {"answer": "❌ No tables selected."}

        # Load API key
        key = load_api_key()
        if not key:
            return {"answer": "❌ API key not loaded. Please save your OpenAI API key first."}
        
        # Initialize OpenAI client with new API
        client = OpenAI(api_key=key)

        # Combine selected tables into context
        context_text = "Power BI Data Model Context:\n\n"
        for table in selected_data:
            context_text += f"📊 Table: {table['Name']}\n"
            context_text += f"   Columns: {', '.join(table['Columns'])}\n"
            if table.get('Measures'):
                context_text += f"   Measures: {', '.join(table['Measures'])}\n"
            context_text += "\n"

        full_prompt = f"{context_text}\n🔍 User Question:\n{prompt}\n\nPlease provide clear, actionable guidance based on this Power BI data model."

        # Use new OpenAI API syntax
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful Power BI and DAX expert assistant. Provide clear, practical advice."
                },
                {
                    "role": "user", 
                    "content": full_prompt
                }
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
    except Exception as e:
        answer = f"❌ Error communicating with OpenAI:\n\n{str(e)}\n\nPlease check:\n- Your API key is valid\n- You have OpenAI credits/quota\n- Your internet connection"

    return {"answer": answer}

# ----------------- HEALTH CHECK -----------------
@app.get("/")
async def root():
    return {
        "status": "ok", 
        "message": "Albert's Power BI Assistant Backend is running!",
        "endpoints": ["/save-key", "/load-key", "/get-model", "/ask"]
    }

# ----------------- RUN -----------------
if __name__ == "__main__":
    print("🚀 Starting Albert's Power BI Assistant Backend...")
    print("📍 Backend running at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)