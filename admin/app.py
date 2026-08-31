"""Admin panel — JSON API (React frontend uchun)."""
from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel

from . import config, db

app = FastAPI(title="Taxi Yordamchi — Admin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_serializer = URLSafeTimedSerializer(config.SECRET_KEY, salt="admin-auth")
_TOKEN_MAX_AGE = 60 * 60 * 12  # 12 soat


# ---------------------------------------------------------------------- auth
def _make_token(username: str) -> str:
    return _serializer.dumps({"u": username})


def require_admin(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Avtorizatsiya talab qilinadi")
    token = authorization[7:]
    try:
        data = _serializer.loads(token, max_age=_TOKEN_MAX_AGE)
    except SignatureExpired:
        raise HTTPException(status_code=401, detail="Sessiya muddati tugadi")
    except BadSignature:
        raise HTTPException(status_code=401, detail="Yaroqsiz token")
    return data["u"]


class LoginIn(BaseModel):
    username: str
    password: str


@app.post("/api/login")
async def login(body: LoginIn):
    if body.username == config.ADMIN_USERNAME and body.password == config.ADMIN_PASSWORD:
        return {"token": _make_token(body.username), "username": body.username}
    raise HTTPException(status_code=401, detail="Login yoki parol xato")


@app.get("/api/me")
async def me(admin: str = Depends(require_admin)):
    return {"username": admin, "currency": config.CURRENCY}


# ------------------------------------------------------------------- ma'lumot
@app.get("/api/stats")
async def stats(admin: str = Depends(require_admin)):
    return db.get_stats()


@app.get("/api/users")
async def users(
    admin: str = Depends(require_admin),
    search: str = "",
    status: str = "all",
    sort: str = "last_active",
    page: int = 1,
):
    page = max(1, page)
    per_page = 25
    rows, total = db.list_users(search, status, sort, page, per_page)
    pages = (total + per_page - 1) // per_page
    return {"users": rows, "total": total, "page": page, "pages": pages}


@app.get("/api/users/{user_id}")
async def user_detail(user_id: int, admin: str = Depends(require_admin)):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return user


class PayIn(BaseModel):
    amount: float
    months: int = 1
    note: str = ""


@app.post("/api/users/{user_id}/pay")
async def add_payment(user_id: int, body: PayIn, admin: str = Depends(require_admin)):
    db.add_payment(user_id, body.amount, body.months, body.note)
    return db.get_user(user_id)


class SetDateIn(BaseModel):
    paid_until: str = ""


@app.post("/api/users/{user_id}/set-date")
async def set_date(user_id: int, body: SetDateIn, admin: str = Depends(require_admin)):
    db.set_paid_until(user_id, body.paid_until)
    return db.get_user(user_id)


@app.get("/api/payments")
async def payments(
    admin: str = Depends(require_admin),
    date_from: str = "",
    date_to: str = "",
):
    rows, total = db.list_payments(date_from, date_to)
    return {"payments": rows, "total": total}


# ------------------------------------------------- React build (production)
_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        # API bo'lmagan barcha yo'llar React index.html ga yo'naltiriladi (SPA routing).
        index = os.path.join(_DIST, "index.html")
        return FileResponse(index)


def run() -> None:
    import uvicorn

    uvicorn.run(app, host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    run()
