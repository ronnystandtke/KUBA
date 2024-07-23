import ipywidgets as widgets
from IPython.display import display


class ProgressBar:
    """A progress bar that handles updates and resets.

    Methods
    -------
    update_progress(description=None)
        Updates the ProgressBar with the description of the current step.
    reset(steps=None)
        Resets the ProgressBar with a new known number of steps.
    """

    def __init__(self, steps: int = None) -> None:
        """Initialize the ProgressBar with the known number of steps.

        Parameters
        ----------
        steps : int
            The known number of steps (default is None)
        """

        self.step = 0
        self.int_progress = widgets.IntProgress(
            value=0,
            min=0,
            max=steps,
            description_width=200,
            # bar_style can be 'success', 'info', 'warning', 'danger' or ''
            bar_style='success',
            style={'bar_color': 'green', 'description_width': 'initial'},
            orientation='horizontal',
            layout=widgets.Layout(width='auto')
        )
        display(self.int_progress)

    def update_progress(self,
                        step: int = None,
                        description: str = None) -> None:
        """Updates the ProgressBar with the description of the current step.

        Parameters
        ----------
        step : int
            The the number of the current step, if left empty the step is
            automatically increased (default is None)
        description : str
            The the description of the current step (default is None)
        """

        if step is None:
            value = self.step
        else:
            value = step
            self.step = step
        self.step += 1

        self.int_progress.value = value
        self.int_progress.description = description

    def reset(self, steps: int = None) -> None:
        """Resets the ProgressBar with a new known number of steps.

        Parameters
        ----------
        steps : int
            The new known number of steps (default is None)
        """
        self.step = 0
        self.int_progress.value = 0
        self.int_progress.max = steps
        self.int_progress.description = ''
