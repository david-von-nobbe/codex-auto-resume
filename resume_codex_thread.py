import time
import sys
import glob
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from openai_codex import Codex

def release_thread_lock(thread_id):
    """Clears any active or stale local writer locks for the given thread."""
    lock_dir = os.path.expanduser("~/.codex/thread-writer-locks")
    if os.path.exists(lock_dir):
        matching_locks = glob.glob(f"{lock_dir}/*{thread_id}*")
        for lock_file in matching_locks:
            try:
                os.remove(lock_file)
                print(f"[Lock Manager] Removed active writer lock: {lock_file}")
            except Exception as e:
                print(f"[Lock Manager] Could not remove lock file: {e}")

def resume_local_thread():
    print("--- Codex Interactive Auto-Resume Script ---")
    
    # 1. User Inputs
    thread_input = input("Enter Thread ID or full URL (e.g., 01a12d09-...): ").strip()
    thread_id = thread_input.split("/")[-1] if "/" in thread_input else thread_input
    
    time_input = input("Enter target wake time (HH:MM in 24-hour format, e.g. 04:32 or 16:32): ").strip()
    
    try:
        parsed_time = datetime.strptime(time_input, "%H:%M")
        target_hour = parsed_time.hour
        target_minute = parsed_time.minute
    except ValueError:
        print("Error: Invalid time format. Please use HH:MM. Exiting.")
        sys.exit(1)

    prompt_text = "Du wurdest durch das Ratenlimit unterbrochen. Bitte fahre exakt an der Stelle fort, an der du aufgehört hast."

    # 2. Precise Sleep Calculation
    now = datetime.now()
    target_datetime = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    if now >= target_datetime:
        target_datetime += timedelta(days=1)
        
    sleep_seconds = (target_datetime - now).total_seconds()
    
    print(f"\n[Info] Current time: {now.strftime('%H:%M:%S')}")
    print(f"[Info] Target wake time: {target_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[Info] Sleeping for {sleep_seconds / 3600:.2f} hours (plus 1-min safety buffer)...")
    
    time.sleep(sleep_seconds + 60)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Waking up to attempt resuming thread {thread_id}...")

    # 3. Retry Loop with Timeout Protection (Max 3 attempts)
    max_attempts = 3
    attempt = 1
    
    while attempt <= max_attempts:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Attempt {attempt} of {max_attempts}...")
        
        # Clear the lock file before attempting to attach
        release_thread_lock(thread_id)
        
        try:
            with Codex() as codex:
                thread = codex.thread_resume(thread_id)
                print("Sending resume prompt (with a 30-second timeout)...")
                
                # Use ThreadPoolExecutor to prevent hanging if rate limit blocks the server
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(thread.run, prompt_text)
                    response = future.result(timeout=30)
                
                print("\n--- Success! Prompt sent and response received ---")
                # Correct attribute for openai-codex TurnResult
                if hasattr(response, 'final_response') and response.final_response:
                    print(response.final_response[:200] + "...")
                else:
                    print(str(response)[:200])
                return
                
        except TimeoutError:
            print(f"Attempt {attempt} timed out. Rate limit likely still active (server is hanging).")
        except Exception as e:
            print(f"Attempt {attempt} failed. Reason: {e}")
            
        if attempt < max_attempts:
            print("Waiting 5 minutes before retrying...")
            time.sleep(300)
        attempt += 1

    print("\n[Error] Failed to resume the chat thread after 3 attempts. Giving up.")

if __name__ == "__main__":
    resume_local_thread()
