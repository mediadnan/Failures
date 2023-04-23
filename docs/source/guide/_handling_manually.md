# Controlled failure handling
The previous example we separated the functions ``test`` into three sub-scopes, however if a failure occurs, 
the rest of code will never be reached, but sometimes this default behavior isn't what we always want.

Say that we want to give a variable an alternative value in case of failure, and proceed to the next steps.

In this example, imagine extracting from inconsistent data that doesn't include optional fields

````python
employees = {
    "097953c06ab31524ad80932a": {
      "name": "Greg Arias",
      "email": "gregorious_534@exmaple.com",
      "phone": '1-376-337-7499',
      "team": "DevOps"
    },
    "0fd316358e289b821ab60fe4": {
      "name": "Clementine Hood",
      "email": "Clemiss76@example.com",
      "team": "DevOps"
    },
    "3a95b2aae5e3026259e0b062": {
      "name": "Arian Wayne",
      "phone": 'fake-number',
      "team": "DevOps"
    }
}
````
And we want to convert it to an evenly structured list of data like:
````python
from typing import TypedDict, Optional

class Employee(TypedDict):
    id: str
    name: str
    team: str
    phone: Optional[str]    # str | None (for py >= 3.10)
    email: Optional[str]    # str | None (for py >= 3.10)
````

Our function will be like

````python
import re
from failures import scope, print_failure


def test(data: dict) -> list[Employee]:
    employees = []
    with scope('extract_employees') as sp:
        pass
````
