# Handoff operativo — Nyvia Polaris

Este documento es el runbook detallado para transferir, replicar y operar Nyvia Polaris. Está pensado para que una persona nueva del equipo pueda entender qué existe, qué falta validar y cómo levantar el RAG sin depender de conocimiento oral.

---

## 1. Objetivo del handoff

Nyvia Polaris debe quedar listo para que:

1. El repositorio sea propiedad de Nyvia.
2. Railway, Qdrant, Supabase, Anthropic, Voyage, Lovable y Langfuse estén en cuentas de Nyvia.
3. Cualquier empleado técnico pueda levantar localmente el proyecto.
4. Cualquier empleado autorizado pueda usar Polaris de forma segura.
5. El equipo pueda replicar la arquitectura para otros proyectos/organizaciones.
6. El equipo tenga pruebas de usuario para validar que el RAG funciona.

---

## 2. Estado actual detectado en el repo

Repositorio actual:

```text
rmartinez-lgtm/nyvia-polaris
```

Rama principal:

```text
master
```

Estado técnico observado:

| Área | Estado |
|---|---|
| Backend | FastAPI |
| Frontend | Next.js 14 |
| Embeddings | Voyage AI |
| LLM | Anthropic Claude |
| Vector DB | Qdrant |
| Docs fuente | Markdown en `docs/` |
| Observabilidad | Langfuse |
| Feedback | Endpoint `/chat/feedback` |
| Auth | Supabase aparece en dependencias/config, implementación productiva pendiente de validar |
| Multi-proyecto | Parcial: filtros dinámicos existen, pero falta metadata explícita de organización/proyecto |
| Deployment | Railway, pendiente documentar configuración real |
| Lovable | Pendiente documentar flujo exacto |

---

## 3. Diagrama mental del sistema

```text
[Empleado]
   |
   v
[Frontend Next.js / Lovable / Nyvia OS]
   |
   | pregunta
   v
[FastAPI]
   |
   | 1. Genera embedding de pregunta
   v
[Voyage AI]
   |
   | vector
   v
[Qdrant]
   |
   | chunks relevantes + metadata
   v
[FastAPI]
   |
   | prompt con contexto
   v
[Claude]
   |
   | respuesta con fuentes
   v
[Frontend]
   |
   | feedback útil/no útil
   v
[Langfuse]
```

---

## 4. Replicar Polaris desde cero

### Paso 0 — Requisitos

Instalar:

- Git
- Python 3.11+
- Node.js 20 LTS
- Docker Desktop, si se usará Qdrant local
- Cuenta o acceso a Anthropic
- Cuenta o acceso a Voyage AI
- Cuenta o acceso a Qdrant
- Cuenta o acceso a Supabase
- Cuenta o acceso a Railway
- Cuenta o acceso a Langfuse

### Paso 1 — Clonar repo

```bash
git clone https://github.com/rmartinez-lgtm/nyvia-polaris.git
cd nyvia-polaris
```

Cuando se transfiera a Nyvia, actualizar URL:

```bash
git remote set-url origin https://github.com/<ORG_NYVIA>/nyvia-polaris.git
```

### Paso 2 — Crear APIs y llaves

Crear o conseguir:

```env
ANTHROPIC_API_KEY=
VOYAGE_API_KEY=
QDRANT_URL=
QDRANT_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

Nunca enviar llaves por Slack, email o README. Guardarlas en:

- Railway variables,
- `.env` local,
- password manager de Nyvia.

### Paso 3 — Preparar backend local

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install anthropic voyageai
```

Si estás en macOS/Linux:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install anthropic voyageai
```

### Paso 4 — Crear `backend/.env`

```env
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-opus-4-8
JUDGE_MODEL=claude-haiku-4-5-20251001

VOYAGE_API_KEY=...
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

### Paso 5 — Preparar frontend

```bash
cd ../frontend
npm install
```

### Paso 6 — Preparar documentos

Agregar archivos Markdown a `docs/`.

Formato recomendado:

```markdown
---
source: DST-202606-001
client: nyvia_interno
dimension: estrategia
date: 2026-06-10
nda_level: bajo
organization_id: nyvia
organization_name: Nyvia
project_id: polaris
project_name: Nyvia Polaris
---

## Resumen

Contenido del documento.
```

