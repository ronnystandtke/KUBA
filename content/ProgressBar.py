import string
from inspect import cleandoc
from IPython.display import display, HTML
from random import choices


class ProgressBar:
    """A progress bar that only needs IPython and therefore can be used
    immediately in Jupyter notebooks.

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
        self.steps = steps
        # create random ID so that the progress bar can be used in several tabs
        # at the same time
        self.random_ID = ''.join(choices(
            string.ascii_letters + string.digits, k=64))
        self.progress_bar_template = f"""
            <div style="border: 1px solid #ddd;
                        border-radius: 4px;
                        padding: 3px;
                        width: 100%;
                        margin: 10px 0;">
                <div id="progress-bar_{self.random_ID}"
                     style="background: #4caf50;
                            width: 0%;
                            height: 20px;
                            border-radius: 2px;"></div>
            </div>
            <p id="package-name_{self.random_ID}"
               style="text-align: center; font-weight: bold;"/>
            """
        self.progress_bar_template = cleandoc(self.progress_bar_template)
        display(HTML(self.progress_bar_template))

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
            progress = self.__get_progress(self.step)
        else:
            progress = self.__get_progress(step)
            self.step = step
        js_code = f"""
            <script>
                var bar = document.getElementById(
                    "progress-bar_{self.random_ID}");
                bar.style.width = {progress} + "%";
                var packageName = document.getElementById(
                    "package-name_{self.random_ID}");
                packageName.innerText = "{description}";
            </script>
        """
        display(HTML(js_code))
        self.step += 1

    def reset(self, steps: int = None) -> None:
        """Resets the ProgressBar with a new known number of steps.

        Parameters
        ----------
        steps : int
            The new known number of steps (default is None)
        """
        self.step = 0
        self.steps = steps

    def __get_progress(self, step: int) -> int:
        if (step > self.steps):
            print((f"Warning: only {self.steps} steps defined "
                   f"but already at step {step}."))
            return 100
        else:
            return ((step * 100) / self.steps)
