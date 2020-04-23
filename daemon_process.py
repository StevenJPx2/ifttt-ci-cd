import subprocess
import os
import sys
import shlex
import yaml
import daemon


def action():
    cmd = str(input())
    parsed_cmd = shlex.split(cmd)
    subprocess.run(parsed_cmd)
    print("hello")


with daemon.DaemonContext(
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        working_directory=os.getcwd(),
):
    action()
