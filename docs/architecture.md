# Architecture

```text
browser -> FastAPI -> local Ollama -> constraint gate -> three cards
                    \-> local SQLite (content)
                     \-> Backboard adapter (behavioural signals only)
```

Content (goal text, notes, and drafts) stays in local SQLite and is never sent
to a remote service. Backboard receives only abstract signals: goal ID, energy,
minutes, time bucket, action type, and completion status. The adapter is
explicitly stubbed until its current official API is verified.
