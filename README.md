# Pulse Backend ⚡

The backend service for **Pulse**, a modern real-time messaging application built with **FastAPI, MySQL, SQLAlchemy, JWT authentication, and WebSockets**.

Pulse provides secure authentication, user management, real-time one-to-one messaging, online/offline presence, message delivery status, read receipts, and typing indicators.

---

## ✨ Features

### 🔐 Authentication

- User registration
- User login
- JWT access-token authentication
- Protected API endpoints
- Password hashing
- Current-user authentication
- Secure WebSocket authentication using JWT

### 👤 User Management

- Get authenticated user
- Retrieve available users
- User online/offline state
- User presence synchronization

### 💬 Real-Time Messaging

Pulse uses WebSockets for real-time communication.

Supported events include:

- Send messages
- Receive messages instantly
- Delivery synchronization
- Read receipts
- Typing indicators
- Online/offline presence
- WebSocket disconnect handling

### ✓ Message Status

Pulse supports message status progression:

```text
⚡ Sent
   ↓
⚡⚡ Delivered
   ↓
🟠⚡⚡ Seen
```

Only the message sender receives delivery/read status information.

### 🟢 Presence

The backend keeps track of connected users and broadcasts presence changes.

```text
User connects
     ↓
Authenticate JWT
     ↓
Register WebSocket connection
     ↓
Mark user online
     ↓
Broadcast presence
```

When a user disconnects:

```text
WebSocket disconnect
        ↓
Remove connection
        ↓
Mark user offline
        ↓
Broadcast presence
```

### ⌨️ Typing Indicators

Typing events are forwarded through the WebSocket connection so the frontend can display real-time typing status.

---

# 🏗️ Technology Stack

| Technology | Purpose |
|---|---|
| FastAPI | REST API and WebSocket server |
| Python | Backend language |
| MySQL | Relational database |
| SQLAlchemy | ORM/database access |
| Pydantic | Data validation and schemas |
| JWT | Authentication |
| WebSockets | Real-time communication |
| Uvicorn | ASGI server |
| Passlib / password hashing | Secure password storage |
| CORS | Frontend API access |

---

# 📁 Project Structure

A typical Pulse backend structure:

```text
pulse-backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── auth.py
│   │   ├── users.py
│   │   └── messages.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── dependencies.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── session.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   └── message.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   └── message.py
│   │
│   ├── websocket/
│   │   ├── manager.py
│   │   └── websocket.py
│   │
│   └── utils/
│       └── ...
│
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── run.py
```

> The exact folder names may differ depending on your local Pulse backend structure.

---

# ⚙️ Requirements

Before running the backend, install:

- Python 3.11+
- MySQL 8+
- pip
- Git

Check your Python version:

```bash
python --version
```

Check pip:

```bash
pip --version
```

---

# 🚀 Getting Started

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/pulse-backend.git
```

Enter the project:

```bash
cd pulse-backend
```

---

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

---

# 📦 Install Dependencies

Install all backend dependencies:

```bash
pip install -r requirements.txt
```

If you haven't created `requirements.txt` yet, your project will generally need packages such as:

```text
fastapi
uvicorn
sqlalchemy
pymysql
python-dotenv
pydantic
python-jose
passlib
bcrypt
```

Use the versions actually tested by your project rather than blindly copying these package names into production.

---

# 🗄️ Database Setup

Pulse uses MySQL.

Create a database:

```sql
CREATE DATABASE pulse;
```

You can verify it with:

```sql
SHOW DATABASES;
```

---

# 🔑 Environment Variables

Create a `.env` file in the backend root:

```env
DATABASE_URL=mysql+pymysql://USERNAME:PASSWORD@localhost:3306/pulse

SECRET_KEY=YOUR_SECRET_KEY

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Replace:

```text
USERNAME
PASSWORD
YOUR_SECRET_KEY
```

with your own values.

### ⚠️ Never commit `.env`

Your `.env` contains secrets and must remain local.

Add it to `.gitignore`:

```gitignore
.env
.env.*
```

---

# 🔐 Authentication Flow

Pulse uses JWT-based authentication.

The general flow is:

