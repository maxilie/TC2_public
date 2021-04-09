import math
from typing import Dict, Optional, List

import numpy

from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.stock_analysis.ModelWeightingSystem import ModelWeightingSystem
from tc2.log.LogFeed import LogFeed, LogLevel


def evenly_distribute_weights(pass_fail_models: List[AnalysisModelType],
                              min_model_weights: Dict[AnalysisModelType, float],
                              max_model_weights: Dict[AnalysisModelType, float],
                              logfeed_process: LogFeed) -> ModelWeightingSystem:
    """Returns the scoring system which assigns weights evenly among models, within the allowed mins and maxes."""

    # Ensure min_model_weights has same number of models as max_model_weights
    if len(min_model_weights) != len(max_model_weights):
        logfeed_process.log(LogLevel.ERROR,
                            'Tried to generate a weight combination with mismatched model ranges '
                            '(min and max dicts have different number of models)')
        return ModelWeightingSystem(dict.fromkeys(pass_fail_models, 0), logfeed_process)

    # If the scoring system has no models, leave it blank
    if len(max_model_weights.keys()) == 0:
        return ModelWeightingSystem(dict.fromkeys(pass_fail_models, 0), logfeed_process)

    # Ensure at least one combination of weights sums to 1
    if sum(max_model_weights.values()) < 0.999:
        logfeed_process.log(LogLevel.ERROR,
                            'Tried to generate a weight combination but the weight ranges do not allow for any '
                            'combinations that add up to 1.')
        return ModelWeightingSystem(dict.fromkeys(pass_fail_models, 0), logfeed_process)

    # First, make each model's weight the midpoint between its min and max allowed value
    model_weights = {}
    for model_type, min_weight in min_model_weights.items():
        # Init the weight as the average of its min and max allowed value
        max_weight = max_model_weights[model_type]
        model_weights[model_type] = (min_weight + max_weight) / 2.0

    # Second, raise or lower weights until their sum is 1
    diff = _one_minus(model_weights)
    safety = 0
    while diff != 0 and safety < 999:
        safety += 1
        incr = max(0.001, abs(diff) / len(model_weights.values()))
        for model_type in model_weights:
            # Lower model's weight if weights are too high
            if diff < 0 and model_weights[model_type] - incr >= min_model_weights[model_type]:
                model_weights[model_type] -= incr
            # Raise model's weight if weights are too low
            if diff > 0 and model_weights[model_type] + incr <= max_model_weights[model_type]:
                model_weights[model_type] += incr
        # Calculate new diff
        diff = _one_minus(model_weights)
    if safety >= 999:
        logfeed_process.log(LogLevel.WARNING, 'Initialization of strategy\'s analysis model weights incomplete! '
                                              'Could not find an even combination that sums to one!')

    # Finally, add in pass/fail models
    for model_type in pass_fail_models:
        model_weights[model_type] = 0

    return ModelWeightingSystem(model_weights, logfeed_process)


