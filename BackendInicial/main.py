from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pyzeebe import create_insecure_channel, ZeebeClient
from dotenv import load_dotenv
from models import SolicitudReembolso
import os
import json
import asyncio
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener host y validar que no esté vacío
ZEEBE_HOST = os.getenv("ZEEBE_HOST", "localhost").strip()
if not ZEEBE_HOST:
    raise ValueError("La variable de entorno ZEEBE_HOST no puede estar vacía.")

# Obtener puerto y validar que sea entero válido
port_str = os.getenv("ZEEBE_PORT", "26500").strip()
try:
    ZEEBE_PORT = int(port_str)
    if not (1 <= ZEEBE_PORT <= 65535):
        raise ValueError()
except ValueError:
    raise ValueError(f"ZEEBE_PORT debe ser un entero válido entre 1 y 65535, got '{port_str}'.")

# Construir target y crear canal
target = f"{ZEEBE_HOST}:{ZEEBE_PORT}"
logger.info(f"Conectando a Zeebe en {target}")
channel = create_insecure_channel(target)

# Crear cliente Zeebe
zeebe_client = ZeebeClient(channel)

logger.info("Cliente Zeebe creado correctamente")

# Inicializar aplicación FastAPI
app = FastAPI()

# Middleware CORS (para desarrollo permite todos los orígenes, en producción restringir)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar a lista de dominios permitidos en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/reembolso")
async def enviar_reembolso(
    solicitud: str = Form(...),
    archivo: UploadFile = File(...)
):
    try:
        logger.info("Recibida solicitud de reembolso")

        # Convertir string JSON a dict
        try:
            data = json.loads(solicitud)
        except json.JSONDecodeError:
            logger.warning("Solicitud no es un JSON válido")
            raise HTTPException(status_code=422, detail="❌ La solicitud no es un JSON válido.")

        # Validar con Pydantic
        try:
            solicitud_obj = SolicitudReembolso(**data)
        except Exception as e:
            logger.warning(f"Validación fallida: {str(e)}")
            raise HTTPException(status_code=422, detail=f"❌ Validación fallida: {str(e)}")

        # Guardar archivo localmente
        os.makedirs("archivos", exist_ok=True)
        archivo_path = os.path.join("archivos", archivo.filename)
        with open(archivo_path, "wb") as f:
            contenido = await archivo.read()
            f.write(contenido)
        logger.info(f"Archivo guardado en {archivo_path}")

        # Preparar variables para Zeebe
        variables = solicitud_obj.dict(by_alias=True)
        variables["archivoNombre"] = archivo.filename
        logger.info(f"Variables para Zeebe: {variables}")

        # Ejecutar proceso en Zeebe con timeout para evitar bloqueo indefinido
        try:
            await asyncio.wait_for(
                zeebe_client.run_process(
                    bpmn_process_id="Process_1bag78u",
                    variables=variables
                ),
                timeout=15  # segundos
            )
            logger.info("Proceso enviado a Zeebe con éxito")
        except asyncio.TimeoutError:
            logger.error("Timeout al conectar con Zeebe")
            raise HTTPException(status_code=504, detail="Timeout al conectar con Zeebe")
        except Exception as e:
            logger.error(f"Error al enviar proceso a Zeebe: {e}")
            raise HTTPException(status_code=500, detail=f"Error al enviar proceso a Zeebe: {e}")

        return JSONResponse(
            status_code=200,
            content={"mensaje": "✅ Reembolso enviado correctamente a Zeebe local."}
        )

    except HTTPException as he:
        raise he

    except Exception as e:
        logger.error(f"Error inesperado en servidor: {e}")
        raise HTTPException(status_code=500, detail=f"⚠️ Error inesperado del servidor: {str(e)}")
