# InterviewLens setup

## 1. Frontend check

Open `interviewlens/index.html` directly in a browser. Enter `Data Analyst` and click **Generate Prep Pack**. You should see questions, topics, behavioral questions, the checklist, and the Web Research section.

The frontend is configured for the Render API at `https://interviewlens-api.onrender.com`.

## 2. Deploy the backend on Render

Create a new **Web Service** from this GitHub repository and use:

- Branch: `main`
- Root Directory: `interviewlens/backend`
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment variable: `BRAVE_SEARCH_API_KEY` = your private Brave Search API key

Do not commit the API key to GitHub.

## 3. Test the backend

After Render deploys, open:

`https://interviewlens-api.onrender.com/health`

A working backend returns:

`{"status":"ok"}`

Then open `/docs` on the same host to test `/prep`, `/research`, and `/confirm` interactively.

## 4. Test web research

Use `/docs` → `POST /research` with:

```json
{"role":"Data Analyst","company":""}
```

With the Brave key configured, the response should contain `enabled: true`, source results, and any cautious `question_leads` extracted from search snippets.

## 5. Test the full site

Open the frontend, enter a role, generate the pack, and verify that:

1. role questions appear;
2. Web Research changes from `Connect API to enable` to a source count;
3. source links open;
4. clicking **I was asked this** increases the confirmation count;
5. refreshing the page preserves local confirmation totals for fallback/local questions.

## Current trust rule

InterviewLens does not call search results verified interview reports. Search-derived items are marked **Research lead**, while candidate confirmations are shown separately.
