from typing import List, Dict, Optional

from tc2.stock_analysis.model_output.ModelStep import ModelStep
from tc2.stock_analysis.model_output.ModelSteps import ModelSteps


class AbstractModelOutput:
    """
    The output of an analysis model, in a format that can be serialized and shown
        on the webpanel.
    """

    steps: List[ModelStep]
    vals: Dict[str, any]

    def __init__(self):
        self.steps = []
        self.vals = {}

    def add_step(self,
                 step: ModelStep = None,
                 passed: bool = None,
                 value: str = None,
                 step_id: ModelSteps = None) -> None:
        """
        Adds a step in the calculation of model output.
        Parameters: either a single ModelStep, or:
            passed: bool,
            value: str,
            step_id: ModelSteps
        """
        if step is not None:
            self.steps.append(step)
        elif passed is not None and value is not None and step_id is not None:
            self.steps.append(ModelStep(passed=passed,
                                        value=value,
                                        step_id=step_id))
        else:
            raise ValueError('Invalid arguments passed to model\'s output.add_step()')

    def set_val(self,
                val_name: str,
                val_value: any) -> None:
        """
        THIS VALUE SHOULD BE DE-SERIALIZABLE BY THE FRONTEND.
        Sets the value of a piece of info used in calculating the model's output.
        """
        self.vals[val_name] = val_value

    def get_val(self,
                val_name: str) -> Optional[any]:
        return self.vals[val_name] if val_name in self.vals else None

    def to_json(self) -> Dict[str, any]:
        """
        Serializes output steps and values into a json mapping that can be used by the frontend.
        """
        json_output = {'steps': [step.to_json() for step in self.steps]}
        for val_name, val_value in self.vals.items():
            json_output[val_name] = val_value
        return json_output
