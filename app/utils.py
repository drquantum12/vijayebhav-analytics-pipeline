from database import FirestoreDB, mongo_db
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo  # Python 3.9+
from typing import List, Dict

student_metrics_collection = FirestoreDB("student_metrics")
student_insights_collection = FirestoreDB("student_metrics_insights")
users = mongo_db["users"]
tz_name = "Asia/Kolkata"  # IST


# get user ids for users who submitted quizzes in last hour
def get_active_users(last_hours: int = 1) -> List[str]:
    one_hour_ago = datetime.now() - timedelta(hours=last_hours)
    active_users = []
    for user in users.find({"last_quiz_submission_time": {"$gte": one_hour_ago}}, {"_id":1}):
        active_users.append(user["_id"])
    return active_users


# fetching student metrics from firestore for active users
def get_student_metrics(user_ids):
    metrics = dict()
    for user_id in user_ids:
        metric = student_metrics_collection.get_document(user_id)
        if metric:
            metrics[user_id] = metric
    return metrics

def last_n_days_attempts(quiz_submissions_collection, user_id: str, n_days: int = 7) -> List[Dict]:
    """
    Returns a list of dicts with timestamp (IST string), subject, and score
    for the last n days, ordered by responded_at (newest first).
    """
    # Build a UTC window for matching
    now_utc = datetime.now(timezone.utc)
    start_utc = now_utc - timedelta(days=n_days)

    pipeline = [
        {
            "$match": {
                "user_id": user_id,
                "responded_at": {"$gte": start_utc}
            }
        },
        {"$sort": {"responded_at": -1}},  # sort before projecting
        {
            "$project": {
                "_id": 0,
                # Format responded_at in IST
                "timestamp": {
                    "$dateToString": {
                        "date": "$responded_at",
                        "format": "%Y-%m-%d %H:%M:%S",
                        "timezone": tz_name
                    }
                },
                "subject": 1,
                "score": 1
            }
        }
    ]

    return list(quiz_submissions_collection.aggregate(pipeline, allowDiskUse=True))

def get_timestamp_based_metrics(last_n_days_data: List[Dict], n_most_active_hours: int) -> Dict:
    """
    Returns a dictionary with subject-wise array of score, an array of day wise attempts and an array of n most active hours.
    subject_wise_scores: {
        "subject1": [score1, score2, ...],
        "subject2": [score1, score2, ...],
    },
    day_wise_attempts: [
        {"date": "YYYY-MM-DD", "attempts": <int>},
        ...
    ],
    n_most_active_hours: [
        {"hour": "HH:MM", "attempts": <int>},
        ...
    ]
    """
    subject_wise_scores = {}
    day_wise_attempts = {}
    hourly_distribution = {}
    for entry in last_n_days_data:
        # Collect scores by subject
        subject = entry["subject"]
        score = entry["score"]
        if subject not in subject_wise_scores:
            subject_wise_scores[subject] = []
        subject_wise_scores[subject].append(score)

        # Collect attempts by date
        date = entry["timestamp"].split(" ")[0]
        if date not in day_wise_attempts:
            day_wise_attempts[date] = 0
        day_wise_attempts[date] += 1

        # Collect attempts by hour
        hour = entry["timestamp"].split(" ")[1].split(":")[0]  # Get hour part
        if hour not in hourly_distribution:
            hourly_distribution[hour] = 0
        hourly_distribution[hour] += 1

    # Get the n most active hours
    n_most_active_hours = sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:n_most_active_hours]
    n_most_active_hours = [{"hour": hour, "attempts": attempts} for hour, attempts in n_most_active_hours]

    # Convert day_wise_attempts to list of dicts
    day_wise_attempts_list = [{"date": date, "attempts": attempts} for date, attempts in day_wise_attempts.items()]

    return {
        "subject_wise_scores": subject_wise_scores,
        "day_wise_attempts": day_wise_attempts_list,
        "n_most_active_hours": n_most_active_hours
    }
