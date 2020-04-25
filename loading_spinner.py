import time
import itertools
import concurrent.futures as cf


class Spinner:
    spins = {'default_spin': '|/-\\'}
    after_prompt_styles = [
        'one_line',
        'one_line_no_p',
        'two_lines',
        'two_lines_no_p',
    ]

    def __init__(self,
                 fn,
                 *args,
                 spinner='default_spin',
                 parent_spinner=None,
                 message=None,
                 after_prompt_style='two_lines',
                 indent=1,
                 **kwargs):

        self.spinner = itertools.cycle(self.spins[spinner])
        self.message = message if message is not None else fn.__name__
        self._kill_flag = None
        self._error_log = ""
        self.completed = False
        self.indent = indent
        self.parent_spinner = parent_spinner
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        assert after_prompt_style in self.after_prompt_styles
        self.after_prompt_style = after_prompt_style

    def _fn_wrapper(self):
        try:
            return_code = self.fn(*self.args, **self.kwargs)
            self._kill_flag = True
        except Exception as e:
            self._error_log = e
            self._kill_flag = False

            return

        return return_code

    def generate_message(self):
        clear_line = "\x1b[2K\x1b[G\x1b[F"
        if self.parent_spinner is not None:
            if self.completed is not False:
                return clear_line + self.parent_spinner.generate_message()\
                       + f"\n{' '*self.indent}{self.completed}  {self.message}"
            return clear_line + self.parent_spinner.generate_message() \
                + f"\n{' '*self.indent}{next(self.spinner)}  {self.message}"
        return clear_line + f"{' '*self.indent}{next(self.spinner)}  {self.message}"

    def _spin_fn(self, sleep_time):

        clear_line = "\x1b[2K\x1b[G\x1b[F"
        while True:
            if self._kill_flag is not None:
                if self.after_prompt_style in ['one_line', 'one_line_no_p']:
                    print(clear_line + "\x1b[2K")
                elif self.after_prompt_style in ['two_lines']:
                    print()

                if self._kill_flag is True:
                    prefix = "✔︎"
                    if self.after_prompt_style in ['two_lines', 'one_line']:
                        prompt = 'Success!'
                    if self.after_prompt_style in [
                            'two_lines_no_p', 'one_line_no_p'
                    ]:
                        prompt = self.message
                    self.completed = prefix
                else:
                    prefix = "✘"
                    if self.after_prompt_style in ['two_lines', 'one_line']:
                        prompt = 'Failed.'
                    if self.after_prompt_style in [
                            'two_lines_no_p', 'one_line_no_p'
                    ]:
                        prompt = self.message

                    print(
                        clear_line +
                        f"{'  '*self.indent}{prefix} {prompt} \n{'    '*self.indent}{self._error_log}\n"
                    )
                    self.completed = prefix
                    return False

                print(clear_line + f"{'  '*self.indent}{prefix} {prompt}")
                return True

            print(self.generate_message())
            time.sleep(sleep_time)

    def spin(self, sleep_time=0.1):
        print()
        with cf.ThreadPoolExecutor(max_workers=2) as e:
            return_code = e.submit(self._fn_wrapper)
            future = e.submit(self._spin_fn, sleep_time)

        return future.result(), return_code.result()
