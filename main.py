"""FASTAPI APP"""
from fastapi import FastAPI, HTTPException, status, Depends

from . import db
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from .schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    TicketCreateRequest,
    TicketResponse,
    DecisionResponse,
)
from .decide import decide

app = FastAPI(title="MaxsorLabs Support Decision API")


@app.on_event("startup")
def on_startup():
    db.init_db()


@app.get("/")
def root():
    return {"status": "ok", "service": "support-decision-api"}


# ---------------- Auth routes ----------------

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    existing = db.get_user_by_email(payload.email)
    if existing is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    password_hash = hash_password(payload.password)
    user_id = db.create_user(payload.email, password_hash)
    user = db.get_user_by_id(user_id)
    return UserResponse(id=user["id"], email=user["email"], created_at=user["created_at"])


@app.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = db.get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    token = create_access_token(user["id"])
    return TokenResponse(access_token=token)


@app.get("/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)


# ---------------- Ticket routes ----------------

def _to_ticket_response(ticket: dict) -> TicketResponse:
    """Converts a raw DB row (dict) into the TicketResponse shape, with a nested decision."""
    decision = None
    if ticket.get("action"):
        decision = DecisionResponse(
            action=ticket["action"],
            reason=ticket["reason"],
            confidence=ticket["confidence"],
            sources=ticket["sources"],
        )
    return TicketResponse(
        id=ticket["id"],
        user_id=ticket["user_id"],
        message=ticket["message"],
        created_at=ticket["created_at"],
        decision=decision,
    )


@app.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreateRequest, current_user: dict = Depends(get_current_user)):
    ticket_id = db.create_ticket(current_user["id"], payload.model_dump())

    decision = decide(payload.model_dump())
    db.save_decision(ticket_id, decision)

    ticket = db.get_ticket_for_user(ticket_id, current_user["id"])
    return _to_ticket_response(ticket)


@app.get("/tickets", response_model=list[TicketResponse])
def list_tickets(current_user: dict = Depends(get_current_user)):
    tickets = db.list_tickets_for_user(current_user["id"])
    return [_to_ticket_response(t) for t in tickets]


@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, current_user: dict = Depends(get_current_user)):
    ticket = db.get_ticket_for_user(ticket_id, current_user["id"])
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found")
    return _to_ticket_response(ticket)
