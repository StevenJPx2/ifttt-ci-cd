import subprocess
import yaml
import pyperclip
import pyautogui


def get_actions(file_name):
    'gets actions from yaml file and runs them'
    ifttt_cond = yaml.load(open(file_name, 'r'), yaml.Loader)

    for cmd in ifttt_cond["then"]:
        if isinstance(cmd, dict):
            copy_cmd = cmd.get("copy")
            if copy_cmd is not None:
                pyperclip.copy(copy_cmd)

            temp_cmd = cmd["cmd"]
            if temp_cmd == "<paste>":
                pyautogui.hotkey('command', 'v')
                pyautogui.press('enter')
                continue

            cmd = temp_cmd.replace("<paste>", pyperclip.paste())

        subprocess.run(cmd, shell=True, check=True)


get_actions('cmds.yaml')
