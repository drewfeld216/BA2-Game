metrics = {}

def log_metric(k, v = 1):
    if (k not in metrics.keys()):
        metrics[k] = []
    metrics[k].append(v)

def get_metric(k):
    return metrics[k]