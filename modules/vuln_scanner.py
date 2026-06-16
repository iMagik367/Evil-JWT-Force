import time


def run_scan(url, options, log_callback, progress_callback=None):
    """
    Simulated vulnerability scan. For each option, logs start and success.
    """
    total = len(options) or 1
    log_callback(f"Starting scan on {url} with options: {', '.join(options)}")
    if progress_callback:
        progress_callback(0)
    for idx, t in enumerate(options):
        log_callback(f"Scanning {t}...")
        time.sleep(1)
        log_callback(f"SUCCESS: {t} check passed.")
        if progress_callback:
            progress = int((idx + 1) / total * 100)
            progress_callback(progress)
    log_callback("Scan complete.")
    if progress_callback:
        progress_callback(100) 