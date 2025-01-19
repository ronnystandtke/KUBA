import gettext
import math
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
                  support_structure_name: str,
                  year_of_construction: str,
                  human_error_factor: int,
                  condition_class: int,
                  condition_factor: int,
                  support_structure_type_factor: float,
                  wall_type: str,
                  material_factor: float,
                  visible_area: float,
                  visible_area_factor: float,
                  height: float,
                  height_factor: float,
                  precipitation_zone: int,
                  precipitation_zone_factor: float,
                  probability_of_collapse: float) -> None:
        """Adds an entry to the table.

        Parameters
        ----------
        support_structure_name: str
            The descriptive name of the support structure
        year_of_construction: str
            The year of construction of the support structure
        human_error_factor: int
            The factor for human errors
        condition_class: int
            The condition class of the support structure
        condition_factor: int
            The condition factor of the support structure
        support_structure_type_factor: int
            The type factor of the support structure
        wall_type: str
            The wall type of the support structure
        material_factor : int
            The material factor of the support structure
        visible_area: float
            The visible area of the support structure
        visible_area_factor: float
            The visible area factor of the support structure
        height: float
            The height of the support structure
        height_factor: float
            The height factor of the support structure
        precipitation_zone: int
            The precipitation zone of the support structure
        precipitation_zone_factor: float
            The precipitation zone factor of the support structure
        probability_of_collapse : float
            The probability of collapse of the support structure
        """

        if (precipitation_zone is None) or (math.isnan(precipitation_zone)):
            precipitation_zone_string = _('unknown')
        else:
            precipitation_zone_string = str(precipitation_zone)

        new_data_frame = pd.DataFrame({
            _('Name'): [support_structure_name],
            _('Year of construction'): [year_of_construction],
            _('Human error factor'): [human_error_factor],
            _('Condition class'): [condition_class],
            _('Condition factor'): [condition_factor],
            _('Type factor'): [support_structure_type_factor],
            _('Wall type'): [wall_type],
            _('Building material factor'): [material_factor],
            _('Visible area'): [
                "" if math.isnan(visible_area) else visible_area],
            _('Visible area factor'): [visible_area_factor],
            _('Height'): ["" if math.isnan(height) else height],
            _('Height factor'): [height_factor],
            _('Precipitation zone'): [precipitation_zone_string],
            _('Precipitation zone factor'): [precipitation_zone_factor],
            _('Probability of collapse'): [probability_of_collapse]
            })
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
                 {"extend": "csvHtml5", "title": _("Support structures")}],
             column_filters="footer",
             layout={"top": "searchBuilder"},
             maxBytes=0)