### Paso 7 — Indexar documentos

```bash
cd backend
python ../scripts/index_documents.py
```

Validar que la salida diga cuántos chunks indexó.

### Paso 8 — Correr backend

```bash
uvicorn main:app --reload
```

Abrir:

```text
http://localhost:8000/health
```

Debe responder:

```json
{"status":"ok","service":"nyvia-brain"}
```

### Paso 9 — Correr frontend

```bash
cd frontend
npm run dev
```

Abrir:

```text
http://localhost:3000
```

### Paso 10 — Probar pregunta

Preguntar algo que esté en `docs/`.

Validar:

- Responde con contenido relevante.
- Cita fuentes.
- Muestra fuentes desplegables.
- No inventa si no hay contexto.
- Feedback útil/no útil funciona.

---

## 5. Ingesta de documentos

### Cómo funciona hoy

El script `scripts/index_documents.py`:

1. Encuentra Markdown en `docs/`.
2. Lee frontmatter.
3. Parte por headers `##` y `###`.
4. Parte textos largos en chunks de 1200 caracteres.
5. Usa overlap de 200.
6. Genera embeddings con Voyage AI.
7. Borra la colección anterior.
8. Recrea la colección.
9. Inserta todos los chunks.

### Riesgo actual

La indexación actual es full re-index: borra y recrea todo. Esto es aceptable para una base pequeña, pero puede ser riesgoso en producción.

### Recomendación

Agregar dos modos:

```bash
python ../scripts/index_documents.py --full
python ../scripts/index_documents.py --source docs/nuevo_documento.md
```

El modo incremental debería:

1. Leer un archivo específico.
2. Detectar `source`.
3. Borrar solo puntos con ese `source`.
4. Insertar chunks nuevos.

---

## 6. Multi-organización y multi-proyecto

### Objetivo

Polaris debe soportar:

- varias organizaciones,
- varios proyectos por organización,
- permisos de usuario,
- aislamiento de documentos,
- etiquetas visibles de contexto.

### Metadata recomendada

Cada chunk debería tener:

```json
{
  "organization_id": "nyvia",
  "organization_name": "Nyvia",
  "project_id": "polaris",
  "project_name": "Nyvia Polaris",
  "source": "DST-202606-001",
  "client": "nyvia_interno",
  "dimension": "estrategia",
  "nda_level": "bajo",
  "date": "2026-06-10"
}
```

### Filtro obligatorio recomendado

El backend debería construir filtros desde el usuario autenticado, no confiar solo en lo que mande el frontend.

Ejemplo:

```python
filters = {
    "organization_id": current_user.organization_id,
    "project_id": selected_project_id,
}
```

### Riesgo

Si el frontend manda filtros manipulables, un usuario podría intentar consultar otra organización/proyecto. El backend debe validar permisos antes de consultar Qdrant.

---

## 7. Supabase Auth

### Decisiones que faltan

- Método de login: email/password, magic link, Google OAuth.
- Si se exigirá dominio `@nyvia.mx`.
- Si habrá roles.
- Si habrá admin panel.
- Si se usará MFA/2FA.
- Si backend validará JWT.

### Tablas recomendadas

```text
profiles
- id uuid primary key
- email text
- full_name text
- default_organization_id text
- role text

organizations
- id text primary key
- name text

projects
- id text primary key
- organization_id text
- name text

organization_members
- organization_id text
- user_id uuid
- role text

conversation_memory
- id uuid
- user_id uuid
- organization_id text
- project_id text
- summary text
- created_at timestamp
- updated_at timestamp
```

### Validación backend recomendada

Cada request a `/chat/` debería:

1. Recibir JWT de Supabase.
2. Validar JWT server-side.
3. Obtener usuario.
4. Obtener organizaciones/proyectos permitidos.
5. Construir filtros seguros.
6. Consultar Qdrant.

---

## 8. Memoria del RAG

El usuario mencionó que se le puso memoria al RAG. En este handoff falta confirmar dónde vive.

### Opciones posibles

