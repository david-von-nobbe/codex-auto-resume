import time
import sys
from datetime import datetime, timedelta
from openai_codex import Codex

def resume_local_thread():
    print("--- Codex Interactive Auto-Resume Script ---")
    
    # 1. Interactive User Inputs
    thread_input = input("Enter Thread ID or full URL (e.g., 01a12d09-...): ").strip()
    # Extract clean UUID if a full codex:// URL was pasted
    thread_id = thread_input.split("/")[-1] if "/" in thread_input else thread_input
    
    time_input = input("Enter target wake time (HH:MM in 24-hour format, e.g. 04:32 or 16:32): ").strip()
    
    try:
        parsed_time = datetime.strptime(time_input, "%H:%M")
        target_hour = parsed_time.hour
        target_minute = parsed_time.minute
    except ValueError:
        print("Error: Invalid time format. Please use HH:MM (e.g. 04:32 or 16:32). Exiting.")
        sys.exit(1)

    prompt_text = "Du wurdest durch das Ratenlimit unterbrochen. Bitte fahre exakt an der Stelle fort, an der du aufgehört hast."

    # 2. Precise Sleep Calculation
    now = datetime.now()
    target_datetime = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    # If the target time has already passed today, target that time tomorrow
    if now >= target_datetime:
        target_datetime += timedelta(days=1)
        
    sleep_seconds = (target_datetime - now).total_seconds()
    
    print(f"\n[Info] Current time: {now.strftime('%H:%M:%S')}")
    print(f"[Info] Target wake time: {target_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[Info] Sleeping for {sleep_seconds / 3600:.2f} hours (plus 1-min safety buffer)...")
    
    # Sleep precisely until target time + 60s safety buffer
    time.sleep(sleep_seconds + 60)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Waking up to attempt resuming thread {thread_id}...")

    # 3. Retry loop (Max 3 attempts)
    max_attempts = 3
    attempt = 1
    
    while attempt <= max_attempts:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Attempt {attempt} of {max_attempts}...")
        try:
            with Codex() as codex:
                thread = codex.get_thread(thread_id)
                print("Sending resume prompt...")
                response = thread.run(prompt_text)
                
                print("\n--- Success! Prompt sent and response received ---")
                print(response.text[:200] + "...")
                return
        except Exception as e:
            print(f"Attempt {attempt} failed. Reason: {e}")
            if attempt < max_attempts:
                print("Waiting 5 minutes before retrying...")
                time.sleep(300)
            attempt += 1

    print("\n[Error] Failed to resume the chat thread after 3 attempts. Giving up.")

if __name__ == "__main__":
    resume_local_thread()
