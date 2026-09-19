# MaxsorLabs Support Decision Assistant Assignment

A small AI app that reads a customer support ticket and decides what action to take,
using the company's policy documents as the source of truth.

## What it does?

1. You log in through a simple web page (Streamlit).
2. You type in a support ticket (e.g. "My order arrived damaged").
3. The app finds the most relevant policy rules from the knowledge base.
4. It sends the ticket + those rules to Google's Gemini AI model.
5. The AI returns a decision (like "Request Photos" or "Approve Return") with a reason.
6. Everything is saved so you can look back at your past tickets anytime.

## Tech used -

- **Streamlit** — the web page you interact with
- **FastAPI** — the backend server that does the actual work
- **JWT** — keeps your login secure
- **SQLite** — stores users, tickets, and decisions
- **Gemini API** — the AI model that reads policies and makes the decision
- **RAG** — finds the right policy rules before asking the AI, so it doesn't guess

## How to run it?

1. Install the required packages:
2. Create a new file named `.env`, and fill in:

   - `GEMINI_API_KEY` — free key from https://aistudio.google.com/apikey
   - `JWT_SECRET` — any long random text you make up
3. Set up the database.
4. Build the policy search index.
5. Start the backend (and keep this terminal open):
6. In a **second terminal**, start the app:
7. Open the link it shows (`http://localhost:8501`).

   ## How the AI decision works?


   - Each policy file's rules are split into small pieces ("chunks").
   - Each chunk is turned into a set of numbers ("embedding") that captures its meaning.
   - When a ticket comes in, the app finds the 4 most relevant chunks by comparing numbers.
   - Only those 4 rules — not the whole knowledge base — are sent to Gemini, along with the ticket.
   - Gemini replies with a decision, and the app double-checks the reply makes sense
     before saving it. If the reply looks wrong or incomplete, the app plays it safe
     and returns "Needs More Information" instead of guessing.

   ## Tests -

   - `pytest tests/test_auth_isolation.py -v` — proves one user can't see another user's tickets
   - `python tests/run_eval.py` — checks the AI's decisions against 5 known example cases

   ## Known limitations -

   This was built as a small assignment project, not a production system:

   - The AI can occasionally be inconsistent on borderline cases.
   - No production database (SQLite is fine for this scale).
   - No deployment/hosting — runs locally only.
