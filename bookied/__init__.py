from bookied.triggers.create import CreateTrigger
from bookied.triggers.result import ResultTrigger
from bookied.triggers.in_progress import InProgressTrigger
from bookied.triggers.finish import FinishTrigger
from bookied.triggers.cancel import CancelTrigger
from bookied.triggers.dynamic_bmg import DynamicBmgTrigger


INCIDENT_CALLS = [
    "create",
    "in_progress",
    "finish",
    "result",
    "canceled",
    "dynamic_bmgs",
]


TRIGGERS = {
    "create": CreateTrigger,
    "in_progress": InProgressTrigger,
    "finish": FinishTrigger,
    "result": ResultTrigger,
    "canceled": CancelTrigger,
    "dynamic_bmgs": DynamicBmgTrigger
}