| Opción | Ventaja | Riesgo |
|---|---|---|
| Memoria en frontend | Simple | Se pierde o puede manipularse |
| Memoria en Supabase | Persistente y auditable | Requiere diseño de permisos |
| Memoria en Qdrant | Útil para memoria semántica | Puede mezclarse si faltan filtros |
| Memoria en Langfuse | Buena para observabilidad | No debería ser fuente principal de producto |

### Recomendación

Guardar memoria en Supabase con llaves:

- `user_id`,
- `organization_id`,
- `project_id`,
- `conversation_id`.

Nunca usar memoria global sin filtros.

### Checklist memoria

- [ ] Identificar archivo donde se implementó memoria.
- [ ] Confirmar dónde se guarda.
- [ ] Confirmar si se separa por usuario.
- [ ] Confirmar si se separa por organización.
- [ ] Confirmar si se separa por proyecto.
- [ ] Agregar pruebas de no mezcla.

---

## 9. Railway

### Migración desde cuenta personal

Checklist:

- [ ] Proyecto Railway está en cuenta/workspace `tech@nyvia.mx` o Nyvia.
- [ ] Usuario personal ya no es owner único.
- [ ] Billing pertenece a Nyvia.
- [ ] Hard limit 30 USD activo.
- [ ] Alert 25 USD activo.
- [ ] Variables migradas.
- [ ] Dominio sigue funcionando.
- [ ] Deploy automático apunta a rama correcta.

### Variables mínimas

