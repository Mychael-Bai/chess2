
import psutil
import time
import os

def monitor_ai_thread():
    # Initialize previous thread ID
    prev_thread_id = None
    
    while True:
        # Read current AI thread ID
        try:
            with open('ai_thread.log', 'r') as f:
                content = f.read().strip()
                current_thread_id = int(content) if content else None
        except (FileNotFoundError, ValueError):
            current_thread_id = None

        # If we have a new thread ID
        if current_thread_id and current_thread_id != prev_thread_id:
            print(f"\n\nNew AI thread detected: {current_thread_id}")
            print("Thread details:")
            
            # Find the thread in all Python processes
            for proc in psutil.process_iter(['pid', 'name']):
                if 'python' in proc.info['name'].lower():
                    try:
                        p = psutil.Process(proc.info['pid'])
                        for thread in p.threads():
                            if thread.id == current_thread_id:
                                print(f"Process ID: {proc.info['pid']}")
                                print(f"Process Name: {proc.info['name']}")
                                print(f"Thread ID: {thread.id}")
                                print(f"Thread CPU Time: {thread.user_time + thread.system_time:.2f}s")
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

        # Update previous thread ID
        prev_thread_id = current_thread_id
        
        # Print status every 5 iterations
        iteration_count = 0
        if iteration_count % 5 == 0:
            if current_thread_id:
                print(f"\rMonitoring AI thread: {current_thread_id}", end='')
            else:
                print("\rWaiting for AI thread...", end='')
        
        iteration_count += 1
        if iteration_count >= 20:  # Stop after 20 iterations
            break
            
        time.sleep(0.5)

if __name__ == "__main__":
    print("Starting AI thread monitor...")
    print("Will monitor for 10 seconds")
    monitor_ai_thread()
    print("\nMonitoring complete")