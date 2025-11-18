from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pbix_connector import save_api_key, load_api_key, get_pbix_metadata
import openai
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
    data = await request.json()
    key = data.get("key")
    if not key:
        return JSONResponse({"status":"error", "message":"No key provided"}, status_code=400)
    save_api_key(key)
    return {"status":"ok", "message":"API key saved successfully!"}

@app.get("/load-key")
async def get_key():
    key = load_api_key()
    if not key:
        return {"status":"error", "message":"No API key saved"}
    return {"status":"ok", "key":key}

# ----------------- PBIX MODEL -----------------
@app.get("/get-model")
async def get_model():
    try:
        model = get_pbix_metadata()
        return {"status":"ok", "model": model}
    except Exception as e:
        return {"status":"error", "message": str(e)}

# ----------------- ASK OPENAI -----------------
@app.post("/ask")
async def ask_openai(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    selected_data = data.get("selected_data", [])

    if not prompt or not selected_data:
        return {"answer":"No prompt or data provided."}

    # Load API key
    key = load_api_key()
    if not key:
        return {"answer":"API key not loaded."}
    
    openai.api_key = key

    # Combine selected tables into context
    context_text = ""
    for table in selected_data:
        context_text += f"Table: {table['Name']}\nColumns: {', '.join(table['Columns'])}\nMeasures: {', '.join(table.get('Measures',[]))}\n\n"

    full_prompt = f"Context:\n{context_text}\nUser question: {prompt}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user", "content":full_prompt}],
            max_tokens=800
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"Error: {e}"

    return {"answer": answer}

# ----------------- RUN -----------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