```env
ANTHROPIC_API_KEY=
VOYAGE_API_KEY=
QDRANT_URL=
QDRANT_API_KEY=
QDRANT_COLLECTION=nyvia_brain
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Pruebas post-migración

- [ ] `/health` responde.
- [ ] `/chat/` responde.
- [ ] Qdrant Cloud recibe queries.
- [ ] Claude responde.
- [ ] Voyage genera embeddings.
- [ ] Langfuse registra traces.
- [ ] Frontend llama URL correcta.

---

## 10. Lovable

### Qué debe quedar documentado

- Cuenta propietaria.
- Proyecto Lovable exacto.
- Repo conectado.
- Rama conectada.
- Cómo se exportan cambios a GitHub.
- Qué archivos toca Lovable.
- Qué variables usa.
- Cómo apunta a Railway.

### Flujo recomendado para no romper producción

1. Crear cambios en Lovable.
2. Exportar a rama nueva.
3. Abrir PR.
4. Revisar diff.
5. Probar local o staging.
6. Merge a rama principal.
7. Deploy.

### Regla importante

Lovable debe usarse principalmente para frontend. Cambios en backend, auth, permisos, Qdrant o variables deben pasar por revisión técnica manual.

---

## 11. Google Analytics en Nyvia OS

### Qué medir

- Uso de Polaris.
- Preguntas enviadas.
- Respuestas exitosas.
- Errores.
- Feedback.
- Cambio de proyecto/organización.

### Qué no medir

No enviar a Google Analytics:

- texto completo de preguntas,
- respuestas completas,
- nombres de clientes sensibles,
- contenido de documentos,
- API keys,
- emails si no es necesario.

### Eventos recomendados

```text
polaris_chat_question_sent
polaris_answer_received
polaris_answer_error
polaris_feedback_submitted
polaris_source_opened
polaris_project_changed
polaris_org_changed
```

---

## 12. Pruebas desde punto de vista usuario

### Prueba A — Usuario nuevo

1. Abrir app.
2. Intentar entrar sin login.
3. Confirmar que redirige a login.
4. Login exitoso.
5. Confirmar que ve organización/proyecto.
6. Preguntar algo básico.

Resultado esperado:

- Accede solo si está autorizado.
- Ve contexto correcto.
- Obtiene respuesta con fuentes.

### Prueba B — Usuario sin permisos

1. Login con usuario sin permisos a un proyecto.
2. Intentar consultar proyecto restringido.

Resultado esperado:

- No puede seleccionar proyecto.
- Backend rechaza request si intenta manipularlo.

### Prueba C — Pregunta cubierta

1. Preguntar algo que está en docs.
2. Revisar fuentes.
3. Abrir detalles.

Resultado esperado:

- Respuesta correcta.
- Fuentes correctas.
- Score razonable.

### Prueba D — Pregunta fuera de base

1. Preguntar algo inexistente.

Resultado esperado:

- Polaris dice que no tiene información.
- No inventa.

### Prueba E — Feedback

1. Marcar útil.
2. Revisar Langfuse.
3. Marcar no útil en otra respuesta.
4. Revisar Langfuse.

Resultado esperado:

- Feedback queda vinculado al trace.

### Prueba F — Memoria

1. Preguntar: “Estoy hablando del proyecto X”.
2. Preguntar seguimiento: “¿cuáles son sus riesgos?”.
3. Cambiar proyecto.
4. Preguntar algo similar.

Resultado esperado:

- La memoria ayuda dentro del mismo contexto.
- No mezcla proyectos.

---

## 13. Checklist para entregar al jefe

### Documentación

- [ ] README actualizado.
- [ ] Handoff creado.
- [ ] `.env.example` creado.
- [ ] Diagrama de arquitectura agregado.
- [ ] Flujo Lovable documentado.
- [ ] Flujo Railway documentado.

### Seguridad

- [ ] Repo en org de Nyvia.
- [ ] Secrets fuera de GitHub.
- [ ] CORS restringido.
- [ ] Supabase Auth validado.
- [ ] 2FA/MFA evaluado.
- [ ] Permisos por organización/proyecto probados.

### Producto

- [ ] Login funcional.
- [ ] Etiqueta organización/proyecto visible.
- [ ] Chat funcional.
- [ ] Fuentes visibles.
- [ ] Feedback funcional.
- [ ] Memoria probada.
- [ ] Analytics configurado.

### Operación

- [ ] Railway en cuenta Nyvia.
- [ ] Anthropic en `tech@nyvia.mx`.
- [ ] Voyage en `tech@nyvia.mx`.
- [ ] Qdrant bajo Nyvia.
- [ ] Supabase bajo Nyvia.
- [ ] Lovable bajo Nyvia.
- [ ] Langfuse bajo Nyvia.

---

## 14. Riesgos principales

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Repo en cuenta personal | Dependencia de empleado | Transferir a org Nyvia |
| Railway en cuenta personal | Riesgo operativo/billing | Migrar a workspace Nyvia |
| CORS abierto | Exposición innecesaria | Restringir dominios |
| Filtros controlados por frontend | Fuga entre organizaciones | Validar permisos backend |
| Memoria sin separación | Mezcla de datos | Guardar por usuario/org/proyecto |
| Full re-index | Borrado accidental | Agregar indexación incremental |
| Secrets en frontend | Compromiso de llaves | Solo variables públicas en frontend |
| Qdrant sin budget alerts | Sorpresa de costo por infra | Revisar tamaño cluster mensual |

---

## 15. Prompt de mantenimiento para Claude Code

```text
Actúa como engineer responsable de Nyvia Polaris.
Necesito revisar si el RAG está listo para producción.

Haz lo siguiente:
1. Lee README.md y docs/HANDOFF_NYVIA_POLARIS.md.
2. Revisa backend/config.py, routers/chat.py, services/embeddings.py, services/vector_store.py, services/llm.py y scripts/index_documents.py.
3. Detecta inconsistencias entre documentación y código.
4. Revisa si requirements.txt está completo.
5. Revisa riesgos de seguridad: CORS, secrets, auth, multi-tenant.
6. Propón cambios mínimos en archivos concretos.
7. Crea una checklist de pruebas manuales y automatizadas.
```

---

## 16. Próximos cambios recomendados en código

1. Crear `backend/.env.example`.
2. Agregar `anthropic` y `voyageai` a `backend/requirements.txt`.
3. Agregar metadata `organization_id` y `project_id` a indexador.
4. Crear índices Qdrant para filtros frecuentes.
5. Validar JWT Supabase en backend.
6. Restringir CORS.
7. Agregar selector/etiqueta de organización y proyecto en frontend.
8. Agregar tests de `/health`, `/chat/` y filtros.
9. Documentar start command real de Railway.
10. Documentar flujo real de Lovable.
