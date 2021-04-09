from datetime import date, datetime
from typing import Optional


class VisualsGenerator:
    """
    A manager containing methods that generate graphs, charts, and other visual insights into the program.

    This is located under the webpanel package instead of tc2 because it could potentially access
    tc2 modules and create circular imports.

    All modules under the tc2 package must be imported locally into the generate_visual method!
    """

    @staticmethod
    def generate_visual(program: 'TC2Program',
                        live_env: 'ExecEnv',
                        sim_env: 'ExecEnv',
                        visual_type: 'VisualType',
                        symbol: Optional[str] = None,
                        day_date: Optional[date] = None,
                        paper: bool = False,
                        check_moment: datetime = None) -> 'AbstractVisualizationData':
        """Compiles JSON data used to display a visual on the webpanel, and returns it in a VisualizationData object."""

        # Import tc2 modules locally so they can be reloaded
        from tc2.TC2Program import TC2Program
        from tc2.visualization.VisualType import VisualType

        program: TC2Program = program

        if visual_type is VisualType.PRICE_GRAPH:
            from tc2.visualization.visualization_data.PriceGraphData import PriceGraphData
            return PriceGraphData.generate_data(
                live_env=live_env,
                sim_env=sim_env,
                symbol=symbol
            )
        elif visual_type is VisualType.RUN_HISTORY:
            from tc2.visualization.visualization_data.RunHistoryData import RunHistoryData
            return RunHistoryData.generate_data(
                live_env=live_env,
                sim_env=sim_env,
                paper=paper
            )
        elif visual_type is VisualType.SINGLE_RUN:
            from tc2.visualization.visualization_data.SingleRunData import SingleRunData
            return SingleRunData.generate_data(
                live_env=live_env,
                sim_env=sim_env,
                symbol=symbol
            )
        elif visual_type is VisualType.SWING_SETUP:
            from tc2.visualization.visualization_data.SwingSetupData import SwingSetupData
            return SwingSetupData.generate_data(
                live_env=live_env,
                sim_env=sim_env,
                symbol=symbol
            )
        elif visual_type is VisualType.BREAKOUT1_SETUP:
            from tc2.visualization.visualization_data.Breakout1SetupData import Breakout1SetupData
            return Breakout1SetupData.generate_data(
                live_env=live_env,
                sim_env=sim_env,
                symbol=symbol,
                check_moment=check_moment
            )
        else:
            error_msg = 'VisualsGenerator encountered a VisualType which it doesn\'t know how to handle. ' \
                f'Likely another \'if\' statement is needed for unhandled visual_type: {visual_type.value}'
            program.error_main(error_msg)
            raise ValueError(error_msg)
