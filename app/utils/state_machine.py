def update_status(submission,new_status):
    allowed_transitions={
        "IN_QUEUE": {"RUNNING"},
        "RUNNING": {"DONE", "ERROR","IN_QUEUE"},
        "DONE": {"IN_QUEUE"},
        "ERROR": {"IN_QUEUE"}
    }
    current_status=submission.status
    if new_status not in allowed_transitions.get(current_status, set()):
        raise ValueError(f"Invalid status transition from {current_status} to {new_status}")
    
    submission.status=new_status