```text
Register
   ↓
Hash password
   ↓
Store user
   ↓
Login
   ↓
Verify credentials
   ↓
Create JWT
   ↓
Return access token
   ↓
Frontend stores token
   ↓
Token used for protected requests
```

Protected REST endpoints validate the JWT before processing the request.

---

# 🌐 REST API

The backend exposes REST endpoints for operations that don't require a persistent real-time connection.

Typical API groups include:

```text
/api/auth
/api/users
/api/messages
```

Examples of functionality:

### Authentication

```text
POST /api/auth/register
POST /api/auth/login
```

### Users

```text
GET /api/users
GET /api/users/me
```

### Messages

```text
GET /api/messages/{user_id}
```

> Endpoint names should match the actual routes configured in your application.

---

# ⚡ WebSocket

Pulse uses a WebSocket endpoint for real-time communication:

```text
/ws?token=ACCESS_TOKEN
```

The JWT token is supplied during the WebSocket connection.

Example:

```text
ws://localhost:8000/ws?token=YOUR_ACCESS_TOKEN
```

For production:

```text
wss://your-domain.com/ws?token=YOUR_ACCESS_TOKEN
```

---

# 🔌 WebSocket Events

Pulse currently supports several real-time event types.

## Send Message

Client sends:

```json
{
  "type": "message",
  "receiver_id": 2,
  "text": "Hello!"
}
```

The server validates the receiver and message content, stores the message, and sends the resulting message to the appropriate connected users.

---

## Read Receipt

Client can notify the server that a message has been read.

```json
{
  "type": "read",
  "message_id": 123
}
```

The backend forwards the read notification to the original sender.

---

## Typing

Example:

```json
{
  "type": "typing",
  "receiver_id": 2,
  "is_typing": true
}
```

The backend forwards the typing event to the receiver when connected.

---

# 🧠 WebSocket Connection Manager

Pulse uses a connection manager to maintain active WebSocket connections.

The manager is responsible for:

- Connecting users
- Disconnecting users
- Tracking active connections
- Sending messages
- Broadcasting presence
- Forwarding events to specific users

Conceptually:

```text
                    ┌──────────────┐
                    │ Connection   │
                    │   Manager    │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
       User A           User B           User C
       Online           Online           Offline
```

---

# 🟢 Presence System

When a user establishes a WebSocket connection:

```text
CONNECT
   ↓
JWT validation
   ↓
manager.connect()
   ↓
User becomes online
   ↓
Presence broadcast
```

When the connection closes:

```text
DISCONNECT
    ↓
manager.disconnect()
    ↓
User becomes offline
    ↓
Presence broadcast
```

This allows the frontend to update online indicators in real time.

---

# 💾 Message Persistence

Messages are stored in MySQL rather than existing only inside the WebSocket connection.

The basic lifecycle is:

```text
Frontend
   ↓
WebSocket
   ↓
FastAPI
   ↓
Validate message
   ↓
Create Message
   ↓
Database commit
   ↓
Broadcast message
   ↓
Sender + receiver receive event
```

This allows conversation history to remain available after refreshing the application.

---

# 🛡️ Security

Pulse follows several security practices:

- Passwords are never stored as plain text
- JWT authentication protects private resources
- WebSocket connections require authentication
- Input validation is performed using Pydantic
- Database access is handled through SQLAlchemy
- Secrets are stored in environment variables
- CORS is explicitly configured

### Production security checklist

Before deploying:

- Generate a strong random `SECRET_KEY`
- Use HTTPS
- Use secure WebSockets (`wss://`)
- Restrict CORS to trusted frontend domains
- Use a dedicated production database user
- Never commit `.env`
- Keep dependencies updated
- Disable debug mode
- Configure secure database credentials

---

# 🌍 CORS

During development, the backend can allow requests from the local frontend.

For example:

```text
http://localhost:5173
```

For production, replace development origins with the actual Pulse frontend domain.

Avoid using unrestricted origins in production unless there is a specific reason.

---

# ▶️ Running the Server

Start FastAPI with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

---

# 📚 API Documentation

FastAPI automatically provides interactive API documentation.

Swagger UI:

```text
/docs
```

ReDoc:

```text
/redoc
```

For example:

```text
http://127.0.0.1:8000/docs
```

