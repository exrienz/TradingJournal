from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv
from fastapi import Cookie
import markdown  # Add this at the top with other imports

from . import models, schemas, crud, auth
from .database import engine, get_db, init_db

load_dotenv()

# Initialize database
init_db()

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Gemini AI integration
def get_gemini_insights(texts: list[str], prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API key not configured"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    # Combine all texts with newlines
    combined_text = "\n".join(texts)
    
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": f"{prompt}\n\n{combined_text}"}
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Error getting insights: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, access_token: str = Cookie(None), db: Session = Depends(get_db)):
    # Try to get the current user from the access_token cookie
    if access_token:
        try:
            # Remove 'Bearer ' prefix if present
            token = access_token[7:] if access_token.startswith('Bearer ') else access_token
            from jose import jwt
            from .auth import SECRET_KEY, ALGORITHM
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username:
                from .crud import get_user_by_username
                user = get_user_by_username(db, username=username)
                if user:
                    return RedirectResponse(url="/dashboard", status_code=303)
        except Exception:
            pass
    # Not logged in, show landing page
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    print("\n=== Registration Request ===")
    try:
        form = await request.form()
        print(f"Form data: {dict(form)}")
        
        email = form.get("email")
        username = form.get("username")
        password = form.get("password")
        
        print(f"Parsed fields:")
        print(f"- Email: {email}")
        print(f"- Username: {username}")
        print(f"- Password length: {len(password) if password else 0}")
        
        if not email or not username or not password:
            print("Error: Missing required fields")
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": "All fields are required.",
                    "email": email,
                    "username": username
                }
            )
        
        # Check if email exists
        if crud.get_user_by_email(db, email=email):
            print(f"Error: Email {email} already exists")
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": "Email already registered.",
                    "email": email,
                    "username": username
                }
            )
        
        # Check if username exists
        if crud.get_user_by_username(db, username=username):
            print(f"Error: Username {username} already exists")
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": "Username already taken.",
                    "email": email,
                    "username": username
                }
            )
        
        print("Creating new user...")
        # Create user
        user_in = schemas.UserCreate(email=email, username=username, password=password)
        db_user = crud.create_user(db=db, user=user_in)
        print(f"User created successfully with ID: {db_user.id}")
        
        print("Redirecting to login page...")
        return RedirectResponse(url="/login?registered=1", status_code=303)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": f"Registration failed: {str(e)}",
                "email": email if 'email' in locals() else None,
                "username": username if 'username' in locals() else None
            }
        )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    registered = request.query_params.get("registered")
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "registered": registered
        }
    )

@app.post("/token")
async def login(request: Request, db: Session = Depends(get_db)):
    print("\n=== Login Request ===")
    try:
        form = await request.form()
        print(f"Form data: {dict(form)}")
        
        username = form.get("username")
        password = form.get("password")
        
        print(f"Login attempt for username: {username}")
        
        user = crud.get_user_by_username(db, username=username)
        if not user:
            print(f"User not found: {username}")
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Incorrect username or password"
                }
            )
        
        print(f"User found, verifying password...")
        if not auth.verify_password(password, user.hashed_password):
            print("Password verification failed")
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Incorrect username or password"
                }
            )
        
        print("Password verified successfully")
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Create response with redirect
        response = RedirectResponse(url="/dashboard", status_code=303)
        # Set the token in a cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=1800,
            samesite="lax"
        )
        return response
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": f"Login failed: {str(e)}"
            }
        )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get dashboard stats
    stats = crud.get_dashboard_stats(db, current_user.id)
    
    # Get current month's entries
    now = datetime.utcnow()
    monthly_entries = crud.get_monthly_entries(db, current_user.id, now.year, now.month)
    
    # Convert entries to dictionaries
    entries_dict = []
    for entry in monthly_entries:
        entry_dict = {
            "id": entry.id,
            "date": entry.date.isoformat(),
            "profit": float(entry.profit),
            "loss": float(entry.loss),
            "reason_profit": entry.reason_profit,
            "reason_loss": entry.reason_loss
        }
        entries_dict.append(entry_dict)
    
    # Get Gemini insights
    profit_reasons = [entry.reason_profit for entry in monthly_entries if entry.reason_profit]
    loss_reasons = [entry.reason_loss for entry in monthly_entries if entry.reason_loss]
    
    if profit_reasons:
        trading_tips_md = get_gemini_insights(
            profit_reasons,
            "You are a trading coach. Based on these reasons traders succeeded, generate a concise list of best-practice Trading Tips. Format your response in Markdown."
        )
        trading_tips = markdown.markdown(trading_tips_md)
    else:
        trading_tips = "No profit reasons submitted yet."
    
    if loss_reasons:
        lessons_learned_md = get_gemini_insights(
            loss_reasons,
            "You are a trading mentor. Based on these reasons traders lost money, generate a concise Lessons Learned list of common mistakes and how to avoid them. Format your response in Markdown."
        )
        lessons_learned = markdown.markdown(lessons_learned_md)
    else:
        lessons_learned = "No loss reasons submitted yet."
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "monthly_entries": entries_dict,
            "trading_tips": trading_tips,
            "lessons_learned": lessons_learned
        }
    )

