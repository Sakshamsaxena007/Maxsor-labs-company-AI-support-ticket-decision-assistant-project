# Development Notes ->

## How I used AI while building this?

I used Claude as a pair-programmer throughout this project.
I described what each part of the assignment needed, Claude wrote the first version
of the code, and I ran it, tested it, and fixed issues as they came up — including:

- A deprecated Gemini embedding model name that needed updating.
- A login bug where the word "Bearer" was accidentally duplicated in the auth header.
- A display bug in the History tab where the AI's decision wasn't showing up
  (it was nested one level deeper in the response than the frontend expected).
- Occasional inconsistent AI answers on borderline tickets, fixed by asking the
  AI a second time only when it says it needs more information.

I reviewed and tested every part before considering it done — for example, I ran the
authentication test to confirm one user genuinely cannot see another user's tickets,
and I ran the evaluation script against the provided sample test cases to check accuracy.

## Why I made certain choices?

- Used plain SQLite since the database only has 3 simple tables.
- Split each policy document by its numbered rules rather than arbitrary text chunks,
  so each retrieved piece of context maps to one specific, citable rule.
- Added strict validation after every AI response — if it returns anything outside
  the 15 allowed actions, the system falls back to "Needs More Information" instead
  of trusting an unexpected answer.
- I hit the Gemini free-tier daily quota while testing extensively; switched to a fresh API key to complete testing and the recording.
