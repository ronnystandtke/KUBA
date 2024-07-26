import gettext
import pandas as pd
from functools import cache


@cache
def cached_gettext(message):
    return gettext.gettext(message)


_ = cached_gettext


class InteractiveTable:
    """An interactive table for exploring the KUBA dataset.

    Methods
    -------
    add_entry(bridge_name, norm_year, year_of_construction,
              human_error_factor, bridge_type, statical_determinacy_factor,
              age, condition_factor, span, bridge_function, overpass_factor,
              static_calculation_factor, bridge_type_factor, building_material,
              material_factor, robustness_factor, earthquake_zone_name,
              earthquake_zone_factor, maintenance_acceptance_date,
              probability_of_collapse)
        Adds an entry to the table.
    """

    def __init__(self) -> None:
        self.data_frame = pd.DataFrame({
            _('Name'): [],
            _('Year of the norm'): [],
            _('Year of construction'): [],
            _('Human error factor'): [],
            _('Type'): [],
            _('Statical determinacy factor'): [],
            _('Age'): [],
            _('Condition factor'): [],
            _('Function'): [],
            _('Overpass factor'): [],
            _('Span'): [],
            _('Static calculation factor'): [],
            _('Bridge type factor'): [],
            _('Building material'): [],
            _('Building material factor'): [],
            _('Robustness factor'): [],
            _('Earthquake zone'): [],
            _('Earthquake zone factor'): [],
            _('Last maintenance acceptance date'): [],
            _('Probability of collapse'): []})

    def add_entry(self,
                  bridge_name: str,
                  norm_year: str,
                  year_of_construction: str,
                  human_error_factor: int,
                  bridge_type: str,
                  statical_determinacy_factor: int,
                  age: str,
                  condition_factor: int,
                  span: int,
                  bridge_function: str,
                  overpass_factor: int,
                  static_calculation_factor: int,
                  bridge_type_factor: int,
                  building_material: str,
                  material_factor: int,
                  robustness_factor: int,
                  earthquake_zone_name: str,
                  earthquake_zone_factor: int,
                  maintenance_acceptance_date: str,
                  probability_of_collapse: float) -> None:
        """Adds an entry to the table.

        Parameters
        ----------
        bridge_name: str
            The descriptive name of the bridge
        norm_year: str
            The year of the norm that was applied when the bridge was built
        year_of_construction: str
            The year of construction of the bridge
        human_error_factor: int
            The factor for human errors
        bridge_type: str
            The type of the bridge
        statical_determinacy_factor: int
            The statical determinacy factor of the bridge
        age: str
            The age of the bridge
        condition_factor: int
            The condition factor of the bridge
        span : int
            The span of the bridge
        bridge_function : str
            The function of the bridge
        overpass_factor: int
            The overpass factor of the bridge
        static_calculation_factor: int
            The static calculation factor of the bridge
        bridge_type_factor: int
            The type factor of the bridge
        building_material : str
            The building material of the bridge
        material_factor : int
            The material factor of the bridge
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
        """
        new_data_frame = pd.DataFrame({
            _('Name'): [bridge_name],
            _('Year of the norm'): [norm_year],
            _('Year of construction'): [year_of_construction],
            _('Human error factor'): [human_error_factor],
            _('Type'): [bridge_type],
            _('Statical determinacy factor'): [
                statical_determinacy_factor],
            _('Age'): [age],
            _('Condition factor'): [condition_factor],
            _('Function'): [bridge_function],
            _('Overpass factor'): [overpass_factor],
            _('Span'): [span],
            _('Static calculation factor'): [
                static_calculation_factor],
            _('Bridge type factor'): [bridge_type_factor],
            _('Building material'): [building_material],
            _('Building material factor'): [material_factor],
            _('Robustness factor'): [robustness_factor],
            _('Earthquake zone'): [earthquake_zone_name],
            _('Earthquake zone factor'): [earthquake_zone_factor],
            _('Last maintenance acceptance date'): [
                maintenance_acceptance_date],
            _('Probability of collapse'): [probability_of_collapse]})
        self.data_frame = pd.concat(
            [self.data_frame, new_data_frame], ignore_index=True)
