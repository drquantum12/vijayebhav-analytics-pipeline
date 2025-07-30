from utils import get_active_users, get_student_metrics
from analytics import save_intellectual_level_metric
import os

LAST_ACTIVE_HOURS = int(os.getenv("LAST_ACTIVE_HOURS", 24))  # Default to 24 hours if not set
N_ANALYTICS_DAYS = int(os.getenv("N_ANALYTICS_DAYS", 7))  # Default to 7 days if not set
N_MOST_ACTIVE_HOURS = int(os.getenv("N_MOST_ACTIVE_HOURS", 2))  # Default to 2 hours if not set

if __name__ == "__main__":
    active_users = get_active_users(last_hours=LAST_ACTIVE_HOURS)

    
    if active_users:
        student_metrics = get_student_metrics(active_users)
        id_metric_tuple = list(student_metrics.items())
        
        if id_metric_tuple:
            save_intellectual_level_metric(id_metric_tuple, N_ANALYTICS_DAYS, N_MOST_ACTIVE_HOURS)
        else:
            print("No student metrics found for active users.")