# 💬 MCP Assistant Playground

A Streamlit-based chatbot interface powered by OpenAI GPT-4o that intelligently routes user input to custom MCP tools such as GPT chat, image generation, Supabase queries, and text-to-speech.

Built for rapid experimentation with AI-powered tool routing, inspired by Claude-style confirmation flows.

---

## ✨ Features

- Natural language tool selection using GPT-4o
- MCP tool execution via `fastmcp`
- Real-time OpenAI image generation (DALL·E 3)
- Text-to-speech audio synthesis (GPT-4o mini TTS)
- Supabase integration for member CRUD operations
- Streamlit UI with tool result rendering (image/audio)

---

## 🛠️ Prerequisites

- Python 3.10+
- OpenAI API key
- Supabase project (optional, for member tools)

---

## 🧪 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/niawjunior/mcp-assistant-playground.git
cd mcp-assistant-playground
```

### 2. Set up virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root directory with the following variables:

```bash
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 5. Run the application

```bash
python app.py
```

### 6. Access the chat interface

Open your web browser and navigate to `http://localhost:8501`.

---
