# Codex Smart Auto-Resume Script

An interactive Python automation script for M1/M2/M3 Macs that automatically resumes a local Codex/ChatGPT thread after a rate limit reset.

## Quick Start / How to Run

1. Open **Terminal** and navigate to this project folder:
   ```bash
   cd chatgpt-autoresume
   ```

2. Run the following commands to activate the virtual environment and start the script with sleep prevention (`caffeinate`):
   ```bash
   source venv/bin/activate
   caffeinate -i python3 resume_codex_thread.py
   ```

3. Enter your **Thread ID** and desired **Target Wake Time** (`HH:MM` in 24-hour format, e.g. `04:32` or `16:32`) when prompted.
