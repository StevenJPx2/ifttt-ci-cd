import sys
import shlex
import subprocess
from argparse import ArgumentParser

import yaml
import pyperclip
import pyautogui
import pexpect

from loading_spinner import Spinner

AFTER_PROMPT_STYLE = "one_line_no_p"


def paste_action():
    pyautogui.hotkey("command", "v")
    pyautogui.press("enter")


def do_action_spin(action):
    if isinstance(action, str):
        Spinner(
            subprocess.run,
            shlex.split(action),
            check=True,
            after_prompt_style=AFTER_PROMPT_STYLE,
            message=action,
        ).spin()
    elif isinstance(action, dict):
        spinner = None
        kwarg_cond = {
            'copy': action.get("copy"),
            'o': action.get("o"),
            'ssh': action.get('ssh'),
        }
        if kwarg_cond['copy'] is not None:
            Spinner(
                pyperclip.copy,
                kwarg_cond["copy"],
                message=kwarg_cond["copy"],
                after_prompt_style=AFTER_PROMPT_STYLE,
            ).spin()

        if kwarg_cond['o'] is not None:
            action_out = Spinner(
                subprocess.run,
                shlex.split(kwarg_cond["o"]),
                check=True,
                capture_output=True,
                message=kwarg_cond['o'],
                after_prompt_style=AFTER_PROMPT_STYLE,
            ).spin()[1].stdout.decode('utf-8')

        if kwarg_cond['ssh'] is not None:
            spinner = Spinner(
                pexpect.spawn,
                kwarg_cond["ssh"],
                message=kwarg_cond["ssh"],
                after_prompt_style=AFTER_PROMPT_STYLE,
            )
            parent_spinner = spinner
            child = spinner.spin()[1]

        for sub_cmd in action["cmd"]:
            if isinstance(sub_cmd, str):
                if "<o>" in sub_cmd:
                    sub_cmd = sub_cmd.replace("<o>", action_out)
                elif sub_cmd == "<paste>":
                    Spinner(
                        paste_action,
                        message="paste macro",
                        after_prompt_style=AFTER_PROMPT_STYLE,
                        indent=2,
                    ).spin()
                    continue

                Spinner(
                    subprocess.run,
                    shlex.split(sub_cmd),
                    check=True,
                    message=sub_cmd,
                    indent=2,
                    after_prompt_style=AFTER_PROMPT_STYLE,
                ).spin()

            elif isinstance(sub_cmd, dict):
                if sub_cmd.get("interact") is True:
                    child.interact()
                    continue
                if sub_cmd.get("send") is not None:
                    if not isinstance(sub_cmd["send"], list):
                        sub_cmd["send"] = [sub_cmd["send"]]
                    for send in sub_cmd["send"]:
                        spinner = Spinner(
                            child.expect,
                            sub_cmd["expect"],
                            parent_spinner=spinner,
                            message=sub_cmd["expect"],
                            after_prompt_style=AFTER_PROMPT_STYLE,
                            indent=2,
                        )
                        spinner.spin()
                        spinner = Spinner(
                            child.sendline,
                            send,
                            parent_spinner=spinner,
                            message=send,
                            after_prompt_style=AFTER_PROMPT_STYLE,
                            indent=3,
                        )
                        spinner.spin()


def do_actions_no_spin(action):
    if isinstance(action, str):
        subprocess.run(shlex.split(action), check=True)
    elif isinstance(action, dict):
        kwarg_cond = {
            'copy': action.get("copy"),
            'o': action.get("o"),
            'ssh': action.get('ssh'),
        }
        if kwarg_cond['copy'] is not None:
            pyperclip.copy(kwarg_cond["copy"])

        if kwarg_cond['o'] is not None:
            action_out = subprocess.run(
                shlex.split(kwarg_cond["o"]),
                check=True,
                capture_output=True,
            )

        if kwarg_cond['ssh'] is not None:
            child = pexpect.spawn(kwarg_cond["ssh"])

        for sub_cmd in action["cmd"]:
            if isinstance(sub_cmd, str):
                if "<o>" in sub_cmd:
                    sub_cmd = sub_cmd.replace("<o>", action_out)
                elif sub_cmd == "<paste>":
                    paste_action()
                    continue

                subprocess.run(shlex.split(sub_cmd), check=True)

            elif isinstance(sub_cmd, dict):
                if sub_cmd.get("interact") is True:
                    child.interact()
                    continue
                if sub_cmd.get("send") is not None:
                    if not isinstance(sub_cmd["send"], list):
                        sub_cmd["send"] = [sub_cmd["send"]]
                    for send in sub_cmd["send"]:
                        child.expect(sub_cmd["expect"])
                        child.sendline(sub_cmd["send"])


def do_actions(yaml_file, casc_failure, no_spinner):
    actions = yaml.load(open(yaml_file, 'r'), yaml.Loader)["then"]
    for action in actions:
        if no_spinner is False:
            do_action_spin(action)
        else:
            do_action_no_spin(action)


if __name__ == "__main__":
    parser = ArgumentParser(
        "Performs actions in order given in your yaml file.")
    parser.add_argument("-f",
                        "--yaml_file",
                        help="Executes shell scripts in typed order",
                        default="cmds.yaml")
    parser.add_argument(
        "-ns",
        "--no-spinner",
        help="Removes the spinner; useful for key macros. default: false",
        action='store_true')
    parser.add_argument(
        "-cf",
        "--casc-failure",
        help="If one statement fails, everything after it fails",
        action='store_true')

    args = parser.parse_args()

    do_actions(args.yaml_file, args.casc_failure, args.no_spinner)
