import subprocess


def run_job(command: str):
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout
