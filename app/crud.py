from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from . import models, schemas, auth

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    print(f"Creating user with email: {user.email}, username: {user.username}")
    hashed_password = auth.get_password_hash(user.password)
    print(f"Password hashed successfully")
    
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    print("User object created, adding to database...")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print(f"User created successfully with ID: {db_user.id}")
    return db_user

def create_deposit(db: Session, deposit: schemas.DepositCreate, user_id: int):
    db_deposit = models.Deposit(**deposit.dict(), user_id=user_id)
    db.add(db_deposit)
    
    # Update user's active balance
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.active_balance += deposit.amount
    
    db.commit()
    db.refresh(db_deposit)
    return db_deposit

def create_withdrawal(db: Session, withdrawal: schemas.WithdrawalCreate, user_id: int):
    db_withdrawal = models.Withdrawal(**withdrawal.dict(), user_id=user_id)
    db.add(db_withdrawal)
    
    # Update user's active balance
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.active_balance -= withdrawal.amount
    
    db.commit()
    db.refresh(db_withdrawal)
    return db_withdrawal

def create_daily_entry(db: Session, entry: schemas.DailyEntryCreate, user_id: int):
    db_entry = models.DailyEntry(**entry.dict(), user_id=user_id)
    db.add(db_entry)
    
    # Update user's active balance
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.active_balance += entry.profit - entry.loss
    
    db.commit()
    db.refresh(db_entry)
    return db_entry

def get_daily_entry(db: Session, entry_id: int, user_id: int):
    return db.query(models.DailyEntry).filter(
        models.DailyEntry.id == entry_id,
        models.DailyEntry.user_id == user_id
    ).first()

def update_daily_entry(db: Session, entry_id: int, entry: schemas.DailyEntryCreate, user_id: int):
    db_entry = get_daily_entry(db, entry_id, user_id)
    if not db_entry:
        return None
    
    # Revert previous profit/loss from active balance
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.active_balance -= db_entry.profit - db_entry.loss
    
    # Update entry and add new profit/loss
    for key, value in entry.dict().items():
        setattr(db_entry, key, value)
    user.active_balance += entry.profit - entry.loss
    
    db.commit()
    db.refresh(db_entry)
    return db_entry

def get_dashboard_stats(db: Session, user_id: int):
    total_deposited = db.query(func.sum(models.Deposit.amount)).filter(
        models.Deposit.user_id == user_id
    ).scalar() or 0.0
    
    total_withdrawn = db.query(func.sum(models.Withdrawal.amount)).filter(
        models.Withdrawal.user_id == user_id
    ).scalar() or 0.0
    
    total_profit = db.query(func.sum(models.DailyEntry.profit)).filter(
        models.DailyEntry.user_id == user_id
    ).scalar() or 0.0
    
    total_loss = db.query(func.sum(models.DailyEntry.loss)).filter(
        models.DailyEntry.user_id == user_id
    ).scalar() or 0.0
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    return {
        "active_balance": user.active_balance,
        "total_deposited": total_deposited,
        "total_withdrawn": total_withdrawn,
        "total_profit": total_profit,
        "total_loss": total_loss,
        "total_pnl": total_profit - total_loss
    }

def get_monthly_entries(db: Session, user_id: int, year: int, month: int):
    return db.query(models.DailyEntry).filter(
        models.DailyEntry.user_id == user_id,
        func.extract('year', models.DailyEntry.date) == year,
        func.extract('month', models.DailyEntry.date) == month
    ).all()

def get_daily_entry_by_date(db, user_id: int, date):
    return db.query(models.DailyEntry).filter(
        models.DailyEntry.user_id == user_id,
        models.DailyEntry.date == date
    ).first()

def reset_user_data(db: Session, user_id: int):
    """Delete all trading data for the given user and reset balance."""
    db.query(models.Deposit).filter(models.Deposit.user_id == user_id).delete(synchronize_session=False)
    db.query(models.Withdrawal).filter(models.Withdrawal.user_id == user_id).delete(synchronize_session=False)
    db.query(models.DailyEntry).filter(models.DailyEntry.user_id == user_id).delete(synchronize_session=False)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.active_balance = 0.0

    db.commit()
