from typing import Callable
from datetime import datetime

try:  # Optional for colored console logs
    from colorama import Fore, Style, just_fix_windows_console  # noqa

    just_fix_windows_console()
    _error_format = (
        f"{Style.BRIGHT + Fore.LIGHTRED_EX}[FAILURE] "
        f"{Style.BRIGHT + Fore.WHITE}{{src}}{Style.RESET_ALL} :: "
        f"{Style.BRIGHT + Fore.LIGHTRED_EX}{{type}}({Style.RESET_ALL}"
        f"{Fore.LIGHTWHITE_EX}{{error}}{Fore.RESET}"
        f"{Style.BRIGHT + Fore.LIGHTRED_EX}){Style.RESET_ALL} "
        f"{Style.DIM + Fore.CYAN}{{time}}{Fore.RESET}{Style.RESET_ALL}"
    )
except ImportError:
    _error_format = "[FAILURE] {src} :: {type}({error}) {time}"


def print_failure(source: str, error: Exception) -> None:
    err_type = type(error).__name__
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(_error_format.format(src=source, type=err_type, error=error, time=time))


# (Protocol) describing a substitute of the default handler
FailureHandler = Callable[[str, Exception], None]
