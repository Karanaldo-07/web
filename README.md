# InterviewLens

A mobile-first interview preparation website. Enter a job title or job description and get a practical preparation pack: role/JD-targeted questions, behavioral questions, preparation steps, live web research, and community-reported interview experiences.

## Current MVP
- Role and job-description targeting
- Candidate confirmation signal: **I was asked this**
- Persistent interview-experience reports with company, round, and difficulty context
- Tavily-powered web interview research through the server-side API
- Five-question **AI Mock Interview** practice flow with answer scoring
- Mock scoring rubric: relevance, completeness, structure, and specificity
- Responsive GitHub Pages frontend + FastAPI/Vercel backend

## Mock interview note
The current mock interviewer uses a transparent local scoring engine so it works without exposing an AI provider key in the browser. It is intentionally structured as an MVP; an LLM evaluator can be added behind the existing backend later without changing the user flow.

## Product principle
Generated/recommended questions are clearly separated from candidate-reported evidence. A question receives a community confirmation only after a user reports that they were actually asked it.

## Security
Secrets such as Tavily and Supabase server keys must stay in Vercel environment variables and must never be committed to this repository or shipped to browser JavaScript.
