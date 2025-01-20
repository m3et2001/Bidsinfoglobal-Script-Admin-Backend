from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import UploadFile, HTTPException, status

from datetime import datetime
import subprocess
from pymongo import MongoClient
from pymongo.database import Database
from fastapi import HTTPException
from threading import Thread
from .models import ScheduledScriptInDB
from db import get_database


# Mapping to track current schedules
current_schedules = {}
SCRIPTS_SCHEDULE_COLLECTION = "scheduler"
SCRIPTS_COLLECTION="scripts"
_scheduler_instance = None
def get_scheduler():
    """Returns a global instance of the APScheduler."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = BackgroundScheduler()
        _scheduler_instance.start()
    return _scheduler_instance

def run_script(script_path):
    """Run the Python script."""
    print(f"*********************[INFO] Running script: {script_path}")
    
    try:
        database = get_database()
      
        result = database[SCRIPTS_COLLECTION].find_one({"script_file_path":script_path})
        if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found")
        
        if result["status"]:
            subprocess.run(["/usr/bin/python3", script_path], check=True)
            print(f"[INFO] Script {script_path} completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error occurred while running {script_path}: {e}")
        # Handle error: Trigger API call or MongoDB query
        handle_script_error(script_path, str(e))

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
    
        result = database[SCRIPTS_COLLECTION].update_one({"script_file_path":script_path},{"$set": {"status": False}})
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Script with the given name not found."
            )

        collection.insert_one(error_document)
        print("[INFO] Error logged successfully to MongoDB.",script_path,collection)
        print("[INFO] Error logged successfully to MongoDB.")
    except Exception as mongo_exception:
        print(f"[ERROR] Exception occurred while logging to MongoDB: {mongo_exception}")



def schedule_script(db: Database, script_id, script_name, script_path, schedule_time):
    """
    Schedule the script to run at the specified time using APScheduler.
    :param scheduler: The APScheduler instance.
    :param db: The database instance.
    :param script_id: ID of the script.
    :param script_name: Name of the script.
    :param script_path: Path to the Python script.
    :param schedule_time: Time in HH:MM (24-hour format) or seconds interval.
    """
    print(f"[INFO] Scheduling script: {script_path} at {schedule_time}")
    scheduler = get_scheduler()
    print("*************************** *schedule_script *******************************")

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


    hour, minute = map(int, schedule_time_str.split(":"))
    # scheduler.add_job(run_script, CronTrigger(hour=hour, minute=minute), args=[script_path], id=str(script_id))
    scheduler.add_job(run_script, 'interval', seconds=30,args=[script_path],id=script_id)


    # Update the mapping
    current_schedules[script_id] = schedule_time_str
    print(f"[INFO] Successfully scheduled {script_path} at {schedule_time_str}.")


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
    print("[INFO] Initializing schedules from the database...")
    try:
        scripts_cursor = db[SCRIPTS_SCHEDULE_COLLECTION].find()
        scripts = list(scripts_cursor)

        for script in scripts:
            script["_id"] = str(script["_id"])
            script_obj = ScheduledScriptInDB(**script)

            if script["script_file_path"] and script["schedule_time"]:
                try:
                    schedule_script(
                        db,
                        script["script_id"],
                        script["script_name"],
                        script["script_file_path"],
                        script["schedule_time"]
                    )
                    print(f"[INFO] Scheduled script: {script_obj.script_name}")
                except Exception as e:
                    print(f"[ERROR] Failed to schedule script {script_obj.script_name}: {e}")
            else:
                print(f"[WARNING] Script {script_obj.script_name} is missing schedule_time or file path.")
    except Exception as e:
        print(f"[ERROR] Error initializing schedules: {e}")