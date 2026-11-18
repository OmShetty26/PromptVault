from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
import models
import jwt
from schemas import *
from database import engine, get_db
from datetime import datetime, timezone
from security import (
    hash_password,
    verify_password,
    create_access_token,
    ALGORITHM
)

from config import settings
import logging
from fastapi.responses import FileResponse, JSONResponse


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    # Never return submitted input values or raw validation context.
    # Request bodies may contain passwords or other sensitive information.
    safe_errors = [
        {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
        }
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=422,
        content={"detail": safe_errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception during %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# 2. Define who is allowed to talk to this API
origins = [settings.frontend_url]

# 3. Add the CORS middleware to your engine
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Only allow requests from the VIP list
    allow_credentials=True,
    allow_methods=["*"],         # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],         # Allow all headers
)

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )

        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

    return user

@app.get("/api/prompts")
def get_prompts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    response = db.query(models.Prompt).filter(models.Prompt.user_id == current_user.id).all()
    return response

# Create a POST route to receive new prompts
@app.post("/api/prompts")
def create_prompt(new_prompt: PromptCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if new_prompt.title.strip() == "" or new_prompt.content.strip() == "":
        raise HTTPException(status_code = 400, detail = "Title and Content cannot be empty!")
    logger.info("Prompt created successfully")
    new_db_prompt = models.Prompt(title=new_prompt.title, category=new_prompt.category, content=new_prompt.content, user_id = current_user.id)
    db.add(new_db_prompt)
    db.commit()
    db.refresh(new_db_prompt)
    
    return new_db_prompt

#PUT route to update existing prompts
@app.put("/api/prompts/{prompt_id}")
def update_prompt(
    prompt_id: int,
    updated_prompt: PromptCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_prompt = (
        db.query(models.Prompt)
        .filter(
            models.Prompt.id == prompt_id,
            models.Prompt.user_id == current_user.id
        )
        .first()
    )

    if not db_prompt:
        raise HTTPException(
            status_code=404,
            detail="Prompt ID Not Found!"
        )

    if updated_prompt.title.strip() == "" or updated_prompt.content.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Title and Content cannot be empty!"
        )

    db_prompt.title = updated_prompt.title
    db_prompt.category = updated_prompt.category
    db_prompt.content = updated_prompt.content

    db.commit()
    db.refresh(db_prompt)

    return db_prompt

# GET one prompt
@app.get("/api/prompts/{prompt_id}")
def get_prompt(prompt_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_prompt = (
        db.query(models.Prompt)
        .filter(models.Prompt.id == prompt_id,
                models.Prompt.user_id == current_user.id)
        .first()
    )

    if not db_prompt:
        raise HTTPException(status_code = 404, detail = "Prompt ID Not Found!")

    return db_prompt


# PATCH pin status
@app.patch("/api/prompts/{prompt_id}/pin")
def update_prompt_pin(
    prompt_id: int,
    update: PromptPinUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_prompt = (
        db.query(models.Prompt)
        .filter(models.Prompt.id == prompt_id, models.Prompt.user_id == current_user.id)
        .first()
    )

    if not db_prompt:
        raise HTTPException(status_code = 404, detail = "Prompt ID Not Found!")

    db_prompt.is_pinned = update.is_pinned

    db.commit()
    db.refresh(db_prompt)

    return db_prompt


# Record prompt opening
@app.post("/api/prompts/{prompt_id}/open")
def open_prompt(
    prompt_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_prompt = (
        db.query(models.Prompt)
        .filter(models.Prompt.id == prompt_id, models.Prompt.user_id == current_user.id)
        .first()
    )

    if not db_prompt:
        raise HTTPException(status_code = 404, detail = "Prompt ID Not Found!")

    db_prompt.last_opened_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(db_prompt)

    return db_prompt


# DELETE prompt
@app.delete("/api/prompts/{prompt_id}")
def delete_prompt(
    prompt_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_prompt = (
        db.query(models.Prompt)
        .filter(models.Prompt.id == prompt_id, models.Prompt.user_id == current_user.id)
        .first()
    )

    if not db_prompt:
        raise HTTPException(status_code = 404, detail = "Prompt ID Not Found!")

    db.delete(db_prompt)
    db.commit()

    return {"status": "success"}

@app.patch("/api/prompts/{prompt_id}/rename")
def rename_prompt(
    prompt_id: int,
    update: PromptRenameUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_prompt = (
        db.query(models.Prompt)
        .filter(models.Prompt.id == prompt_id, models.Prompt.user_id == current_user.id)
        .first()
    )

    if not db_prompt:
        raise HTTPException(
            status_code = 404,
            detail = "Prompt ID Not Found!"
        )

    new_title = update.title.strip()

    if not new_title:
        raise HTTPException(
            status_code = 400,
            detail = "Prompt title cannot be empty!"
        )

    db_prompt.title = new_title

    db.commit()
    db.refresh(db_prompt)

    return db_prompt

# POST Route to register a first time user
@app.post("/auth/register", response_model=UserResponse, status_code=201)
def register_user(
    user_input: UserCreate,
    db: Session = Depends(get_db)
):
    input_username = user_input.username.strip()

    existing_username = (
        db.query(models.User.username)
        .filter(models.User.username == input_username)
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    hashed_pwd = hash_password(user_input.password)

    new_user = models.User(
        username=input_username,
        password_hash=hashed_pwd
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# POST Route to login a user
@app.post("/auth/login", response_model = UserResponse)
def login_user(user_input: UserLogin, response: Response, db: Session = Depends(get_db)):
    input_username = user_input.username.strip()

    db_user = (db.query(models.User)
                   .filter(models.User.username == input_username)
                   .first())

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    check_password = verify_password(user_input.password, db_user.password_hash)

    if not check_password:
        raise HTTPException(
                    status_code=401,
                    detail="Invalid username or password"
                )

    access_token = create_access_token(db_user.id)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.is_production,
        max_age=30 * 60
    )

    return db_user


# GET currently authenticated user
@app.get("/auth/me", response_model=UserResponse)
def get_me(
    current_user: models.User = Depends(get_current_user)
):
    return current_user


@app.post("/auth/logout")
def logout_user(response: Response, current_user: models.User = Depends(get_current_user)):
    response.delete_cookie(
        key="access_token",
        path="/"
    )

    return {"message": "Logged out successfully"}


# Serve the production React frontend
FRONTEND_DIST_DIR = (
    Path(__file__).resolve().parent / "static"
).resolve()

if (FRONTEND_DIST_DIR / "index.html").is_file():

    @app.get("/", include_in_schema=False)
    async def serve_frontend_root():
        return FileResponse(FRONTEND_DIST_DIR / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):

        # Preserve 404 responses for unknown API endpoints
        if (
            full_path in {"api", "auth"}
            or full_path.startswith(("api/", "auth/"))
        ):
            raise HTTPException(
                status_code=404,
                detail="Not Found"
            )

        requested_file = (
            FRONTEND_DIST_DIR / full_path
        ).resolve()

        # Serve actual frontend assets, such as JS, CSS and images
        if (
            requested_file.is_relative_to(FRONTEND_DIST_DIR)
            and requested_file.is_file()
        ):
            return FileResponse(requested_file)

        # Don't return index.html for missing static assets
        if (
            full_path == "assets"
            or full_path.startswith("assets/")
            or Path(full_path).suffix
        ):
            raise HTTPException(
                status_code=404,
                detail="Not Found"
            )

        # Let React handle frontend routes
        return FileResponse(FRONTEND_DIST_DIR / "index.html")


