Information Integrity Command & Control Centre (IICCC)
Version:** 2.0 (Prototype)
Status:** Live Demo Stable

Project Overview
This system is a real-time misinformation surveillance dashboard. It uses AI to monitor media feeds, classify threats (Scams, Deepfakes, Clickbait), and visualize them for command centre analysts.

Architecture
Frontend: Streamlit (`dashboard.py`)
Backend: Python Script (`listener.py`)
Database: SQLite (`fake_news.db`)
AI Engine: Groq Cloud (Llama 3.1 8b-instant) - given in listerner.py code

Quick Start Guide

1. Prerequisites
* Python 3.12+
* Pip (Python Package Manager)
open requirements.txt and download all the given dependencies.

2. Installation
Run the following command to install dependencies:
```bash
pip install -r requirements.txt