These interfaces can be used to inspect and test API endpoints during development.

---

# 🧪 Testing

Before deploying, test:

### Authentication

- Register a user
- Login
- Invalid password
- Invalid token
- Expired token

### Users

- Retrieve users
- Retrieve current user
- Verify online status

### Messaging

- Send message
- Receive message
- Refresh conversation
- Verify message persistence
- Verify duplicate handling

### Delivery

- Sent status
- Delivered status
- Read status

### Presence

- Connect
- Disconnect
- Multiple users
- Reconnect

### WebSocket

- Valid token
- Invalid token
- Invalid receiver
- Empty message
- Disconnect/reconnect

---

# 🐳 Future Docker Support

Docker support can be added later for easier deployment.

A future production architecture could be:

```text
                  Internet
                     │
                     ▼
              ┌──────────────┐
              │ Reverse Proxy│
              │    Nginx     │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │    FastAPI   │
              │    Backend   │
              └──────┬───────┘
                     │
             ┌───────┴────────┐
             │                │
             ▼                ▼
        ┌─────────┐      ┌──────────┐
        │  MySQL  │      │ WebSocket│
        │ Database│      │ Clients  │
        └─────────┘      └──────────┘
```

---

# 📈 Future Features

Pulse's backend can be extended with:

- Message reactions
- Message replies
- Message editing
- Message deletion
- Unread message counts
- Attachments
- Image messages
- File messages
- Voice messages
- Message search
- Push notifications
- Message pagination
- Conversation pinning
- Message forwarding
- User blocking
- Conversation muting
- Last-seen timestamps
- Multi-device synchronization
- Redis-based WebSocket scaling
- Background jobs
- Rate limiting

---

# 🧩 Scaling Architecture

For a single-server deployment, in-memory WebSocket connections can be sufficient.

As Pulse grows to multiple backend instances, a shared real-time layer can be introduced:

```text
                 Load Balancer
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
       FastAPI     FastAPI     FastAPI
       Server 1    Server 2    Server 3
          │           │           │
          └───────────┼───────────┘
                      │
                      ▼
                   Redis
                      │
                      ▼
                    MySQL
```

Redis can provide shared pub/sub and presence coordination between backend instances.

---

# 🤝 Development Guidelines

When contributing to Pulse:

1. Keep authentication secure.
2. Validate all incoming data.
3. Do not expose secrets.
4. Keep WebSocket events predictable.
5. Avoid breaking existing message events.
6. Keep database operations transactional.
7. Test both REST and WebSocket behavior.
8. Keep frontend/backend contracts synchronized.

---

# 📝 Git Workflow

Create a feature branch:

```bash
git checkout -b feature/message-reactions
```

Make your changes and commit:

```bash
git add .
git commit -m "feat: add message reactions"
```

Push:

```bash
git push origin feature/message-reactions
```

Then create a Pull Request on GitHub.

---

# 📌 Commit Convention

Recommended commit prefixes:

```text
feat:     New feature
fix:      Bug fix
refactor: Code restructuring
docs:     Documentation
test:     Tests
chore:    Maintenance
perf:     Performance improvement
security: Security-related change
```

Examples:

```text
feat: add message reactions
fix: handle websocket disconnect
feat: add unread message tracking
refactor: improve websocket manager
docs: update API documentation
```

---

# 📄 License

No license has been added yet.

If Pulse is eventually released as open-source, add an appropriate license such as MIT, Apache-2.0, or another license that matches your intended usage.

---

# ⚡ Pulse

**Pulse** is built around one simple idea:

> Real-time communication should feel fast, clean, and effortless.

The backend provides the secure, real-time foundation that powers the Pulse messaging experience.

---

## Project Status

```text
Authentication       ✅
User Management      ✅
MySQL Persistence    ✅
REST API             ✅
WebSocket Messaging  ✅
Presence             ✅
Typing Indicators    ✅
Delivery Status      ✅
Read Receipts        ✅
Message History      ✅

Advanced Messaging   🚧
Attachments          🚧
Reactions            🚧
Notifications        🚧
Voice Messages       🚧
```

**Pulse Backend — Fast, Real-Time, Connected. ⚡**