# AI Analyst Agent -- Structured News Extraction

## 🚀 Features Implemented

### ✅ 1. News Ingestion

The system fetches real-time news using **NewsAPI** (API key
configurable via environment variable).

### ✅ 2. Structured Extraction (LLM-Powered)

Each article is processed using an LLM to extract:

``` json
{
  "company_name": "OpenAI",
  "category": "Video AI",
  "sentiment_score": 0.8,
  "is_funding_news": false
}
```

### ✅ 3. Hybrid Architecture

-   **GPT Mini** (OpenAI) is used as the primary model.\
-   If the usage limit is reached or API fails → automatically switches
    to **local Ollama Llama3**.

### ✅ 4. Clean Logging, Modular Code & PEP8 Compliance

The project follows Python best practices: - Modular structure\
- Logger integrated\
- Error handling & fallback architecture\
- Clear folder layout

### ✅ 5. Reproducibility

Includes: - `requirements.txt` - `.env.example` (optional) - This
README\
Everything can be reproduced easily.

------------------------------------------------------------------------

## 📂 Project Structure

    ai-analyst-agent/
    │── backend/
    │   ├── app.py
    │   ├── llm_handler.py
    │   ├── news_fetcher.py
    │   ├── extractors/
    │   │   ├── structured_extractor.py
    │   ├── utils/
    │   │   ├── logger.py
    │── requirements.txt
    │── README.md

------------------------------------------------------------------------

## 🛠️ Setup Instructions

### 🔧 1. Clone the Repository

    git clone <your-repo-url>
    cd ai-analyst-agent

### 🔧 2. Create Virtual Environment

    python -m venv venv
    source venv/bin/activate     # macOS/Linux
    venv\Scripts\activate        # Windows

### 🔧 3. Install Dependencies

    pip install -r requirements.txt

### 🔧 4. Add API Keys

Set your NewsAPI key:

    setx NEWSAPI_KEY "your_key_here"   # Windows
    export NEWSAPI_KEY="your_key_here" # macOS/Linux

Optional: Add to `.env`

    NEWSAPI_KEY=your_key_here

### 🔧 5. Install and Run Ollama (Optional Fallback)

    ollama run llama3
    ollama list

Make sure the model exists:

    ollama pull llama3

------------------------------------------------------------------------

## ▶️ Running the App

    python -m src.main 

Outputs will be saved inside the data folder as final_output.csv.

------------------------------------------------------------------------

## 📹 Demo Video 

https://www.youtube.com/watch?v=coAuH0eMKwE

------------------------------------------------------------------------

## 🧠 Why These Libraries/Models?

### 🟦 NewsAPI

-   Fast, reliable news aggregator
-   Free tier supports this task

### 🟩 GPT Mini (OpenAI)

-   High-quality structured extraction
-   Faster + lower cost

### 🟧 Ollama + Llama3

-   Local fallback (no token usage)
-   Ensures reliability even without API

### 🟨 Python + Requests + Logging

-   Lightweight
-   Easy to maintain
-   Industry standard and PEP8-compliant

------------------------------------------------------------------------