def get_next_weights(pass_fail_models: List[AnalysisModelType],
                     min_model_weights: Dict[AnalysisModelType, float],
                     max_model_weights: Dict[AnalysisModelType, float],
                     logfeed_process: LogFeed,
                     combination_number: int,
                     resolution: float = 0.025) -> Optional[ModelWeightingSystem]:
    """
    Returns the combination_number-th combination of weights (starting at 1),
     or None if current_weights is the final combination.
    """

    # Init each model weight to its min allowable value
    model_weights = {}
    for model_type, min_weight in min_model_weights.items():
        model_weights[model_type] = min_weight

    # Create a list of model_type's
    models = [model_type for model_type in model_weights.keys()]

    # Iterate combination_number times
    iterations = 0

    # Ensure at least one combination of weights sums to 1
    if sum(max_model_weights.values()) < 1:
        logfeed_process.log(LogLevel.WARNING,
                            'Tried to generate a weight combination but the weight ranges do not allow for any '
                            'combinations that add up to 1.')
        return None

    # Handle edge case of zero non-pass/fail models
    if len(models) == 0:
        logfeed_process.log(LogLevel.WARNING,
                            'Tried to generate a weight combination for a strategy that only uses pass/fail models')
        return None

    # Handle edge case of only one model
    elif len(models) == 1:
        model_weights[models[0]] = 1.0
        iterations += 1

    # Handle edge case of only two models
    elif len(models) == 2:
        # Call first model 'mover_1' and second model 'mover_2'
        mover_1 = models[0]
        mover_2 = models[1]

        # Generate combinations by raising mover_1 while lowering mover_2
        model_weights[mover_1] = min_model_weights[mover_1]
        model_weights[mover_2] = max_model_weights[mover_2]
        while model_weights[mover_2] > min_model_weights[mover_2] + 0.00001 \
                or model_weights[mover_1] < max_model_weights[mover_1] - 0.00001:
            # Stop when combination_number is reached
            if iterations == combination_number:
                break

            moved = False

            # Raise mover_1 if doing so will not raise mover_1 above its max
            if model_weights[mover_1] < max_model_weights[mover_1] - 0.00001:
                model_weights[mover_1] += min(resolution, max_model_weights[mover_1] - model_weights[mover_1])
                moved = True

            # Lower mover_2 if doing so will not lower mover_2 below its min or the sum of weights below 1
            if model_weights[mover_2] > min_model_weights[mover_2] + 0.00001 and \
                    sum(model_weights.values()) >= 1 + resolution:
                model_weights[mover_2] -= min(resolution, model_weights[mover_2] - min_model_weights[mover_2])
                moved = True

            if not moved:
                break

            # Count this combination if the sum of weights is 1
            if abs(sum(model_weights.values()) - 1) < 0.0001:
                iterations += 1

        if iterations < combination_number:
            # Generate combinations by raising mover_2 while lowering mover_1
            model_weights[mover_1] = max_model_weights[mover_1]
            model_weights[mover_2] = min_model_weights[mover_2]
            while model_weights[mover_1] > min_model_weights[mover_1] + 0.00001 \
                    or model_weights[mover_2] < max_model_weights[mover_2] - 0.00001:
                # Stop when combination_number is reached
                if iterations == combination_number:
                    break

                moved = False

                # Raise mover_2 if doing so will not raise mover_2 above its max
                if model_weights[mover_2] < max_model_weights[mover_2] - 0.00001:
                    model_weights[mover_2] += min(resolution, max_model_weights[mover_2] - model_weights[mover_2])
                    moved = True

                # Lower mover_1 if doing so will not lower mover_1 below its min or the sum of weights below 1
                if model_weights[mover_1] > min_model_weights[mover_1] + 0.00001 and \
                        sum(model_weights.values()) >= 1 + resolution:
                    model_weights[mover_1] -= min(resolution, model_weights[mover_1] - min_model_weights[mover_1])
                    moved = True

                if not moved:
                    break

                # Count this combination if the sum of weights is 1
                if abs(sum(model_weights.values()) - 1) < 0.0001:
                    iterations += 1

    # Handle general case of three or more models
    else:
        # Loop A: go thru each pivot
        for pivot_index in range(len(models)):
            # Stop when combination_number is reached
            if iterations == combination_number:
                break

            # Set all weights to their min
            pivot = models[pivot_index]
            set_mins(model_weights, min_model_weights)

            # Loop B: go thru each possible value of the pivot
            pivot_min = model_weights[pivot]
            pivot_max = max_model_weights[pivot]
            for pivot_weight in numpy.linspace(start=pivot_min,
                                               stop=pivot_max,
                                               num=int(math.ceil((pivot_max - pivot_min) / resolution))):
                # Stop when combination_number is reached
                if iterations == combination_number:
                    break

                # Increment pivot weight
                model_weights[pivot] = pivot_weight

                # Init mover_2 as the right-most model that isn't the pivot
                mover_2_index = len(models) - 1 if pivot_index != len(models) - 1 else len(models) - 2

                # Loop C: go thru each possible mover_2
                while mover_2_index > 0:
                    # Stop when combination_number is reached
                    if iterations == combination_number:
                        break

                    # Init mover_1 as the left-most model that isn't the pivot
                    mover_1_index = 0 if pivot_index != 0 else 1

                    # Loop D: go thru each possible mover_1
                    while mover_1_index < mover_2_index:
                        # Stop when combination_number is reached
                        if iterations == combination_number:
                            break

                        # Reset every weight except the pivot to its min
                        for model_type in models:
                            if model_type != pivot:
                                model_weights[model_type] = min_model_weights[model_type]

                        # Set mover_1 weight to its min and mover_2 weight to the max it can be
                        mover_1 = models[mover_1_index]
                        model_weights[mover_1] = min_model_weights[mover_1]
                        mover_2 = models[mover_2_index]
                        set_logical_max(mover_2, model_weights, min_model_weights[mover_2], max_model_weights[mover_2])

                        # Loop E: go thru each possible mover weights combination
                        while model_weights[mover_2] > min_model_weights[mover_2] + 0.00001 \
                                and model_weights[mover_1] < max_model_weights[mover_1] - 0.00001:
                            iterations += 1
                            # Stop when combination_number is reached
                            if iterations == combination_number:
                                break

                            # Increment mover_1 and decrement mover_2
                            model_weights[mover_1] += min(resolution,
                                                          max_model_weights[mover_1] - model_weights[mover_1])
                            model_weights[mover_2] -= min(resolution,
                                                          model_weights[mover_2] - min_model_weights[mover_2])

                        # Move to next mover_1
                        mover_1_index += 1
                        if mover_1_index == pivot_index:
                            mover_1_index += 1

                    # Move to next mover_2
                    mover_2_index -= 1
                    if mover_2_index == pivot_index:
                        mover_2_index -= 1

    # Add in pass/fail models and return the weight combination we just generated
    if iterations == combination_number:
        for model_type in pass_fail_models:
            model_weights[model_type] = 0
        return ModelWeightingSystem(model_weights, logfeed_process)

    # Return None once all combinations have been generated
    return None


def _one_minus(model_weights: Dict[AnalysisModelType, float]) -> float:
    """
    Returns the difference between 1 and the sum weights.
    Returns 0 if the difference is practically 0.
    """
    weights_sum = sum(model_weights.values())
    return 0 if abs(1 - weights_sum) < 0.005 else 1 - weights_sum


def set_mins(model_weights: Dict[AnalysisModelType, float], min_weights: Dict[AnalysisModelType, float]) -> None:
    """Sets each model weight to its min."""
    for model_type in min_weights.keys():
        model_weights[model_type] = min_weights[model_type]


def set_logical_max(model_type: AnalysisModelType, model_weights: Dict[AnalysisModelType, float], min_weight: float,
                    max_weight: float) -> None:
    """Sets weight of model_type to the max it can be without making the sum of weights greater than 1."""
    model_weights[model_type] = min_weight
    weights_sum = sum(model_weights.values())
    if weights_sum < 1:
        model_weights[model_type] += min(1 - weights_sum, max_weight - model_weights[model_type])


def set_logical_min(model_type: AnalysisModelType, model_weights: Dict[AnalysisModelType, float], min_weight: float,
                    max_weight: float) -> None:
    """Sets weight of model_type to the min it can be without making the sum of weights less than 1."""
    model_weights[model_type] = max_weight
    weights_sum = sum(model_weights.values())
    if weights_sum > 1:
        model_weights[model_type] += min(weights_sum - 1, model_weights[model_type] - min_weight)