@app.get("/deposit", response_class=HTMLResponse)
async def deposit_page(
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return templates.TemplateResponse("deposit.html", {"request": request})

@app.post("/deposit")
async def create_deposit(
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        form = await request.form()
        amount = float(form.get("amount"))
        date_str = form.get("date")
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        deposit = schemas.DepositCreate(amount=amount, date=date)
        result = crud.create_deposit(db=db, deposit=deposit, user_id=current_user.id)
        
        return RedirectResponse(url="/dashboard", status_code=303)
    except Exception as e:
        print(f"Error creating deposit: {str(e)}")
        return templates.TemplateResponse(
            "deposit.html",
            {
                "request": request,
                "error": f"Failed to create deposit: {str(e)}"
            }
        )

@app.get("/withdraw", response_class=HTMLResponse)
async def withdraw_page(
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return templates.TemplateResponse("withdraw.html", {"request": request})

@app.post("/withdraw")
async def create_withdrawal(
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        form = await request.form()
        amount = float(form.get("amount"))
        date_str = form.get("date")
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        withdrawal = schemas.WithdrawalCreate(amount=amount, date=date)
        result = crud.create_withdrawal(db=db, withdrawal=withdrawal, user_id=current_user.id)
        
        return RedirectResponse(url="/dashboard", status_code=303)
    except Exception as e:
        print(f"Error creating withdrawal: {str(e)}")
        return templates.TemplateResponse(
            "withdraw.html",
            {
                "request": request,
                "error": f"Failed to create withdrawal: {str(e)}"
            }
        )

@app.get("/daily-entry", response_class=HTMLResponse)
async def daily_entry_page(
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    date_str = request.query_params.get("date")
    entry_data = None
    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            entry = crud.get_daily_entry_by_date(db, current_user.id, date)
            if entry:
                entry_data = {
                    "date": entry.date.strftime("%Y-%m-%d"),
                    "profit": entry.profit,
                    "loss": entry.loss,
                    "reason_profit": entry.reason_profit or "",
                    "reason_loss": entry.reason_loss or ""
                }
            else:
                entry_data = {"date": date_str, "profit": 0, "loss": 0, "reason_profit": "", "reason_loss": ""}
        except Exception as e:
            entry_data = None
    return templates.TemplateResponse("daily_entry.html", {"request": request, "entry": entry_data})

@app.post("/daily-entry")
async def create_daily_entry(
    request: Request,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        form = await request.form()
        date_str = form.get("date")
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        profit = float(form.get("profit", 0) or 0)
        loss = float(form.get("loss", 0) or 0)
        reason_profit = form.get("reason_profit")
        reason_loss = form.get("reason_loss")
        
        entry = schemas.DailyEntryCreate(
            date=date,
            profit=profit,
            loss=loss,
            reason_profit=reason_profit,
            reason_loss=reason_loss
        )
        result = crud.create_daily_entry(db=db, entry=entry, user_id=current_user.id)
        
        return RedirectResponse(url="/dashboard", status_code=303)
    except Exception as e:
        print(f"Error creating daily entry: {str(e)}")
        return templates.TemplateResponse(
            "daily_entry.html",
            {
                "request": request,
                "error": f"Failed to create daily entry: {str(e)}"
            }
        )

@app.put("/daily-entry/{entry_id}")
async def update_daily_entry(
    entry_id: int,
    entry: schemas.DailyEntryCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    updated_entry = crud.update_daily_entry(db=db, entry_id=entry_id, entry=entry, user_id=current_user.id)
    if not updated_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return updated_entry

@app.get("/test")
async def test():
    print("Test endpoint called")
    return {"message": "Test endpoint working"}

@app.post("/test")
async def test_post(request: Request):
    print("\n=== Test POST Request ===")
    try:
        form = await request.form()
        print(f"Form data: {dict(form)}")
        return {"message": "Test successful", "data": dict(form)}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)} 