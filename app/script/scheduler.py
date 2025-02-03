from apscheduler.schedulers.background import BackgroundScheduler

from apscheduler.triggers.cron import CronTrigger
# from apscheduler.triggers.interval import IntervalTrigger
from fastapi import  HTTPException

from datetime import datetime
import subprocess
from pymongo.database import Database
from fastapi import HTTPException
from threading import Thread
from .models import ScheduledScriptInDB,Frequency
from db import get_database
from datetime import datetime
from pytz import timezone

import threading
import queue
import time
import concurrent.futures
from dotenv import load_dotenv
load_dotenv() 

# MongoDB collections
SCRIPTS_SCHEDULE_COLLECTION = "scheduler"
SCRIPTS_COLLECTION = "scripts"
current_schedules={}
_scheduler_instance = None
# Limit concurrent executions (adjust based on VPS resources)
MAX_CONCURRENT_SCRIPTS = 5
semaphore = threading.Semaphore(MAX_CONCURRENT_SCRIPTS)

# Queue for scripts that exceed the max limit
script_queue = queue.Queue()
def get_scheduler():
    """Returns a global instance of the APScheduler."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = BackgroundScheduler()
        _scheduler_instance.start()
    return _scheduler_instance

def run_script(script_path):
    print("""Run a Python script with limited parallel execution.""",script_path)
    slot_status= semaphore.acquire(blocking=False)
    print(slot_status,script_path)
    if slot_status:  # Check if a slot is available
        try:
            print(f"[INFO] Running script: {script_path}")
            # Local
            subprocess.run(
                ["/Users/meetvelani/Desktop/codebase/bidsinfoglobal/ScriptAdmin/.venv/bin/python3", script_path],
                check=True
            )

            #server
            # subprocess.run(
            #     ["/var/lib/jenkins/workspace/script-admin-backend/.venv/bin/python3", script_path],
            #     check=True
            # )
            print(f"[INFO] Script {script_path} completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Error occurred while running {script_path}: {e}")
            handle_script_error(script_path, str(e))
            process_queue()  # Check if any queued scripts can run
        finally:
            semaphore.release()  # Release slot after script completes
            process_queue()  # Check if any queued scripts can run
    else:
        print(f"[QUEUE] Max scripts running. Adding {script_path} to queue.")
        script_queue.put(script_path)

def process_queue():
    print( """Process queued scripts when slots become available.""" )
    while not script_queue.empty():
        if semaphore._value < MAX_CONCURRENT_SCRIPTS:  # Check for an open slot
            script_path = script_queue.get()
            run_script(script_path)
        else:
            break  # No available slots, exit loop

def handle_script_error(script_path, error_message):
    

    # Example 2: Perform a MongoDB query
    try:
        database = get_database()

        collection = database["error_logs"]

        error_document = {
            "script_path": script_path,
            "error_message": error_message,
            "status": "failed",
        }
    
        result = database[SCRIPTS_COLLECTION].update_one({"script_file_path":script_path},{"$set": {"status": False,"recent_logs":error_message}})
        result = database[SCRIPTS_SCHEDULE_COLLECTION].delete_one({"script_file_path":script_path})
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Script with the given name not found."
            )

        collection.insert_one(error_document)
        print("[INFO] Error logged successfully to MongoDB.",script_path,collection)
        print("[INFO] Error logged successfully to MongoDB.")
    except Exception as mongo_exception:
        print(f"[ERROR] Exception occurred while logging to MongoDB: {mongo_exception}")


def get_cron_trigger(frequency: Frequency, hour: int, minute: int, custom_days: int = None):
    """
    Returns a CronTrigger based on the selected frequency.

    Args:
        frequency (Frequency): The scheduling frequency.
        hour (int): The hour of execution.
        minute (int): The minute of execution.
        timezone (str): The timezone string.
        custom_days (int, optional): Number of days for custom interval (only required if frequency is "custom").

    Returns:
        CronTrigger: An APScheduler CronTrigger object.
    """
    ist_timezone = timezone("Asia/Kolkata")




    if frequency == Frequency.daily:
        return CronTrigger(hour=hour, minute=minute, timezone=ist_timezone)

    elif frequency == Frequency.weekly:
        return CronTrigger(day_of_week="1", hour=hour, minute=minute, timezone=ist_timezone)  # Every Sunday

    elif frequency == Frequency.monthly:
        return CronTrigger(day="1", hour=hour, minute=minute, timezone=ist_timezone)  # 1st of every month

    elif frequency == Frequency.custom:
        if not custom_days or custom_days < 1:
            raise ValueError("For 'custom' frequency, custom_days must be provided and should be at least 1.")
        return CronTrigger(day=f"*/{custom_days}", hour=hour, minute=minute, timezone=ist_timezone)

    else:
        raise ValueError("Invalid frequency type.")
    

def schedule_script(db: Database, script_id, script_name, script_path, schedule_time,frequency=None,custom_days=None):
    # return "ee"
    print(f"[INFO] Scheduling script: {script_path} at {schedule_time}")
    scheduler = get_scheduler()
    print("*************************** *schedule_script *******************************")
    # Get current time
    current_time = datetime.now().strftime('%H:%M:%S')
    print("Current Time:", current_time)

    try:
        # Convert schedule_time to HH:MM if it's not a string
        if isinstance(schedule_time, datetime):
            schedule_time_str = schedule_time.strftime("%H:%M")
        else:
            schedule_time_str = schedule_time
    except Exception as e:
        print(f"[ERROR] Invalid schedule_time: {schedule_time}. Error: {e}")
        return

    # Remove any existing schedule for this script
    unschedule_script(scheduler, script_id)

    script_data = {
        "script_id": script_id,
        "script_name": script_name,
        "script_file_path": script_path,
        "schedule_time": schedule_time_str
    }

    # Save or update schedule in the database
    print("*************************** *schedule_script find_one*******************************")

    result = db[SCRIPTS_SCHEDULE_COLLECTION].find_one({"script_id": script_id})
    if not result:
        print("*************************** *schedule_script insert_one*******************************")
        db[SCRIPTS_SCHEDULE_COLLECTION].insert_one(script_data)
    else:
        db[SCRIPTS_SCHEDULE_COLLECTION].update_one({"script_id": script_id}, {"$set": script_data})

    ist_timezone = timezone("Asia/Kolkata")
    hour, minute = map(int, schedule_time_str.split(":"))
    if frequency:
        if frequency == Frequency.one_time:

            thread = threading.Thread(target=run_script,args=[script_path])
            thread.start()  # Start the thread
        else:
            scheduler.add_job(run_script, get_cron_trigger(frequency,hour,minute,custom_days), args=[script_path], id=str(script_id))
    else:
        scheduler.add_job(run_script, CronTrigger(hour=hour, minute=minute,timezone=ist_timezone), args=[script_path], id=str(script_id))
    # scheduler.add_job(run_script, 'interval', seconds=30,args=[script_path],id=script_id)
 

    # Update the mapping
    current_schedules[script_id] = schedule_time_str
    print(f"[INFO] Successfully scheduled {script_path} at {schedule_time_str}.")
    # return True

def remove_schedule_script(db: Database, script_id, script_name):
    try:
        print(f"[INFO] Remove from Scheduling script: {script_name}")
        scheduler = get_scheduler()

        # Remove any existing schedule for this script
        unschedule_script(scheduler, script_id)

        # Save or update schedule in the database
        print("*************************** *schedule_script delete_one*******************************")
        db[SCRIPTS_SCHEDULE_COLLECTION].delete_one({"script_id": script_id})
        return {
            "status":"success",
            "message":"Script removed successfully"
        }
    except Exception as e:
        return {
            "status":"error",
            "message":"Error during script remove:{e} "
        }

def unschedule_script(scheduler, script_id):
    """Remove any existing schedule for a given script ID."""
    print(f"[INFO] Unscheduling script with ID: {script_id}")
    try:
        if script_id in current_schedules:
            scheduler.remove_job(job_id=str(script_id))
            current_schedules.pop(script_id, None)
            print(f"[INFO] Unscheduled script with ID: {script_id}.")
        else:
            print(f"[WARN] No existing schedule found for script ID: {script_id}.")
    except Exception as e:
        print(f"[ERROR] Failed to unschedule script ID: {script_id}. Error: {e}")


def initialize_schedules( db: Database):
    """
    Fetch all scripts from the database and schedule them.
    :param scheduler: The APScheduler instance.
    :param db: The database instance.
    """
    print("[INFO] Initializing schedules from the database..")
    try:
        scripts_cursor = db[SCRIPTS_SCHEDULE_COLLECTION].find()
      
        scripts = list(scripts_cursor)
        print(len(scripts))
        

        for script in scripts:
            script["_id"] = str(script["_id"])
            script_obj = ScheduledScriptInDB(**script)

            if script["script_file_path"] and script["schedule_time"]:
                try:
                    try:
                        schedule_script(
                            db,
                            script["script_id"],
                            script["script_name"],
                            script["script_file_path"],
                            script["schedule_time"],
                            script["frequency"],
                            script["interval_days"],
                        )
                    except:
                        schedule_script(
                            db,
                            script["script_id"],
                            script["script_name"],
                            script["script_file_path"],
                            script["schedule_time"],
                         
                        )
                    print(f"[INFO] Scheduled script: {script_obj.script_name}")
                except Exception as e:
                    print(f"[ERROR] Failed to schedule script {script_obj.script_name}: {e}")
            else:
                print(f"[WARNING] Script {script_obj.script_name} is missing schedule_time or file path.")
    except Exception as e:
        print(f"[ERROR] Error initializing schedules: {e}")

# Start queue processing in a background thread
def queue_worker():
    print( """Continuously check and run queued scripts.""")
    while True:
        process_queue()
        time.sleep(5)  # Check every 5 seconds

# Start queue worker in a separate thread
# threading.Thread(target=queue_worker, daemon=True).start()