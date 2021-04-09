import traceback
from typing import Dict

from tc2.stock_analysis.model_output.ModelSteps import ModelSteps


class ModelStep:
    """
    The output of a step taken in generating a model's output, in a format that can be
        serialized and shown on the webpanel.
        e.g. 'Distance from support: 1.6% (should be in [-0.5%, 0.3%])'
    """
    passed: bool
    value: str
    step_id: ModelSteps

    def __init__(self,
                 passed: bool,
                 value: str,
                 step_id: ModelSteps) -> None:
        self.passed = passed
        self.value = value
        self.step_id = step_id

    def to_json(self) -> Dict[str, any]:
        return {'passed': 'PASSED' if self.passed else 'FAILED',
                'value': self.value,
                'label': self.step_id.label,
                'info': self.step_id.info}

    @classmethod
    def from_json(cls, data: Dict[str, any]) -> 'ModelStep':
        try:
            return ModelStep(passed=data['passed'] == 'PASSED',
                             value=data['value'],
                             step_id=ModelSteps(data['label'], data['info']))
        except Exception as e:
            traceback.print_exc()
            return ModelStep(passed=True,
                             value='error',
                             step_id=ModelSteps(data['value'], 'this step produced an error'))
