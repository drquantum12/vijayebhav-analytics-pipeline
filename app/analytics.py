from utils import last_n_days_attempts, get_timestamp_based_metrics
from database import FirestoreDB, mongo_db

student_insights_collection = FirestoreDB("student_metrics_insights")
users = mongo_db["users"]
quiz_submissions_collection = mongo_db["quiz_submissions"]


def save_intellectual_level_metric(id_metric_tuple, N_ANALYTICS_DAYS, N_MOST_ACTIVE_HOURS):
    try:
        for _id, metric in id_metric_tuple:
            try:
                user_metric_mapping = dict()

                # knowledge mastery key
                
                if metric["overall_accuracy"] >= 85 and metric["average_score"] >= 1.5:
                    user_metric_mapping["knowledge_mastery"] = "advanced"
                elif metric["overall_accuracy"] >= 60:
                    user_metric_mapping["knowledge_mastery"] = "intermediate"
                else:
                    user_metric_mapping["knowledge_mastery"] = "beginner"

                # challenge preference key
                
                hard_acc = metric["difficulty_wise_accuracy"].get("hard", 0)
                med_acc = metric["difficulty_wise_accuracy"].get("medium", 0)
                if hard_acc >= 70:
                    user_metric_mapping["challenge_preference"] = "enjoys challenge"
                elif med_acc >= 70:
                    user_metric_mapping["challenge_preference"] = "balanced"
                else:
                    user_metric_mapping["challenge_preference"] = "prefers easy"

                # Learning Engagement

                last_n_days_data = last_n_days_attempts(quiz_submissions_collection, user_id=_id, n_days=N_ANALYTICS_DAYS)

                # example timestamp based metrics : {'subject_wise_scores': {'Science': [1, 0, 2, 1], 'Mathematics': [1]},'day_wise_attempts': [{'date': '2025-07-29', 'attempts': 5}]}

                timestamp_based_metrics = get_timestamp_based_metrics(last_n_days_data, n_most_active_hours=N_MOST_ACTIVE_HOURS)
                total_days = len({d["date"] for d in timestamp_based_metrics["day_wise_attempts"]})
                avg_attempts_per_day = sum(d["attempts"] for d in timestamp_based_metrics["day_wise_attempts"]) / total_days

                if avg_attempts_per_day >= 5:
                    user_metric_mapping["learning_engagement"] = "high"
                elif avg_attempts_per_day >= 2:
                    user_metric_mapping["learning_engagement"] = "moderate"
                else:
                    user_metric_mapping["learning_engagement"] = "low"

                

                # Subject Wise Conceptual Stability : TO DO
                subject_wise_conceptual_stability = {}
                for subject, scores in timestamp_based_metrics["subject_wise_scores"].items():
                    score_values = [s for s in scores if isinstance(s, (int, float))]
                    if len(score_values) >= 2:
                        mean_score = sum(score_values) / len(score_values)
                        variance = sum((s - mean_score) ** 2 for s in score_values) / len(score_values)
                        conceptual_stability = 1 - min(1, variance / 2)  # range 0-1
                        subject_wise_conceptual_stability[subject] = conceptual_stability
                    else:
                        subject_wise_conceptual_stability[subject] = 0.5
                user_metric_mapping["subject_wise_conceptual_stability"] = subject_wise_conceptual_stability
                    
                # Active Hours
                
                # Get top 1–2 most active hours
                user_metric_mapping["n_most_active_hours"] = timestamp_based_metrics["n_most_active_hours"]


                # Subject wise Adaptation Strategy

                adaptation_strategy = {}
                for subject, stability in subject_wise_conceptual_stability.items():
                    if user_metric_mapping["knowledge_mastery"] == "beginner" or stability < 0.5:
                        adaptation_strategy[subject] = "slow-paced with analogies"
                    elif user_metric_mapping["knowledge_mastery"] == "intermediate":
                        adaptation_strategy[subject] = "moderate with examples"
                    else:
                        adaptation_strategy[subject] = "fast-paced and concise"

                student_insights_collection.add_or_update_document(_id, {
                    "knowledge_mastery": user_metric_mapping["knowledge_mastery"],
                    "challenge_preference": user_metric_mapping["challenge_preference"],
                    "conceptual_stability": user_metric_mapping["subject_wise_conceptual_stability"],
                    "learning_engagement": user_metric_mapping["learning_engagement"],
                    "peak_learning_hours": user_metric_mapping["n_most_active_hours"],
                    "adaptation_strategy": adaptation_strategy
                })
            except Exception as e:
                print(f"Error processing user {_id}: {e}")
                continue
    except Exception as e:
        print(f"Error in get_intellectual_level_metric: {e}")
        return None