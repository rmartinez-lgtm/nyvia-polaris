# Nyvia Polaris — RAG interno de Nyvia

Nyvia Polaris es una herramienta RAG (Retrieval-Augmented Generation) para consultar conocimiento interno de Nyvia en lenguaje natural. El sistema indexa documentos Markdown, genera embeddings con Voyage AI, guarda vectores y metadata en Qdrant, recupera chunks relevantes por pregunta y genera respuestas con Claude/Anthropic citando fuentes.

> Estado de este README: documenta el estado actual observado en el repositorio y agrega pasos operativos para que otro empleado pueda correr, mantener y replicar Polaris. Las secciones marcadas como **Pendiente de validar** deben confirmarse en las cuentas de Nyvia, Railway, Lovable, Supabase y Qdrant antes de producción.

---

## Tabla de contenidos

1. [Resumen ejecutivo](#resumen-ejecutivo)
2. [Arquitectura](#arquitectura)
3. [Stack y servicios](#stack-y-servicios)
4. [Cuentas, costos y límites](#cuentas-costos-y-límites)
5. [Estructura del proyecto](#estructura-del-proyecto)
6. [Variables de entorno](#variables-de-entorno)
7. [Setup local desde cero](#setup-local-desde-cero)
8. [Arranque diario](#arranque-diario)
9. [Flujo RAG paso a paso](#flujo-rag-paso-a-paso)
10. [Indexación de documentos](#indexación-de-documentos)
11. [API](#api)
12. [Frontend](#frontend)
13. [Supabase Auth y seguridad](#supabase-auth-y-seguridad)
14. [Deployment en Railway](#deployment-en-railway)
15. [Qdrant](#qdrant)
16. [Lovable](#lovable)
17. [Google Analytics en Nyvia OS](#google-analytics-en-nyvia-os)
18. [Pruebas de usuario](#pruebas-de-usuario)
19. [Handoff y transferencia a Nyvia](#handoff-y-transferencia-a-nyvia)
20. [Claude Code](#claude-code)
21. [Troubleshooting](#troubleshooting)
22. [Roadmap y pendientes](#roadmap-y-pendientes)

---

## Resumen ejecutivo

Polaris funciona así:

1. El usuario hace una pregunta desde el frontend.
2. El frontend envía la pregunta al backend FastAPI.
3. El backend convierte la pregunta en embedding usando Voyage AI.
4. El backend consulta Qdrant con ese vector y filtros opcionales.
5. Qdrant devuelve los chunks más relevantes con metadata.
6. El backend arma un prompt con contexto recuperado.
7. Claude genera una respuesta basada en esos chunks.
8. El backend devuelve respuesta, fuentes, scores y `trace_id`.
9. El frontend muestra la respuesta, fuentes y botones de feedback.
10. Langfuse registra trazas de embeddings, retrieval, generación y feedback.

---

## Arquitectura

```text
Usuario
  |
  v
Frontend Next.js / Nyvia OS / Lovable
  |
  | POST /api/backend/chat/
  v
Backend FastAPI
  |
  |-- embed_query(question)
  |     |-- Voyage AI: voyage-3-large
  |
  |-- search(vector, top_k, filters)
  |     |-- Qdrant: colección nyvia_brain
  |
  |-- ask(question, chunks)
  |     |-- Anthropic Claude
  |
  |-- Langfuse trace + feedback
  v
Respuesta con fuentes
```

### Componentes principales

| Componente | Rol |
|---|---|
| `backend/main.py` | Inicializa FastAPI, CORS, routers y healthcheck. |
| `backend/config.py` | Lee variables de entorno con `pydantic-settings`. |
| `backend/routers/chat.py` | Expone `/chat/` y `/chat/feedback`. |
| `backend/routers/eval.py` | Expone evaluación automática del RAG. |
| `backend/services/embeddings.py` | Genera embeddings con Voyage AI. |
| `backend/services/vector_store.py` | Crea colección, upsert, delete y búsqueda en Qdrant. |
| `backend/services/llm.py` | Llama a Claude y aplica el system prompt de Nyvia. |
| `scripts/index_documents.py` | Indexa documentos Markdown en Qdrant. |
| `docs/*.md` | Fuente de conocimiento que se convierte a chunks. |
| `frontend/app/components/Chat.tsx` | UI de chat, fuentes y feedback. |

---

## Stack y servicios

| Capa | Tecnología actual |
|---|---|
| Backend API | FastAPI + Uvicorn |
| LLM | Anthropic Claude |
| Embeddings | Voyage AI |
| Vector DB | Qdrant local o Qdrant Cloud |
| Frontend | Next.js 14 + React + Tailwind + TypeScript |
| Observabilidad | Langfuse |
| Auth | Supabase, pendiente de cerrar implementación productiva |
| Hosting | Railway |
| Frontend asistido | Lovable, pendiente documentar flujo exacto |
| Analytics | Google Analytics en Nyvia OS, pendiente |

> Nota: el README anterior mencionaba OpenAI (`gpt-4o` y `text-embedding-3-small`). El código actual usa Anthropic y Voyage AI. Este README ya refleja el estado actual del código.

---

## Cuentas, costos y límites

| Servicio | Cuenta | Límite / alerta | Uso en Polaris | Estado |
|---|---|---:|---|---|
| Claude API / Anthropic | `tech@nyvia.mx` | Máximo 30 USD, threshold 25 USD | Generación de respuestas | Configurado por variable `ANTHROPIC_API_KEY` |
| Voyage AI | `tech@nyvia.mx` | Threshold 20 USD | Embeddings de documentos y preguntas | Configurado por variable `VOYAGE_API_KEY` |
| Railway | `tech@nyvia.mx` | Hard limit 30 USD, email alert 25 USD | Hosting backend/app | Migrado desde cuenta personal a Nyvia; validar workspace final |
| Qdrant | Cuenta de Nyvia | Sin spend limit configurable detectado | Vector DB | Validar tamaño de cluster |
| Supabase | Cuenta de Nyvia | Pendiente | Auth y posible memoria | Pendiente validar 2FA/RLS |
| Langfuse | Cuenta de Nyvia o equipo | Pendiente | Observabilidad y feedback | Validar ownership |
| Lovable | Cuenta de Nyvia o equipo | Pendiente | Frontend asistido | Validar conexión GitHub |

### Nota sobre Qdrant

Qdrant no cobra principalmente por query, sino por infraestructura asignada: vCPU, RAM y disco del cluster. Por eso el costo mensual suele ser fijo y predecible según el tamaño del cluster, aunque haga pocas o muchas consultas. Revisar periódicamente el tamaño del cluster y si está sobredimensionado.

---

## Estructura del proyecto

```text
nyvia-polaris/
├── README.md
├── docker-compose.yml
├── ARRANQUE.md
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── routers/
│   │   ├── chat.py
│   │   └── eval.py
│   └── services/
│       ├── embeddings.py
│       ├── evaluator.py
│       ├── llm.py
│       └── vector_store.py
│
├── frontend/
│   ├── package.json
│   └── app/
│       ├── page.tsx
│       ├── layout.tsx
│       └── components/
│           ├── Chat.tsx
│           └── Eval.tsx
│
├── scripts/
│   └── index_documents.py
│
└── docs/
    └── *.md
```

---

## Variables de entorno

Crear `backend/.env` localmente. No subir este archivo a GitHub.

```env
# Anthropic / Claude
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-opus-4-8
JUDGE_MODEL=claude-haiku-4-5-20251001

# Voyage AI
VOYAGE_API_KEY=
EMBEDDING_MODEL=voyage-3-large
EMBEDDING_DIM=1024

# Qdrant
QDRANT_URL=
QDRANT_API_KEY=
QDRANT_COLLECTION=nyvia_brain

# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# Langfuse
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Variables importantes

| Variable | Descripción |
|---|---|
| `ANTHROPIC_API_KEY` | Llave para llamar Claude. |
| `ANTHROPIC_MODEL` | Modelo usado para responder. |
| `JUDGE_MODEL` | Modelo usado para evaluación automática. |
| `VOYAGE_API_KEY` | Llave para generar embeddings. |
| `EMBEDDING_MODEL` | Modelo de embeddings. Actualmente `voyage-3-large`. |
| `EMBEDDING_DIM` | Dimensión del vector. Debe coincidir con Qdrant. Actualmente `1024`. |
| `QDRANT_URL` | URL de Qdrant Cloud. Vacío usa almacenamiento local `./qdrant_data`. |
| `QDRANT_API_KEY` | API key de Qdrant Cloud. |
| `QDRANT_COLLECTION` | Nombre de colección. Default `nyvia_brain`. |
| `SUPABASE_URL` | URL del proyecto Supabase. |
| `SUPABASE_SERVICE_KEY` | Llave server-side. No exponer en frontend. |
| `LANGFUSE_*` | Trazabilidad, métricas y feedback. |

> Check técnico: confirmar que `backend/requirements.txt` incluya `anthropic` y `voyageai`. El código actual importa ambos paquetes, así que deben estar instalados en local y en Railway.

---

## Setup local desde cero

### 1. Clonar el repositorio

```bash
git clone https://github.com/rmartinez-lgtm/nyvia-polaris.git
cd nyvia-polaris
```

### 2. Crear archivo de variables

```bash
cd backend
cp .env.example .env  # si existe
```

Si no existe `.env.example`, crear `backend/.env` manualmente usando la sección [Variables de entorno](#variables-de-entorno).

### 3. Crear ambiente Python

Windows:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install anthropic voyageai
```

macOS/Linux:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install anthropic voyageai
```

### 4. Instalar frontend

```bash
cd ../frontend
npm install
```

### 5. Levantar Qdrant local

Desde la raíz del repo:

```bash
docker-compose up -d
```

Verificar dashboard local:

```text
http://localhost:6333/dashboard
```

### 6. Indexar documentos

```bash
cd backend
venv\Scripts\activate  # Windows
python ../scripts/index_documents.py
```

macOS/Linux:

```bash
cd backend
source venv/bin/activate
python ../scripts/index_documents.py
```

### 7. Correr backend

```bash
cd backend
uvicorn main:app --reload
```

Backend:

```text
http://localhost:8000
```

Docs API:

```text
http://localhost:8000/docs
```

Healthcheck:

```text
http://localhost:8000/health
```

### 8. Correr frontend

```bash
cd frontend
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

## Arranque diario

Abrir tres terminales.

### Terminal 1 — Qdrant

```bash
docker-compose up -d
```

### Terminal 2 — Backend

```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload
```

### Terminal 3 — Frontend

```bash
cd frontend
npm run dev
```

---

## Flujo RAG paso a paso

### Paso 1 — Usuario pregunta

El usuario escribe una pregunta en el frontend. El componente `Chat.tsx` envía:

```json
{
  "question": "¿Qué servicios ofrece Nyvia?"
}
```

a:

```text
POST /api/backend/chat/
```

### Paso 2 — Backend valida la pregunta

`backend/routers/chat.py` valida que `question` no esté vacío. Si está vacío, responde 400.

### Paso 3 — Embedding de la pregunta

`embed_query()` convierte la pregunta en vector usando Voyage AI con `input_type="query"`.

### Paso 4 — Retrieval en Qdrant

`search()` busca en Qdrant usando:

- colección `nyvia_brain` por default,
- distancia coseno,
- `top_k`,
- filtros opcionales,
- payload completo.

### Paso 5 — Filtrado por score

El router aplica:

```python
MIN_SCORE = 0.25
HIGH_SCORE = 0.55
```

- Chunks debajo de `0.25` se descartan.
- Si ningún chunk supera `0.55`, la respuesta se marca como baja confianza.

### Paso 6 — Construcción de contexto

`ask()` concatena chunks así:

```text
[Fuente: nombre_fuente]
texto del chunk

---

[Fuente: otra_fuente]
texto del chunk
```

### Paso 7 — Respuesta con Claude

Claude recibe:

- system prompt de Nyvia,
- contexto recuperado,
- pregunta original.

Reglas clave del prompt:

- responder con base en el contexto,
- citar fuentes con `[Fuente: nombre_archivo]`,
- indicar cuando la información es parcial,
- no inventar si no hay contexto suficiente,
- responder en el idioma de la pregunta.

### Paso 8 — Respuesta al frontend

El backend devuelve:

```json
{
  "answer": "Respuesta generada...",
  "sources": [
    {
      "source": "DST-202605-001",
      "score": 0.9124,
      "text": "Fragmento del chunk..."
    }
  ],
  "trace_id": "..."
}
```

### Paso 9 — Feedback

El frontend permite enviar feedback útil/no útil a:

```text
POST /chat/feedback
```

Langfuse guarda el score `user-feedback` ligado al `trace_id`.

---

## Indexación de documentos

Los documentos fuente viven en `docs/` como Markdown.

### Comando

```bash
cd backend
python ../scripts/index_documents.py
```

### Qué hace el script

1. Busca archivos `docs/**/*.md`.
2. Lee frontmatter o metadata al inicio del archivo.
3. Extrae campos como `source`, `client`, `dimension`, `date`, `nda_level`.
4. Divide el contenido por secciones `##` y `###`.
5. Si una sección es larga, la parte en chunks de 1200 caracteres con overlap de 200.
6. Genera embeddings en batches de 8 usando Voyage AI.
7. Borra y recrea la colección en Qdrant.
8. Inserta chunks con vector + payload.

### Parámetros actuales

| Parámetro | Valor |
|---|---:|
| `CHUNK_SIZE` | 1200 caracteres |
| `CHUNK_OVERLAP` | 200 caracteres |
| `BATCH_SIZE` | 8 chunks |
| `RETRY_SLEEP` | 22 segundos |
| Mínimo de chunk | 50 caracteres |
| Distancia vectorial | Cosine |
| Dimensión | 1024 |

### Formato recomendado de documento

```markdown
---
source: DST-202605-001
client: nyvia_interno
dimension: estrategia
date: 2026-05-01
nda_level: bajo
organization: nyvia
project: polaris
---

## Tema principal

Contenido del documento...
```

### Metadata actual indexada

El script actual guarda:

| Campo | Fuente |
|---|---|
| `source` | `source`, `destilado_id` o nombre del archivo |
| `client` | `client` o `nyvia_interno` |
| `dimension` | `dimension`, `tipo_fuente` o `general` |
| `date` | `date`, `fecha_creacion` o vacío |
| `nda_level` | `nda_level` o `bajo` |
| `text` | texto del chunk |

### Metadata recomendada para multi-organización y multi-proyecto

Para cumplir el objetivo de etiquetas por proyecto y organización, agregar y filtrar también:

```yaml
organization_id: nyvia
organization_name: Nyvia
project_id: polaris
project_name: Nyvia Polaris
visibility: internal
```

Luego actualizar `scripts/index_documents.py` para guardar esos campos en Qdrant y actualizar frontend/backend para mandarlos como filtros.

---

## API

### `GET /health`

Verifica que el backend esté vivo.

```json
{
  "status": "ok",
  "service": "nyvia-brain"
}
```

### `POST /chat/`

Responde una pregunta usando RAG.

Request:

```json
{
  "question": "¿Cuáles son los servicios de Nyvia?",
  "top_k": 8,
  "filters": {
    "client": "nyvia_interno",
    "dimension": "estrategia"
  }
}
```

Response:

```json
{
  "answer": "Nyvia ofrece... [Fuente: DST-202605-001]",
  "sources": [
    {
      "source": "DST-202605-001",
      "score": 0.9124,
      "text": "Fragmento del chunk..."
    }
  ],
  "trace_id": "..."
}
```

### `POST /chat/feedback`

Guarda feedback de usuario en Langfuse.

Request:

```json
{
  "trace_id": "...",
  "value": 1
}
```

Valores:

| Valor | Significado |
|---:|---|
| `1` | Útil |
| `0` | No útil |

### `POST /eval/`

Evalúa calidad de respuesta RAG con LLM-as-Judge.

Request:

```json
{
  "question": "¿Cuáles son los pilares de la metodología?",
  "top_k": 5
}
```

---

## Frontend

El frontend actual está en `frontend/` y usa Next.js 14.

### Comandos

```bash
cd frontend
npm install
npm run dev
npm run build
npm run start
```

### Comportamiento actual del chat

- Muestra título `Nyvia Polaris`.
- Permite escribir preguntas.
- Envía preguntas a `/api/backend/chat/`.
- Muestra respuestas en Markdown.
- Muestra fuentes con score de relevancia.
- Permite feedback útil/no útil si existe `trace_id`.

### Pendiente recomendado

Agregar selector o etiqueta visible para:

- organización,
- proyecto,
- ambiente (`dev`, `staging`, `prod`),
- usuario autenticado.

Ejemplo UX:

```text
Organización: Nyvia    Proyecto: Polaris    Ambiente: Producción
```

Esto ayuda a evitar errores de uso, especialmente cuando Polaris se replique para otros equipos o clientes.

---

## Supabase Auth y seguridad

Supabase aparece en configuración y dependencias, pero se debe validar el flujo productivo completo.

### Objetivo

- Solo usuarios autenticados pueden acceder a Polaris.
- Cada usuario pertenece a una organización.
- Cada pregunta consulta solo documentos permitidos para esa organización/proyecto.
- La memoria no se mezcla entre usuarios ni organizaciones.

### Checklist de Supabase

- [ ] Confirmar método de login: email/password, magic link, Google OAuth u otro.
- [ ] Confirmar si Supabase Auth está aplicado en frontend.
- [ ] Confirmar si backend valida JWT de Supabase.
- [ ] Confirmar si existe tabla `profiles` o equivalente.
- [ ] Confirmar si existe tabla `organizations`.
- [ ] Confirmar si existe tabla `projects`.
- [ ] Confirmar si existe relación usuario-organización.
- [ ] Activar Row Level Security donde aplique.
- [ ] Evitar usar `SUPABASE_SERVICE_KEY` en frontend.
- [ ] Validar si 2FA/MFA aplica al plan y flujo actual.

### 2FA / MFA

Pendiente de validar en Supabase:

- Si el plan actual permite MFA.
- Si se usará TOTP/autenticador.
- Si todos los usuarios estarán obligados a configurarlo.
- Qué hacer con usuarios que pierdan acceso.
- Cómo documentar recuperación de cuenta.

---

## Deployment en Railway

Railway se usa para hosting. La cuenta debe estar bajo `tech@nyvia.mx` o workspace oficial de Nyvia.

### Variables en Railway

Configurar las mismas variables de `backend/.env` en Railway:

```env
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-opus-4-8
JUDGE_MODEL=claude-haiku-4-5-20251001
VOYAGE_API_KEY=
EMBEDDING_MODEL=voyage-3-large
EMBEDDING_DIM=1024
QDRANT_URL=
QDRANT_API_KEY=
QDRANT_COLLECTION=nyvia_brain
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Checklist Railway

- [ ] Proyecto está en cuenta/workspace de Nyvia.
- [ ] Billing está en `tech@nyvia.mx`.
- [ ] Hard limit: 30 USD.
- [ ] Email alert: 25 USD.
- [ ] Variables de entorno están configuradas.
- [ ] Deploy usa rama correcta.
- [ ] Dominio público apunta al servicio correcto.
- [ ] Healthcheck `/health` responde OK.
- [ ] Logs no imprimen secretos.

### Comando de arranque esperado

Para backend:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Validar si Railway detecta correctamente carpeta `backend/`. Si no, configurar root directory o start command.

---

## Qdrant

Qdrant guarda vectores y metadata de chunks.

### Local

Si `QDRANT_URL` está vacío, el código usa:

```python
QdrantClient(path="./qdrant_data")
```

También existe `docker-compose.yml`, pero el código actual usa path local si no hay `QDRANT_URL`. Validar si se quiere estandarizar desarrollo local con Docker (`http://localhost:6333`) o con storage local `./qdrant_data`.

### Cloud

Para Qdrant Cloud, configurar:

```env
QDRANT_URL=https://...
QDRANT_API_KEY=...
```

### Colección

Default:

```env
QDRANT_COLLECTION=nyvia_brain
```

Configuración esperada:

| Campo | Valor |
|---|---|
| Distance | Cosine |
| Vector size | 1024 |
| Payload index actual | `source` |

### Filtros

El backend acepta filtros dinámicos:

```json
{
  "filters": {
    "client": "nyvia_interno",
    "dimension": "estrategia"
  }
}
```

Recomendado crear índices de payload también para:

- `client`,
- `dimension`,
- `nda_level`,
- `organization_id`,
- `project_id`.

---

## Lovable

Pendiente de documentar el flujo exacto usado en Lovable. Mientras tanto, este es el proceso recomendado para replicarlo.

### Proceso recomendado

1. Crear o abrir proyecto en Lovable.
2. Conectar Lovable al repositorio oficial de Nyvia, no a una cuenta personal.
3. Confirmar rama de trabajo.
4. Pedir a Lovable cambios de frontend únicamente, evitando tocar backend salvo que se revise manualmente.
5. Conectar llamadas del frontend a la API publicada en Railway.
6. Confirmar que variables públicas no exponen secretos.
7. Exportar/sincronizar cambios a GitHub.
8. Revisar diff en PR antes de merge.
9. Deploy desde rama aprobada.

### Prompt base para Lovable

```text
Estamos construyendo Nyvia Polaris, una interfaz interna para consultar un RAG.
Necesitamos un frontend claro, profesional y seguro.
Debe:
- mostrar nombre del producto: Nyvia Polaris,
- permitir login con Supabase,
- mostrar organización y proyecto actual,
- tener chat con historial visual,
- mostrar fuentes recuperadas con score,
- permitir feedback útil/no útil,
- no exponer API keys,
- consumir el backend mediante una variable pública de URL o proxy seguro.
```

### Pendiente de validar

- [ ] Cuenta Lovable propietaria: Nyvia o `tech@nyvia.mx`.
- [ ] Repo conectado: organización de Nyvia.
- [ ] Rama usada por Lovable.
- [ ] Variables frontend usadas para backend.
- [ ] Si Lovable pisa archivos manuales.
- [ ] Proceso de PR/review antes de producción.

---

## Google Analytics en Nyvia OS

Pendiente de implementar o validar.

### Objetivo

Medir uso básico de Nyvia OS / Polaris:

- visitas,
- usuarios activos,
- páginas más usadas,
- eventos de pregunta enviada,
- feedback útil/no útil,
- errores de frontend.

### Recomendación de eventos

| Evento | Cuándo se dispara |
|---|---|
| `polaris_chat_question_sent` | Usuario envía pregunta |
| `polaris_answer_received` | Backend responde OK |
| `polaris_answer_error` | Backend responde error |
| `polaris_source_opened` | Usuario abre detalle de fuente |
| `polaris_feedback_submitted` | Usuario da útil/no útil |
| `polaris_project_changed` | Usuario cambia proyecto |
| `polaris_org_changed` | Usuario cambia organización |

### Privacidad

No enviar texto completo de preguntas a Google Analytics si contienen información interna o confidencial. Enviar solo metadata no sensible como longitud de pregunta, proyecto, ambiente y resultado.

---

## Pruebas de usuario

### Caso 1 — Login

- [ ] Usuario puede iniciar sesión.
- [ ] Usuario no autenticado no puede entrar a Polaris.
- [ ] Sesión persiste al recargar.
- [ ] Logout funciona.
- [ ] Usuario bloqueado/no autorizado no puede acceder.

### Caso 2 — Pregunta básica

- [ ] Usuario pregunta algo cubierto por documentos.
- [ ] Polaris responde con información útil.
- [ ] Polaris muestra fuentes.
- [ ] Las fuentes corresponden a documentos reales.
- [ ] La respuesta incluye citas `[Fuente: ...]`.

### Caso 3 — Pregunta sin información

- [ ] Usuario pregunta algo fuera de la base.
- [ ] Polaris responde que no tiene información.
- [ ] Polaris no inventa.
- [ ] No muestra fuentes irrelevantes.

### Caso 4 — Filtros por proyecto y organización

- [ ] Usuario ve organización actual.
- [ ] Usuario ve proyecto actual.
- [ ] Pregunta se filtra por proyecto correcto.
- [ ] Pregunta se filtra por organización correcta.
- [ ] No hay fuga de documentos entre organizaciones.

### Caso 5 — Feedback

- [ ] Usuario puede marcar respuesta como útil.
- [ ] Usuario puede marcar respuesta como no útil.
- [ ] Feedback se registra en Langfuse.
- [ ] Feedback no rompe el chat si Langfuse falla.

### Caso 6 — Memoria

- [ ] Polaris mantiene contexto útil dentro de una conversación.
- [ ] Memoria no se mezcla entre usuarios.
- [ ] Memoria no se mezcla entre organizaciones.
- [ ] Usuario puede entender qué contexto se está usando.

---

## Handoff y transferencia a Nyvia

### GitHub

- [ ] Transferir repo desde `rmartinez-lgtm/nyvia-polaris` a la organización de Nyvia.
- [ ] Confirmar owners/admins de Nyvia.
- [ ] Proteger rama principal.
- [ ] Requerir PR para cambios.
- [ ] Configurar secrets si se usa GitHub Actions.
- [ ] Actualizar URLs en README después de la transferencia.

### Railway

- [ ] Confirmar que Railway está en cuenta/workspace de Nyvia.
- [ ] Confirmar que billing ya no depende de cuenta personal.
- [ ] Confirmar límites de gasto.
- [ ] Confirmar variables de entorno.
- [ ] Confirmar dominio productivo.

### APIs y servicios

- [ ] Anthropic/Claude bajo `tech@nyvia.mx`.
- [ ] Voyage AI bajo `tech@nyvia.mx`.
- [ ] Qdrant bajo cuenta de Nyvia.
- [ ] Supabase bajo cuenta de Nyvia.
- [ ] Langfuse bajo cuenta de Nyvia.
- [ ] Lovable bajo cuenta de Nyvia.
- [ ] Google Analytics bajo cuenta de Nyvia.

---

## Claude Code

Claude Code fue y debe seguir siendo una herramienta clave para mantener y replicar Polaris, porque puede trabajar directamente sobre el repositorio, entender dependencias, modificar archivos y generar documentación técnica.

### Casos de uso recomendados

- Entender arquitectura del repo.
- Detectar variables de entorno faltantes.
- Crear scripts de ingesta.
- Refactorizar endpoints.
- Revisar fugas de datos entre organizaciones.
- Agregar pruebas.
- Generar documentación.
- Revisar PRs.
- Migrar de cuenta personal a cuenta empresa.

### Prompt recomendado para Claude Code

```text
Revisa este repositorio de Nyvia Polaris y explícame la arquitectura real del RAG.
Identifica:
1. dónde se generan embeddings,
2. dónde se consulta Qdrant,
3. dónde se llama a Claude,
4. dónde se maneja auth,
5. dónde se guarda memoria,
6. qué variables de entorno faltan documentar,
7. riesgos para multi-tenant por organización/proyecto,
8. cambios mínimos para que otra persona pueda replicar el sistema.

Después propón cambios archivo por archivo y crea una checklist de pruebas.
```

---

## Troubleshooting

### Error: `ModuleNotFoundError: anthropic` o `ModuleNotFoundError: voyageai`

Instalar dependencias:

```bash
cd backend
pip install anthropic voyageai
```

Y agregar a `backend/requirements.txt` si falta.

### Error: colección Qdrant no existe

Correr indexación:

```bash
cd backend
python ../scripts/index_documents.py
```

### Error: dimensión de vector incorrecta

Verificar que coincidan:

```env
EMBEDDING_MODEL=voyage-3-large
EMBEDDING_DIM=1024
```

Si se cambia de modelo, borrar/recrear colección.

### Polaris responde “No tengo esa información...” aunque sí existe

Revisar:

- documento está en `docs/`,
- documento es `.md`,
- se corrió indexación después de agregarlo,
- metadata/filtros no excluyen el documento,
- score mínimo no está descartando chunks útiles,
- el chunk tiene suficiente contexto.

### CORS en producción

Actualmente CORS está abierto con `allow_origins=["*"]`. Antes de producción, restringir a dominios de Nyvia.

---

## Roadmap y pendientes

### Críticos

- [ ] Transferir repo a organización de Nyvia.
- [ ] Confirmar ownership de Railway, Qdrant, Supabase, Langfuse, Lovable, Anthropic y Voyage.
- [ ] Agregar `anthropic` y `voyageai` a `backend/requirements.txt` si no están.
- [ ] Restringir CORS en producción.
- [ ] Validar auth real de Supabase en frontend y backend.
- [ ] Validar RLS / permisos por organización.
- [ ] Agregar filtros por `organization_id` y `project_id`.
- [ ] Agregar etiqueta visual de organización y proyecto.

### Importantes

- [ ] Validar 2FA/MFA en Supabase.
- [ ] Agregar Google Analytics sin enviar información sensible.
- [ ] Documentar flujo exacto de Lovable.
- [ ] Documentar deployment real de Railway.
- [ ] Crear `.env.example`.
- [ ] Crear pruebas automatizadas de API.
- [ ] Crear dataset de evaluación para preguntas frecuentes.

### Mejoras futuras

- [ ] Ingesta desde UI.
- [ ] Ingesta incremental por archivo.
- [ ] Borrado por fuente sin full re-index.
- [ ] Historial persistente de conversaciones.
- [ ] Memoria por usuario/proyecto.
- [ ] Dashboard de calidad con Langfuse.
- [ ] Panel admin para documentos y permisos.
