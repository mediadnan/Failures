import math
import failures


def data_num_inverse_sqrt(data: dict) -> float:
    with failures.scope("number", show_failure):
        with failures.scope("extract"):
            num = data["num"]  # fails if 'num' not in data or data is not a dict (1)
        with failures.scope("convert"):
            num = int(num)  # fails if num is not a digit (2)
        with failures.scope("evaluate"):
            return inverse_sqrt(num)


def inverse_sqrt(num: int) -> float:
    # independent (decoupled) function
    with failures.scope("inverse"):
        num = 1 / num  # fails if num == 0 (3)
    with failures.scope("square_root"):
        return round(math.sqrt(num), 2)  # fails if num < 0 (4)


def show_failure(label: str, error: Exception) -> None:
    # This function will serve as a failure handler
    # and will simply print the source and the error
    print(f"[{label}] {error!r}")
