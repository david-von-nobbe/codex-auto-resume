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

    default_prompt = "Du wurdest durch das Ratenlimit unterbrochen. Bitte fahre exakt an der Stelle fort, an der du aufgehört hast."
    
    # Custom prompt input with fallback
    custom_prompt = input("\nEnter prompt (or press ENTER to use default resume message):\n> ").strip()
    prompt_text = custom_prompt if custom_prompt else default_prompt
    
    print(f"\n[Info] Using prompt: \"{prompt_text}\"")

    # 2. Precise Sleep Calculation
    now = datetime.now()
    target_datetime = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    if now >= target_datetime:
        target_datetime += timedelta(days=1)
        
    sleep_seconds = (target_datetime - now).total_seconds()
    
    print(f"[Info] Current time: {now.strftime('%H:%M:%S')}")
    print(f"[Info] Target wake time: {target_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[Info] Sleeping for {sleep_seconds / 3600:.2f} hours (plus 1-min safety buffer)...")
    
    time.sleep(sleep_seconds + 60)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Waking up to attempt resuming thread {thread_id}...")

    # 3. Retry Loop with Server Warm-Up & Timeout Protection
    max_attempts = 3
    attempt = 1
    
    while attempt <= max_attempts:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Attempt {attempt} of {max_attempts}...")
        
        # Clear any existing lock file
        release_thread_lock(thread_id)
        
        try:
            with Codex() as codex:
                print("Warming up local Codex daemon...")
                thread = codex.thread_resume(thread_id)
                
                # Give the local server 3 seconds to fully initialize the thread session
                time.sleep(3)
                
                print("Sending resume prompt (with 30s timeout)...")
                
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(thread.run, prompt_text)
                    response = future.result(timeout=30)
                
                print("\n--- Success! Prompt sent and response received ---")
                if hasattr(response, 'final_response') and response.final_response:
                    print(response.final_response[:200] + "...")
                else:
                    print(str(response)[:200])
                return
                
        except TimeoutError:
            print(f"Attempt {attempt} timed out. Server hung or rate limit still active.")
        except Exception as e:
            print(f"Attempt {attempt} failed. Reason: {e}")
            
        if attempt < max_attempts:
            print("Waiting 5 minutes before retrying...")
            time.sleep(300)
        attempt += 1

    print("\n[Error] Failed to resume the chat thread after 3 attempts. Giving up.")

if __name__ == "__main__":
    resume_local_thread()
