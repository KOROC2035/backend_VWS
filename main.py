from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import time
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Vision Web Studio API")

# Configuration CORS pour autoriser uniquement ton frontend Vercel à appeler cette API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # L'étoile accepte TOUTES les URLs (Vercel principal, Vercel de test, Localhost)
    allow_credentials=False, # DOIT IMPÉRATIVEMENT ÊTRE SUR "False" QUAND ON UTILISE "*"
    allow_methods=["*"], # Accepte toutes les méthodes (POST, GET, OPTIONS, etc.)
    allow_headers=["*"], # Accepte tous les headers
)

META_PIXEL_ID = os.getenv("META_PIXEL_ID")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

@app.post("/api/track-whatsapp")
async def track_whatsapp_click(
    request: Request, 
    user_agent: str = Header(None, alias="User-Agent"),
    x_forwarded_for: str = Header(None, alias="X-Forwarded-For")
):
    # Récupération de l'IP du client (gestion des proxys)
    client_ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.client.host

    payload = {
        "data": [
            {
                "event_name": "Contact",
                "event_time": int(time.time()),
                "action_source": "website",
                "event_source_url": str(request.url),
                "user_data": {
                    "client_ip_address": client_ip,
                    "client_user_agent": user_agent,
                }
            }
        ]
    }

    url = f"https://graph.facebook.com/v19.0/{META_PIXEL_ID}/events?access_token={META_ACCESS_TOKEN}"

    # Appel asynchrone à l'API Meta
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return {"status": "success", "meta_response": response.json()}
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail="Erreur avec l'API Meta")
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Erreur serveur interne")