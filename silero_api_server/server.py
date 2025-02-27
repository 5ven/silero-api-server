
import os
import pathlib
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from silero_api_server.tts import SileroTtsService
from loguru import logger
from typing import Optional

module_path = pathlib.Path(__file__).resolve().parent
os.chdir(module_path)
SAMPLE_PATH = pathlib.Path("samples")

tts_service = SileroTtsService(f"{module_path}//{SAMPLE_PATH}")
app = FastAPI()

# Make sure the samples directory exists
if not SAMPLE_PATH.exists():
    SAMPLE_PATH.mkdir()

if len(list(SAMPLE_PATH.iterdir())) == 0:
    logger.info("Samples empty, generating new samples.")
    tts_service.generate_samples()

app.mount(f"/samples",StaticFiles(directory=module_path.joinpath(SAMPLE_PATH)),name='samples')
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Voice(BaseModel):
    speaker: str
    text: str
    session: Optional[str] = None

class SampleText(BaseModel):
    text: Optional[str]

class SessionPayload(BaseModel):
    path: Optional[str]

class Language(BaseModel):
    id: str

@app.get("/tts/speakers")
def speakers(request: Request):
    voices = [
        {
            "name":speaker,
            "voice_id":speaker,
            "preview_url": f"{str(request.base_url)}{SAMPLE_PATH}/{speaker}.wav"
        } for speaker in tts_service.get_speakers()
    ]
    return voices

@app.post("/tts/generate")
async def generate(voice: Voice):
    session_id = voice.session
    try:
        if session_id is None:
            session_id = tts_service.session_manager.create_session()
        else:
            existing_session_id = tts_service.session_manager.get_session_path(session_id)
            if existing_session_id:
                tts_service.session_manager.init_session_path(session_id)  
        audio = tts_service.generate(voice.speaker, voice.text, session_id)
        return FileResponse(audio)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{voice.speaker} generation failed: {e}")
            
@app.get("/tts/sample")
def play_sample(speaker: str):
    return FileResponse(f"{SAMPLE_PATH}/{speaker}.wav",status_code=200)

@app.post("/tts/generate-samples")
def generate_samples(sample_text: Optional[str] = ""):
    tts_service.update_sample_text(sample_text)
    tts_service.generate_samples()
    return Response("Generated samples",status_code=200)

@app.post("/tts/session")
def init_session(sessionPayload: SessionPayload):
    tts_service.session_manager.init_session_path(sessionPayload.path)
    return Response(f"Session path created at {sessionPayload.path}")

@app.get("/tts/language")
def get_languages():
    return JSONResponse(list(tts_service.langs.keys()),status_code=200)

@app.post("/tts/language")
def set_language(language: Language):
    tts_service.load_model(language.id)
    return Response(status_code=200)

if __name__ == "__main__":
    uvicorn.run(app,host="0.0.0.0",port=8001)
