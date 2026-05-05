# Nyvia Brain — Guía de Arranque (Día 3)

## 1. Instalar herramientas (una sola vez)

### Docker Desktop
Descarga e instala desde: https://www.docker.com/products/docker-desktop/
Reinicia el equipo después de instalar.

### Python 3.11
Descarga desde: https://www.python.org/downloads/
Durante la instalación, marca "Add Python to PATH".

### Node.js 20 LTS
Descarga desde: https://nodejs.org/

---

## 2. Configurar credenciales

Edita el archivo `backend/.env` y pon tus claves reales:
- ANTHROPIC_API_KEY → tu clave de https://console.anthropic.com
- VOYAGE_API_KEY    → tu clave de https://dash.voyageai.com
- SUPABASE_URL      → URL de tu proyecto en https://supabase.com
- SUPABASE_SERVICE_KEY → clave de servicio de Supabase

---

## 3. Levantar Qdrant (base de vectores)

Abre una terminal en la carpeta raíz del proyecto:
```
docker-compose up -d
```
Verifica en: http://localhost:6333/dashboard

---

## 4. Instalar y arrancar el Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```
El backend queda en: http://localhost:8000
Documentación automática: http://localhost:8000/docs

---

## 5. Indexar el primer documento

Con el backend corriendo (o al menos con el .env cargado):
```bash
cd backend
python ../scripts/index_documents.py
```
Esto indexa todos los .md de la carpeta /docs en Qdrant.

---

## 6. Arrancar el Frontend

```bash
cd frontend
npm install
npm run dev
```
La app queda en: http://localhost:3000

---

## 7. Probar el sistema completo

1. Abre http://localhost:3000
2. Escribe: "¿Cuáles son los servicios de Nyvia?"
3. Deberías recibir una respuesta basada en nyvia_intro.md con citas.

---

## Estructura del proyecto

```
KM Polaris/
├── docker-compose.yml      ← Qdrant
├── backend/
│   ├── main.py             ← FastAPI entry point
│   ├── config.py           ← Variables de entorno
│   ├── .env                ← Credenciales (NO subir a git)
│   ├── requirements.txt
│   ├── routers/chat.py     ← Endpoint POST /chat/
│   └── services/
│       ├── embeddings.py   ← Voyage AI
│       ├── vector_store.py ← Qdrant
│       └── llm.py          ← Anthropic (Claude)
├── frontend/
│   └── app/
│       ├── page.tsx        ← Página principal
│       └── components/Chat.tsx ← Interfaz de chat
├── scripts/
│   └── index_documents.py ← Indexador de Markdown
└── docs/
    └── nyvia_intro.md      ← Primer documento de prueba
```
