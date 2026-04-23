from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import timedelta
import random
from app.utils.email_service import send_verification_otp

from app.database import get_db
from app.models.models import User
from app.schemas.user_schemas import UserCreate, UserResponse, Token, MessageSchema
from app.core.security import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credential_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenicae" : "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
    except JWTError:
        raise credential_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credential_exception
    return user

@router.post("/register", response_model=MessageSchema,status_code= status.HTTP_201_CREATED)
def register(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db : Session = Depends(get_db),
    ):
    db_user = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or Email has been taken")
    
    hashed_password = get_password_hash(user.password)
    otp = f"{random.randint(100000, 999999)}"

    new_user = User (
        username = user.username,
        email = user.email, 
        verification_token = otp,
        password_hashed = hashed_password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    background_tasks.add_task(send_verification_otp, new_user.email, otp)
    return {"message": "User registered successfully. Please check your email for the OTP to verify your account."}

@router.post("/verify-otp")
def verify_otp(email: str, otp: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.email == email,
        User.verification_token == otp
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or OTP")
    
    user.is_verified = True
    user.verification_token = None
    db.commit()
    
    return {"status": "success", "message": "Email verified successfully. You can now log in."}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if (not user) or (not verify_password(form_data.password, user.password_hashed)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified. Please verify your email first.",
        )
    
    access_token_expires = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type":"Bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user