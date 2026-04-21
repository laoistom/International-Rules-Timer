import os
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import asc, or_, select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .database import Base, engine, get_db
from .models import Match, Player, Tournament

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-this")

app = FastAPI(title="Pool Tournament Draw & Score Tracker")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


def require_admin(request: Request) -> None:
    if request.session.get("is_admin") is not True:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/admin/login"})


@app.get("/", response_class=HTMLResponse)
def public_tournaments(request: Request, q: str = "", db: Session = Depends(get_db)):
    stmt = (
        select(Tournament)
        .where(Tournament.draw_published.is_(True), Tournament.status.in_(["scheduled", "running"]))
        .order_by(asc(Tournament.starts_at))
    )
    if q:
        term = f"%{q}%"
        stmt = stmt.where(or_(Tournament.name.ilike(term), Tournament.location.ilike(term)))

    tournaments = db.execute(stmt).scalars().all()
    return templates.TemplateResponse("public_index.html", {"request": request, "tournaments": tournaments, "q": q})


@app.get("/tournaments/{tournament_id}", response_class=HTMLResponse)
def public_tournament_detail(tournament_id: int, request: Request, db: Session = Depends(get_db)):
    tournament = db.get(Tournament, tournament_id)
    if not tournament or not tournament.draw_published:
        raise HTTPException(status_code=404, detail="Tournament not found")

    matches = (
        db.execute(select(Match).where(Match.tournament_id == tournament_id).order_by(asc(Match.round_name), asc(Match.table_no)))
        .scalars()
        .all()
    )
    return templates.TemplateResponse(
        "public_tournament.html",
        {"request": request, "tournament": tournament, "matches": matches},
    )


@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})


@app.post("/admin/login", response_class=HTMLResponse)
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["is_admin"] = True
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)


@app.post("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    tournaments = db.execute(select(Tournament).order_by(asc(Tournament.starts_at))).scalars().all()
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "tournaments": tournaments})


@app.post("/admin/tournaments")
def create_tournament(
    request: Request,
    name: str = Form(...),
    location: str = Form(...),
    starts_at: str = Form(...),
    status_value: str = Form("scheduled"),
    db: Session = Depends(get_db),
):
    require_admin(request)
    tournament = Tournament(
        name=name.strip(),
        location=location.strip(),
        starts_at=datetime.fromisoformat(starts_at),
        status=status_value,
    )
    db.add(tournament)
    db.commit()
    return RedirectResponse("/admin", status_code=303)


@app.get("/admin/tournaments/{tournament_id}", response_class=HTMLResponse)
def manage_tournament(tournament_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    tournament = db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    players = db.execute(select(Player).where(Player.tournament_id == tournament_id).order_by(asc(Player.name))).scalars().all()
    matches = db.execute(select(Match).where(Match.tournament_id == tournament_id).order_by(asc(Match.round_name), asc(Match.table_no))).scalars().all()

    return templates.TemplateResponse(
        "admin/tournament_manage.html",
        {"request": request, "tournament": tournament, "players": players, "matches": matches},
    )


@app.post("/admin/tournaments/{tournament_id}/settings")
def update_tournament_settings(
    tournament_id: int,
    request: Request,
    status_value: str = Form(...),
    draw_published: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    require_admin(request)
    tournament = db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    tournament.status = status_value
    tournament.draw_published = draw_published == "on"
    db.commit()
    return RedirectResponse(f"/admin/tournaments/{tournament_id}", status_code=303)


@app.post("/admin/tournaments/{tournament_id}/players")
def add_player(tournament_id: int, request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    require_admin(request)
    tournament = db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    db.add(Player(tournament_id=tournament_id, name=name.strip()))
    db.commit()
    return RedirectResponse(f"/admin/tournaments/{tournament_id}", status_code=303)


@app.post("/admin/tournaments/{tournament_id}/matches")
def add_match(
    tournament_id: int,
    request: Request,
    round_name: str = Form(...),
    table_no: str = Form(...),
    player_a: str = Form(...),
    player_b: str = Form(...),
    db: Session = Depends(get_db),
):
    require_admin(request)
    tournament = db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    db.add(
        Match(
            tournament_id=tournament_id,
            round_name=round_name.strip(),
            table_no=table_no.strip(),
            player_a=player_a.strip(),
            player_b=player_b.strip(),
        )
    )
    db.commit()
    return RedirectResponse(f"/admin/tournaments/{tournament_id}", status_code=303)


@app.post("/admin/matches/{match_id}/score")
def update_match_score(
    match_id: int,
    request: Request,
    score_a: int = Form(...),
    score_b: int = Form(...),
    is_finished: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    require_admin(request)
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.score_a = max(0, score_a)
    match.score_b = max(0, score_b)
    match.is_finished = is_finished == "on"
    db.commit()

    return RedirectResponse(f"/admin/tournaments/{match.tournament_id}", status_code=303)
