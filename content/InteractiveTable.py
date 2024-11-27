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


class InteractiveTable:
    """An interactive table for exploring the KUBA dataset.
    """

    def __init__(self) -> None:
        self.data_frame = None

    def add_entry(self,
                  bridge_name: str,
                  year_of_norm: str,
                  year_of_construction: str,
                  human_error_factor: int,  # K1
                  bridge_type: str,
                  statical_determinacy_factor: int,  # K3
                  condition_class: int,
                  age: str,
                  condition_factor: int,  # K4
                  bridge_function: str,
                  span: int,
                  overpass_factor: int,  # K6
                  static_calculation_factor: int,  # K7
                  bridge_type_factor: int,  # K8
                  building_material: str,
                  building_material_factor: int,  # K9
                  robustness_factor: int,  # K11
                  earthquake_zone_name: str,
                  earthquake_zone_factor: int,  # K13
                  maintenance_acceptance_date: str,
                  probability_of_collapse: float,
                  length: int,
                  width: int,
                  replacement_costs: int,
                  victim_costs: int,
                  vehicle_lost_costs: int,
                  downtime_costs: int,
                  damage_costs: int) -> None:
        """Adds an entry to the table.

        Parameters
        ----------
        bridge_name: str
            The descriptive name of the bridge
        year_of_norm: str
            The year of the norm that was applied when the bridge was built
        year_of_construction: str
            The year of construction of the bridge
        human_error_factor: int
            The factor for human errors
        bridge_type: str
            The type of the bridge
        statical_determinacy_factor: int
            The statical determinacy factor of the bridge
        condition_class: int
            The condition class of the bridge
        age: str
            The age of the bridge
        condition_factor: int
            The condition factor of the bridge
        bridge_function : str
            The function of the bridge
        span : int
            The span of the bridge
        overpass_factor: int
            The overpass factor of the bridge
        static_calculation_factor: int
            The static calculation factor of the bridge
        bridge_type_factor: int
            The type factor of the bridge
        building_material : str
            The building material of the bridge
        building_material_factor : int
            The building material factor of the bridge
        robustness_factor : int
            The robustness factor of the bridge
        earthquake_zone_name : str
            The name of the earthquake zone in which the bridge is located
        earthquake_zone_factor : int
            The earthquake zone factor of the bridge
        maintenance_acceptance_date : str
            The date of the latest maintenance acceptance of the bridge
        probability_of_collapse : float
            The probability of collapse of the bridge
        length: int,
            The length of the bridge
        width: int,
            The width of the bridge
        replacement_costs: int
            The costs that will be incurred if the bridge has to be rebuilt
            (construction costs)
        victim_costs: int
            The costs of fatalities and injuries
        vehicle_lost_costs: int
            The loss costs from vehicles etc.
        downtime_costs: int
            The costs from business interruption
        damage_costs: int
            The sum of replacement, victim, vehicle and downtime costs
        """
        new_data_frame = pd.DataFrame({
            _('Name'): [bridge_name],
            _('Year of the norm'): [year_of_norm],
            _('Year of construction'): [year_of_construction],
            _('Human error factor'): [human_error_factor],
            _('Type'): [bridge_type],
            _('Statical determinacy factor'): [
                statical_determinacy_factor],
            _('Condition class'): [condition_class],
            _('Age'): [age],
            _('Condition factor'): [condition_factor],
            _('Function'): [bridge_function],
            _('Span'): [span],
            _('Overpass factor'): [overpass_factor],
            _('Static calculation factor'): [
                static_calculation_factor],
            _('Bridge type factor'): [bridge_type_factor],
            _('Building material'): [building_material],
            _('Building material factor'): [building_material_factor],
            _('Robustness factor'): [robustness_factor],
            _('Earthquake zone'): [earthquake_zone_name],
            _('Earthquake zone factor'): [earthquake_zone_factor],
            _('Last maintenance acceptance date'): [
                maintenance_acceptance_date],
            _('Probability of collapse'): [probability_of_collapse],
            _('Length'): [length],
            _('Width'): [width],
            _('Replacement costs'): [replacement_costs],
            _('Victim costs'): [victim_costs],
            _('Vehicle lost costs'): [vehicle_lost_costs],
            _('Downtime costs'): [downtime_costs],
            _('Damage costs'): [damage_costs]})
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
