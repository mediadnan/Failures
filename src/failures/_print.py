from datetime import datetime
try:
    from colorama import Fore, Style, just_fix_windows_console
except ImportError:
    _template = "[FAILURE] {source} :: {err_type}({error}) {time}"
else:
    just_fix_windows_console()
    _template = (
        f"{Style.BRIGHT + Fore.LIGHTRED_EX}[FAILURE] "
        f"{Style.BRIGHT + Fore.WHITE}{{source}}{Style.RESET_ALL} :: "
        f"{Style.BRIGHT + Fore.LIGHTRED_EX}{{err_type}}({Style.RESET_ALL}"
        f"{Fore.LIGHTWHITE_EX}{{error}}{Fore.RESET}"
        f"{Style.BRIGHT + Fore.LIGHTRED_EX}){Style.RESET_ALL} "
        f"{Style.DIM + Fore.CYAN}{{time}}{Fore.RESET}{Style.RESET_ALL}"
    )


def print_failure(source: str, error: Exception, **_) -> None:
    """Default failure handler the prints the failure details to the standard output"""
    err_type = type(error).__name__
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(_template.format(source=source, err_type=err_type, error=error, time=time))
