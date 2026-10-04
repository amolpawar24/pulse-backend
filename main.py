from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Query,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    get_current_user,
)
from database import (
    Base,
    engine,
    get_db,
    SessionLocal,
)
from manager import manager
from models import User, Message
from schemas import RegisterIn, LoginIn


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Pulse Chat API"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:5173",
        "http://127.0.0.1:5173",

        "http://localhost:5174",
        "http://127.0.0.1:5174",

        "http://localhost:3000",
        "http://127.0.0.1:3000",

        # Production
        "https://pulse-messaging.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    print(
        "UNHANDLED ERROR:",
        repr(exc),
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error"
        },
    )


# ============================================================
# SERIALIZERS
# ============================================================

def user_to_dict(
    user: User,
) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_online": manager.is_online(
            user.id
        ),
    }


def message_to_dict(
    message: Message,
) -> dict:
    return {
        "id": message.id,
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "message": message.message,
        "timestamp": (
            message.timestamp.isoformat()
            + "Z"
        ),
    }


# ============================================================
# AUTH
# ============================================================

@app.post(
    "/api/auth/register",
    status_code=201,
)
def register(
    data: RegisterIn,
    db: Session = Depends(get_db),
):
    email = data.email.lower()

    existing_user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    user = User(
        name=data.name.strip(),
        email=email,
        password=hash_password(
            data.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "access_token": create_access_token(
            user.id
        ),
        "token_type": "bearer",
        "user": user_to_dict(user),
    }


@app.post("/api/auth/login")
def login(
    data: LoginIn,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(
            User.email
            == data.email.lower()
        )
        .first()
    )

    if (
        not user
        or not verify_password(
            data.password,
            user.password,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return {
        "access_token": create_access_token(
            user.id
        ),
        "token_type": "bearer",
        "user": user_to_dict(user),
    }


# ============================================================
# CURRENT USER
# ============================================================

@app.get("/api/users/me")
def me(
    current: User = Depends(
        get_current_user
    ),
):
    return user_to_dict(current)


# ============================================================
# USERS
# ============================================================

@app.get("/api/users")
def list_users(
    search: str = "",
    current: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    query = (
        db.query(User)
        .filter(
            User.id != current.id
        )
    )

    if search.strip():
        like = (
            f"%{search.strip()}%"
        )

        query = query.filter(
            or_(
                User.name.ilike(like),
                User.email.ilike(like),
            )
        )

    users = (
        query
        .order_by(User.name)
        .all()
    )

    return [
        user_to_dict(user)
        for user in users
    ]


# ============================================================
# MESSAGES
# ============================================================

@app.get(
    "/api/messages/{other_id}"
)
def get_messages(
    other_id: int,
    current: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    messages = (
        db.query(Message)
        .filter(
            or_(
                and_(
                    Message.sender_id
                    == current.id,
                    Message.receiver_id
                    == other_id,
                ),
                and_(
                    Message.sender_id
                    == other_id,
                    Message.receiver_id
                    == current.id,
                ),
            )
        )
        .order_by(
            Message.timestamp
        )
        .all()
    )

    return [
        message_to_dict(message)
        for message in messages
    ]


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    db = SessionLocal()

    user_id = None

    # --------------------------------------------------------
    # AUTHENTICATE WEBSOCKET
    # --------------------------------------------------------

    try:
        user_id = decode_token(token)

        user = db.get(
            User,
            user_id,
        )

        if not user:
            print(
                "WEBSOCKET USER NOT FOUND:",
                user_id,
            )

            await websocket.close(
                code=4401
            )

            return

    except Exception as exc:
        print(
            "WEBSOCKET AUTH ERROR:",
            repr(exc),
        )

        await websocket.close(
            code=4401
        )

        return

    # --------------------------------------------------------
    # CONNECTION
    # --------------------------------------------------------

    try:
        await manager.connect(
            user_id,
            websocket,
        )

        print(
            "WEBSOCKET CONNECTED:",
            user_id,
        )

        # ----------------------------------------------------
        # PRESENCE ONLINE
        # ----------------------------------------------------

        await manager.broadcast(
            {
                "type": "presence",
                "user_id": user_id,
                "is_online": True,
            }
        )

        # ----------------------------------------------------
        # RECEIVE EVENTS
        # ----------------------------------------------------

        while True:
            data = (
                await websocket.receive_json()
            )

            print(
                "================================"
            )

            print(
                "WEBSOCKET RECEIVED:",
                data,
            )

            if not isinstance(
                data,
                dict,
            ):
                print(
                    "INVALID WEBSOCKET DATA"
                )
                continue

            kind = data.get(
                "type"
            )

            print(
                "WEBSOCKET TYPE:",
                kind,
            )

            # ==================================================
            # MESSAGE
            # ==================================================

            if kind == "message":

                receiver_id = data.get(
                    "receiver_id"
                )

                text = data.get(
                    "message"
                )

                print(
                    "SENDER:",
                    user_id,
                )

                print(
                    "RECEIVER:",
                    receiver_id,
                )

                print(
                    "MESSAGE:",
                    text,
                )

                if not isinstance(
                    receiver_id,
                    int,
                ):
                    print(
                        "INVALID RECEIVER ID"
                    )
                    continue

                if not isinstance(
                    text,
                    str,
                ):
                    print(
                        "INVALID MESSAGE VALUE"
                    )
                    continue

                text = text.strip()

                if not text:
                    print(
                        "EMPTY MESSAGE"
                    )
                    continue

                receiver = db.get(
                    User,
                    receiver_id,
                )

                if not receiver:
                    print(
                        "RECEIVER DOES NOT EXIST:",
                        receiver_id,
                    )
                    continue

                # ----------------------------------------------
                # SAVE MESSAGE
                # ----------------------------------------------

                message = Message(
                    sender_id=user_id,
                    receiver_id=receiver_id,
                    message=text,
                )

                db.add(message)

                print(
                    "MESSAGE ADDED TO "
                    "SQLALCHEMY SESSION"
                )

                try:
                    db.commit()
                    db.refresh(message)

                except Exception as db_error:
                    db.rollback()

                    print(
                        "MYSQL SAVE ERROR:",
                        repr(db_error),
                    )

                    continue

                print(
                    "MESSAGE SAVED TO MYSQL:",
                    message.id,
                )

                # ----------------------------------------------
                # MESSAGE PAYLOAD
                # ----------------------------------------------

                payload = {
                    "type": "message",
                    **message_to_dict(
                        message
                    ),
                }

                print(
                    "MESSAGE PAYLOAD:",
                    payload,
                )

                # ----------------------------------------------
                # SEND TO RECEIVER
                # ----------------------------------------------

                await manager.send_to_user(
                    receiver_id,
                    payload,
                )

                # ----------------------------------------------
                # SEND BACK TO SENDER
                # ----------------------------------------------

                await manager.send_to_user(
                    user_id,
                    payload,
                )

                print(
                    "MESSAGE SENT SUCCESSFULLY"
                )

                print(
                    "================================"
                )

            # ==================================================
            # READ RECEIPT
            # ==================================================

            elif kind == "read":

                message_id = data.get(
                    "message_id"
                )

                sender_id = data.get(
                    "sender_id"
                )

                print(
                    "READ RECEIPT REQUEST:",
                    message_id,
                    sender_id,
                    "CURRENT USER:",
                    user_id,
                )

                if not isinstance(
                    message_id,
                    int,
                ):
                    print(
                        "INVALID MESSAGE ID "
                        "FOR READ RECEIPT"
                    )
                    continue

                if not isinstance(
                    sender_id,
                    int,
                ):
                    print(
                        "INVALID SENDER ID "
                        "FOR READ RECEIPT"
                    )
                    continue

                message = db.get(
                    Message,
                    message_id,
                )

                if not message:
                    print(
                        "READ RECEIPT MESSAGE "
                        "NOT FOUND:",
                        message_id,
                    )
                    continue

                if (
                    message.receiver_id
                    != user_id
                ):
                    print(
                        "INVALID READ RECEIPT USER:",
                        user_id,
                    )
                    continue

                if (
                    message.sender_id
                    != sender_id
                ):
                    print(
                        "INVALID READ RECEIPT SENDER:",
                        sender_id,
                    )
                    continue

                print(
                    "MESSAGE READ:",
                    message.id,
                    "BY USER:",
                    user_id,
                )

                await manager.send_to_user(
                    message.sender_id,
                    {
                        "type": "message_read",
                        "message_id": message.id,
                        "reader_id": user_id,
                    },
                )

                print(
                    "READ RECEIPT SENT:",
                    message.id,
                )

            # ==================================================
            # TYPING
            # ==================================================

            elif kind == "typing":

                receiver_id = data.get(
                    "receiver_id"
                )

                if not isinstance(
                    receiver_id,
                    int,
                ):
                    continue

                await manager.send_to_user(
                    receiver_id,
                    {
                        "type": "typing",
                        "sender_id": user_id,
                        "is_typing": bool(
                            data.get(
                                "is_typing"
                            )
                        ),
                    },
                )

            # ==================================================
            # UNKNOWN EVENT
            # ==================================================

            else:
                print(
                    "UNKNOWN WEBSOCKET EVENT:",
                    kind,
                )

    # --------------------------------------------------------
    # DISCONNECT
    # --------------------------------------------------------

    except WebSocketDisconnect:
        print(
            "WEBSOCKET DISCONNECTED:",
            user_id,
        )

    except Exception as exc:
        print(
            "WEBSOCKET ERROR:",
            repr(exc),
        )

    # --------------------------------------------------------
    # CLEANUP
    # --------------------------------------------------------

    finally:

        if user_id is not None:

            manager.disconnect(
                user_id,
                websocket,
            )

            if not manager.is_online(
                user_id
            ):
                await manager.broadcast(
                    {
                        "type": "presence",
                        "user_id": user_id,
                        "is_online": False,
                    }
                )

        db.close()

        print(
            "WEBSOCKET CLEANUP:",
            user_id,
        )