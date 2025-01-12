import schedule
import time
from threading import Thread
from datetime import datetime
import subprocess
from bson import ObjectId
from pymongo import MongoClient
from fastapi import HTTPException
from pymongo.database import Database
from .models import ScheduledScriptInDB

# Mapping to track current schedules
current_schedules = {}
SCRIPTS_SCHEDULE_COLLECTION = "scheduler"


def run_script(script_path):
    """Run the Python script."""
    print(f"*********************[INFO] Running script: {script_path}")
    try:
        subprocess.run(["python3", script_path], check=True)
        print(f"[INFO] Script {script_path} completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error occurred while running {script_path}: {e}")

def schedule_script(db:Database,script_id,script_name,script_path, schedule_time):
    """
    Schedule the script to run at the specified time.
    :param script_path: Path to the Python script.
    :param schedule_time: Time in HH:MM (24-hour format).
    """
    print(f"[INFO] Scheduling script: {script_path} at {schedule_time}")
    schedule_time_str=schedule_time
    try:
        schedule_time_str = schedule_time.strftime("%H:%M")
    except:
        pass


    # Remove any existing schedule for this script
    unschedule_script(script_path)
    script_data = {"script_id":script_id,"script_name":script_name,"script_file_path": script_path, "schedule_time": schedule_time_str}
    result = db[SCRIPTS_SCHEDULE_COLLECTION].find_one(
        {"script_id": script_id},
        
    )
    print(result,"fffff")
    if not result:
        # Update the script with new schedule time
        result = db[SCRIPTS_SCHEDULE_COLLECTION].insert_one(script_data)
    else:
        result = db[SCRIPTS_SCHEDULE_COLLECTION].update_one(
            {"script_id": script_id},
            {"$set": script_data}
        )
  


    # Schedule the new time
    # schedule.every().day.at(schedule_time_str).do(run_script, script_path)
    schedule.every(10).seconds.do(run_script, script_path)

    # Update the mapp(ng
    current_schedules[script_path] = schedule_time_str
    print(schedule.get_jobs())
    print(f"[INFO] Successfully scheduled {script_path} at {schedule_time_str}.")

def unschedule_script(script_path):
    """Remove any existing schedule for a given script."""
    global current_schedules
    print(f"[INFO] Unscheduling script: {script_path}")
    
    if script_path in current_schedules:
        current_schedules.pop(script_path, None)
        schedule.clear()  # Clear all jobs
        print(f"[INFO] Unscheduled {script_path}.")
    else:
        print(f"[WARN] No existing schedule found for {script_path}.")

def start_scheduler():
    """Start the scheduler in a separate thread."""
    print("[INFO] Starting scheduler...")
    
    def run_scheduler():
        print("[INFO] Scheduler running...")
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("[INFO] Scheduler thread started.")





def initialize_schedules(db: Database):
    """
    Fetch all scripts from the database and schedule them.
    """
    try:
        # Retrieve all scripts from MongoDB
        scripts_cursor = db[SCRIPTS_SCHEDULE_COLLECTION].find()
        scripts = list(scripts_cursor)

        # Iterate and schedule each script
        for script in scripts:
            script["_id"] = str(script["_id"])
            script_obj = ScheduledScriptInDB(**script)

            # Schedule only if valid schedule_time and script_file_path exist
            if script["script_file_path"] and script["schedule_time"]:
                try:
                    schedule_script(db,script["_id"],script["script_name"],script["script_file_path"], script["schedule_time"])
                    print(f"[INFO] Scheduled script: {script_obj.script_name}")
                except Exception as e:
                    print(f"[ERROR] Failed to schedule script {script_obj.script_name}: {e}")
            else:
                print(f"[WARNING] Script {script_obj.script_name} is missing schedule_time or file path.")
    except Exception as e:
        print(f"[ERROR] Error initializing schedules: {e}")