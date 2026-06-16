import time


def intercept_and_suggest_sqli(url, tool, log_callback, suggest_callback):
    """
    Simulate SQLi interception and suggest payloads.
    """
    log_callback(f"Starting interception on {url} using {tool}")
    time.sleep(1)
    log_callback("HTTP 200 OK")
    time.sleep(1)
    log_callback("Detected potential SQL error in response")
    suggest_callback("' OR 1=1--")
    time.sleep(1)
    log_callback("Interception complete.") 