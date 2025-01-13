import gettext
import warnings
import pandas as pd
from functools import cache
from IPython.display import display, HTML
from itables import show


@cache
def cached_gettext(message):
    return gettext.gettext(message)


_ = cached_gettext


class InteractiveSupportStructuresTable:
    """An interactive table for exploring support structures of the KUBA
       dataset.
    """

    def __init__(self) -> None:
        self.data_frame = None

    def add_entry(self,
                  support_structure_name: str) -> None:
        """Adds an entry to the table.

        Parameters
        ----------
        support_structure_name: str
            The descriptive name of the support_structure_name
        """
        new_data_frame = pd.DataFrame({
            _('Name'): [support_structure_name]})
        if self.data_frame is None:
            self.data_frame = new_data_frame
        else:
            with warnings.catch_warnings():
                # TODO: pandas 2.1.0 has a FutureWarning for concatenating
                # DataFrames with Null entries
                warnings.filterwarnings("ignore", category=FutureWarning)
                self.data_frame = pd.concat(
                    [self.data_frame, new_data_frame], ignore_index=True)

    def display(self):
        display(HTML("<hr><div style='text-align: center;'><h1>" +
                     _("Interactive table") + "</h1></div>"))
        show(self.data_frame,
             buttons=[
                 "pageLength",
                 {"extend": "csvHtml5", "title": _("Bridges")}],
             column_filters="footer",
             layout={"top": "searchBuilder"},
             maxBytes=0)
