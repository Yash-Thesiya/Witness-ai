# 👁 Witness — AI Commitment Tracker

> An AI-powered system that automatically extracts, tracks, and manages commitments from meeting transcripts and audio recordings. Never miss a deadline again.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Commitment Lifecycle](#commitment-lifecycle)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Usage Guide](#usage-guide)
- [License](#license)

---

## Overview

**Witness** is a full-stack AI application built as an internship project. It solves a common problem in teams and individuals — commitments made in meetings, calls, and conversations are often forgotten or not tracked properly.

Witness automatically:
- Transcribes audio recordings using **Whisper AI**
- Extracts commitments from text using **LLM (OpenRouter)**
- Tracks each commitment through its full lifecycle
- Detects fulfillment and missed deadlines automatically
- Provides dashboards, calendar views, and accountability reports

---

## Features

### Core Features
- 🎙 **Audio Transcription** — Upload MP3, WAV, M4A files. Whisper AI converts speech to text automatically in the background
- 📄 **Transcript Upload** — Upload TXT, PDF, DOCX files. Text is extracted and processed instantly
- 🤖 **AI Commitment Extraction** — LLM reads transcripts and extracts structured commitments (owner, action, due date, confidence score)
- 🔄 **State Machine** — Full commitment lifecycle: Detected → Active → Fulfilled / Missed / Modified / Cancelled
- 🧠 **Cross-Transcript Detection** — System detects fulfillment and modifications across multiple transcript uploads
- ⏰ **Auto Activation** — Commitments auto-promote from Detected → Active after 2 hours if no manual action
- 📅 **Missed Detection** — Celery Beat runs hourly to mark overdue commitments as Missed automatically

### Dashboard & UI
- 📊 **Dashboard** — Real-time stats cards (Active, Detected, Fulfilled, Missed), donut pie chart, upcoming due-soon list
- 📅 **Calendar View** — FullCalendar.js integration with Month/Week/List views, color-coded by status, click to view detail
- 📋 **Commitments Explorer** — Searchable, filterable table with owner, action, due date, status, confidence
- 📈 **Accountability Report** — Per-owner breakdown with fulfillment rate, progress bars, CSV export
- 🔍 **Commitment Detail** — Summary, status update buttons, auto-activation notice, full event timeline

### Security
- 🔐 JWT Authentication (Register / Login / Logout)
- 🔒 Password hashing with bcrypt
- 🛡️ Protected routes — all endpoints require valid token
- 📁 Private file access — users can only view their own uploads

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI |
| **Frontend** | NiceGUI |
| **Database** | PostgreSQL, SQLAlchemy, Alembic |
| **AI / ML** | OpenRouter API (LLaMA 3.1), faster-whisper (Whisper tiny) |
| **Background Jobs** | Celery, Celery Beat, Redis |
| **Auth** | JWT (python-jose), bcrypt (passlib) |
| **File Processing** | pypdf, python-docx, python-multipart |
| **Deployment** | Docker, Docker Compose, Render |
| **Charts** | ECharts, FullCalendar.js |

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    User Browser                      │
│              http://localhost:8080                   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              NiceGUI Frontend                        │
│   Dashboard │ Commitments │ Calendar │ Report        │
│   Upload │ Login/Register                            │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP API calls
┌──────────────────────▼──────────────────────────────┐
│              FastAPI Backend                         │
│   /auth  │  /uploads  │  /commitments               │
│   JWT Auth │ Business Logic │ AI Orchestration       │
└──────┬───────────────┬──────────────────────────────┘
       │               │
┌──────▼──────┐  ┌─────▼──────────────────────────────┐
│ PostgreSQL  │  │         Redis + Celery               │
│  Database   │  │  Worker │ Beat │ Tasks               │
│  6 Tables   │  │  - transcribe_audio                  │
└─────────────┘  │  - extract_commitments               │
                 │  - auto_activate_commitments          │
                 │  - check_missed_commitments           │
                 └──────────────┬─────────────────────┘
                                │
                 ┌──────────────▼─────────────────────┐
                 │         External APIs               │
                 │  OpenRouter API (LLM Extraction)    │
                 │  Whisper (Audio Transcription)      │
                 └────────────────────────────────────┘
```

---

## Commitment Lifecycle

```
Audio/Transcript Upload
         │
         ▼
   ┌─────────────┐
   │  DETECTED   │  ← AI extracted this commitment
   └──────┬──────┘
          │  Manual confirm OR 2 hours auto
          ▼
   ┌─────────────┐
   │   ACTIVE    │  ← Actively being tracked
   └──────┬──────┘
          │
     ┌────┴─────┬──────────┬───────────┐
     ▼          ▼          ▼           ▼
┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│FULFILLED│ │ MISSED │ │MODIFIED│ │CANCELLED │
│(Terminal│ │        │ │        │ │(Terminal)│
└─────────┘ └───┬────┘ └───┬────┘ └──────────┘
                │           │
                ▼           ▼
          ┌─────────┐   ┌──────┐
          │FULFILLED│   │ACTIVE│
          │(late)   │   │      │
          └─────────┘   └──────┘

Auto Detection:
- Fulfillment → New transcript with completion evidence
- Missed      → Celery Beat hourly check (due_date passed)
- Modified    → New transcript with deadline change evidence
```

---

## Project Structure

```
witness/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          # App settings from .env
│   │   │   ├── security.py        # JWT + bcrypt
│   │   │   ├── dependencies.py    # get_current_user dependency
│   │   │   ├── ai_extractor.py    # OpenRouter LLM calls + prompts
│   │   │   ├── commitment_matcher.py  # Fuzzy matching logic
│   │   │   ├── state_machine.py   # Commitment state transitions
│   │   │   └── file_handler.py    # File save + text extraction
│   │   ├── db/
│   │   │   └── database.py        # SQLAlchemy engine + session
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── upload.py
│   │   │   ├── recording.py
│   │   │   ├── transcript.py
│   │   │   ├── commitment.py
│   │   │   ├── commitment_event.py
│   │   │   └── enums.py
│   │   ├── routers/
│   │   │   ├── auth.py            # /auth endpoints
│   │   │   ├── upload.py          # /uploads endpoints
│   │   │   └── commitments.py     # /commitments endpoints
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── upload.py
│   │   │   └── commitment.py
│   │   ├── tasks/
│   │   │   ├── transcription.py   # Whisper audio → text
│   │   │   ├── extraction.py      # LLM commitment extraction
│   │   │   ├── auto_activator.py  # DETECTED → ACTIVE after 2hrs
│   │   │   └── missed_checker.py  # Hourly missed detection
│   │   ├── celery_app.py          # Celery + Beat schedule
│   │   └── main.py                # FastAPI app entry point
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── 0001_initial.py    # All 6 tables
│   │   │   └── 0002_add_processing_status.py
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── app/
│       ├── pages/
│       │   ├── login.py           # Login + Register
│       │   ├── dashboard.py       # Stats + pie chart + due soon
│       │   ├── upload.py          # Drag & drop upload
│       │   ├── commitments.py     # Explorer + Detail page
│       │   ├── calendar.py        # FullCalendar.js view
│       │   └── report.py          # Accountability report
│       ├── theme.py               # Global color theme
│       ├── api.py                 # Backend API client
│       ├── state.py               # Global app state (token)
│       └── main.py                # NiceGUI routes + entry point
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Setup & Installation

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [OpenRouter API Key](https://openrouter.ai/) (free tier available)
- Git

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/witness.git
cd witness
```

### Step 2 — Create environment file

```bash
cp .env.example .env
```

### Step 3 — Fill in your `.env` file

Open `.env` and fill in the values (see [Environment Variables](#environment-variables) section below).

### Step 4 — Build and start containers

```bash
docker-compose up --build
```

First build will take a few minutes (downloads Whisper model ~150MB).

You should see 5 containers start:
```
✔ Container witness_db          Healthy
✔ Container witness_redis       Healthy
✔ Container witness_backend     Started
✔ Container witness_celery      Started
✔ Container witness_celery_beat Started
✔ Container witness_frontend    Started
```

### Step 5 — Run database migrations

```bash
docker-compose exec backend alembic upgrade head
```

Expected output:
```
INFO Running upgrade  -> 0001_initial
INFO Running upgrade 0001_initial -> 0002_add_processing_status
```

### Step 6 — Open in browser

| Service | URL |
|---------|-----|
| **Frontend (Main App)** | http://localhost:8080 |
| **API Documentation** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |

---

## Environment Variables

```env
# ── PostgreSQL ──────────────────────────────────────
POSTGRES_USER=witness
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=witness_db

# ── Backend ─────────────────────────────────────────
DATABASE_URL=postgresql://witness:your_strong_password@db:5432/witness_db
SECRET_KEY=your-very-long-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENVIRONMENT=development

# ── Redis + Celery ───────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── OpenRouter AI ────────────────────────────────────
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

> ⚠️ **Never commit your `.env` file to GitHub.** It is already in `.gitignore`.

---

## API Documentation

FastAPI provides automatic interactive docs at `http://localhost:8000/docs`.

### Auth Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, get JWT token |
| POST | `/auth/logout` | Logout (client-side) |
| GET | `/auth/me` | Get current user info |

### Upload Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/uploads/transcript` | Upload TXT/PDF/DOCX |
| POST | `/uploads/audio` | Upload MP3/WAV/M4A |
| GET | `/uploads/` | List user's uploads |
| GET | `/uploads/{id}` | Get upload detail |

### Commitment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/commitments/` | List commitments (with filters) |
| GET | `/commitments/dashboard` | Dashboard stats |
| GET | `/commitments/report/accountability` | Per-owner report |
| GET | `/commitments/{id}` | Commitment detail + timeline |
| PATCH | `/commitments/{id}/status` | Update commitment status |

---

## Usage Guide

### 1. Register & Login
- Open `http://localhost:8080`
- Create an account and sign in

### 2. Upload a Transcript
- Go to **Upload** page
- Drag & drop a `.txt`, `.pdf`, or `.docx` file
- AI will automatically extract commitments in the background

**Example transcript content:**
```
Project Status Meeting - June 28, 2026

John: I will send the project report by Friday.
Sarah: The API documentation review is completed.
Mike: I need until next Monday to finish the database migration.
Emma: I will share the meeting notes tomorrow morning.
```

### 3. Upload an Audio File
- Upload an `.mp3`, `.wav`, or `.m4a` recording
- Whisper AI transcribes it automatically
- Commitments are extracted from the transcript

### 4. View Commitments
- Go to **Commitments** page
- Search by action, filter by owner or status
- Click **View** to see detail and timeline

### 5. Manage Commitment Status
- On the detail page, use the action buttons:
  - **Confirm & Activate** — manually activate a detected commitment
  - **Mark Fulfilled** — mark as completed
  - **Cancel** — cancel the commitment
- Or upload a new transcript with fulfillment evidence — the system auto-detects it

### 6. Track with Calendar
- Go to **Calendar** page
- View all commitment due dates on a monthly/weekly/list view
- Click any event to see details

### 7. View Accountability Report
- Go to **Report** page
- See per-owner breakdown: total, active, fulfilled, missed, rate
- Export to CSV with one click

---

## Database Schema

```
Users
  id, email, password_hash, created_at

Uploads
  id, user_id, file_name, file_type, processing_status, created_at

Recordings
  id, upload_id, audio_path, duration, created_at

Transcripts
  id, upload_id, content, created_at

Commitments
  id, owner, action, due_date, status, confidence_score,
  source_transcript_id, created_at, updated_at

CommitmentEvents
  id, commitment_id, event_type, event_data, created_at
```

---

## Background Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `transcribe_audio` | On upload | Whisper converts audio → transcript |
| `extract_commitments` | After transcription | LLM extracts commitments from transcript |
| `auto_activate_commitments` | Every 30 min | DETECTED → ACTIVE after 2 hours |
| `check_missed_commitments` | Every hour | ACTIVE → MISSED if due date passed |

---

## License

```
MIT License

Copyright (c) 2026 Witness

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<div align="center">
  <p>Built with ❤️ using FastAPI, NiceGUI, and AI</p>
  <p>© 2026 Witness — AI Commitment Tracker</p>
</div>
