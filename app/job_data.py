import json
import os


def load_job_count(job_count_file):
    if os.path.exists(job_count_file):
        with open(job_count_file, 'r') as file:
            data = json.load(file)
            return data.get("jobs_accepted", 0)
    else:
        with open(job_count_file, 'w') as file:
            json.dump({"jobs_accepted": 0}, file)
        return 0


def save_job_count(job_count_file, count):
    with open(job_count_file, 'w') as file:
        json.dump({"jobs_accepted": count}, file)
