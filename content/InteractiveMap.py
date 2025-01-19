import geopandas as gpd
import gettext
import ipywidgets as widgets
import json
import math
import pandas as pd
from babel.numbers import format_currency
from branca.colormap import linear
from functools import cache
from ipyleaflet import (basemaps, basemap_to_tiles, Choropleth, CircleMarker,
                        Layer, LayerGroup, LayersControl, LegendControl, Map,
                        MarkerCluster, WidgetControl)
from IPython.display import display, HTML
from ProgressBar import ProgressBar


@cache
def cached_gettext(message):
    return gettext.gettext(message)


_ = cached_gettext


class InteractiveMap:
    """An interactive map for exploring the KUBA dataset.
    """

    def __init__(self, progress_bar: ProgressBar,
                 earthquake_zones_choropleth: Choropleth,
                 precipitation_zones_choropleth: Choropleth,
                 marker_key: str,
                 show_headings: bool) -> None:
        """Initialize the InteractiveMap with the known number of steps.

        Parameters
        ----------
        progress_bar : ProgressBar
            The progress bar for showing the progress while loading the map
        earthquake_zones : geopandas.geodataframe.GeoDataFrame
            The earthquake zones
        marker_key: str
            The key that is used for creating the markers
        """

        self.marker_key = marker_key
        self.show_headings = show_headings

        progress_bar.update_progress(description=_('Creating base map'))

        self.markers = []
        self.clustered_markers = None
        self.single_markers = None

        # create a map with two base layers:
        # - OpenStreetMap.Mapnik for vector data
        # - Esri.WorldImagery for satellite images
        world_imagery = basemap_to_tiles(basemaps.Esri.WorldImagery)
        world_imagery.base = True
        mapnik = basemap_to_tiles(basemaps.OpenStreetMap.Mapnik)
        mapnik.base = True
        self.map = Map(
            layers=[world_imagery, mapnik],
            center=(46.988, 8.17),
            scroll_wheel_zoom=True,
            zoom=8)
        self.map.layout.height = '1200px'

        # add choropleths
        self.map.add(earthquake_zones_choropleth)
        self.map.add(precipitation_zones_choropleth)

        # add control to enable or disable the
        # base, earthquake and precipitation layers
        layers_control = LayersControl()
        layers_control.collapsed = False
        self.map.add(layers_control)

        # add legend for earthquake zones
        self.map.add(LegendControl(
            {"Z1a": earthquake_zones_choropleth.colormap(0),
             "Z1b": earthquake_zones_choropleth.colormap(0.25),
             "Z2": earthquake_zones_choropleth.colormap(0.5),
             "Z3a": earthquake_zones_choropleth.colormap(0.75),
             "Z3b": earthquake_zones_choropleth.colormap(1)},
            title=_('Earthquake zones'),
            position="topright"))

        # add toggle button to switch between clustered and single markers
        self.cluster_button = widgets.ToggleButton(
            description=_("Cluster bridges"))
        self.map.add_control(WidgetControl(
            widget=self.cluster_button, position='topleft'))

    @staticmethod
    def create_bridge_popup(
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
            probability_of_collapse: float,
            length: int,
            width: int,
            replacement_costs: int,
            victim_costs: int,
            axis: str,
            aadt: int,
            vehicle_lost_costs: int,
            downtime_costs: int,
            damage_costs: int,
            risk: float) -> HTML:
        """Creates a popup for a bridge marker (an HTML widget)

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
        length: int,
            The length of the bridge
        width: int,
            The width of the bridge
        replacement_costs: int
            The costs that will be incurred if the bridge has to be rebuilt
            (construction costs)
        victim_costs: int
            The costs of fatalities and injuries
        axis: str
            The traffic axis on which the bridge is located
        aadt: int
            The average annual daily traffic
        vehicle_lost_costs: int
            The loss costs from vehicles etc.
        downtime_costs: int
            The costs from business interruption
        damage_costs: int
            The sum of replacement, victim, vehicle and downtime costs
        risk: float
            The risk value of this bridge
            (probability_of_collapse * damage_costs)
        """
        widget = widgets.HTML()

        widget.value = (
            '<b>' + _('Name') + '</b>: ' + bridge_name + '<br><b>' +
            _('Year of the norm') + '</b>: ' + norm_year + '<br><b>' +
            _('Year of construction') + '</b>: ' + year_of_construction +
            '<br><b><i>K<sub>1</sub>: ' + _('Human error factor') + '</b>: ' +
            str(human_error_factor) + '</i><br><b>' + _('Type') + '</b>: ' +
            bridge_type + '<br><b><i>K<sub>3</sub>: ' +
            _('Statical determinacy factor') + '</b>: ' +
            str(statical_determinacy_factor) + '</i><br><b>' + _('Age') +
            '</b>: ' + age + '<br><b><i>P<sub>f</sub>&times;K<sub>4</sub>: ' +
            _('Condition factor') + '</b>: ' + str(condition_factor) +
            '</i><br><b>' + _('Span') + '</b>: ' +
            InteractiveMap.__get_dimension_string(span) + '<br><b>' +
            _('Function')
            + '</b>: ' + bridge_function + '<br><b><i>K<sub>6</sub>: ' +
            _('Overpass factor') + '</b>: ' + str(overpass_factor) +
            '</i><br><b><i>K<sub>7</sub>: ' + _('Static calculation factor') +
            '</b>: ' + str(static_calculation_factor) +
            '</i><br><b><i>K<sub>8</sub>: ' + _('Bridge type factor') +
            '</b>: ' + str(bridge_type_factor) + '</i><br><b>' +
            _('Building material') + '</b>: ' + building_material +
            '<br><b><i>K<sub>9</sub>: ' + _('Building material factor') +
            '</b>: ' + str(material_factor) +
            '</i><br><b><i>K<sub>11</sub>: ' + _('Robustness factor') +
            '</b>: ' + str(robustness_factor) + '</i><br><b>' +
            _('Earthquake zone') + '</b>: ' + earthquake_zone_name +
            '<br><b><i>K<sub>13</sub>: ' + _('Earthquake zone factor') +
            '</b>: ' + str(earthquake_zone_factor) + '</i><br><b>' +
            _('Last maintenance acceptance date') + '</b>: ' +
            maintenance_acceptance_date + '<br><b>' +
            _('Probability of collapse') + '</b>: ' +
            str(probability_of_collapse) + '<br><b>' + _('Length') + '</b>: ' +
            InteractiveMap.__get_dimension_string(length) + '<br><b>' +
            _('Width') +
            '</b>: ' + InteractiveMap.__get_dimension_string(width) +
            '<br><b>' +
            _('Replacement costs') + '</b>: ' +
            format_currency(replacement_costs, 'CHF') + '<br><b>' +
            _('Victim costs') + '</b>: ' +
            format_currency(victim_costs, 'CHF') + '<br><b>' + _('Axis') +
            '</b>: ' + axis + '<br><b>' + _('Average annual daily traffic') +
            '</b>: ' + str(aadt) + '<br><b>' + _('Vehicle lost costs') +
            '</b>: ' + format_currency(vehicle_lost_costs, 'CHF') + '<br><b>' +
            _('Downtime costs') + '</b>: ' +
            format_currency(downtime_costs, 'CHF') + '<br><b>' +
            _('Damage costs') + '</b>: ' +
            format_currency(damage_costs, 'CHF') + '<br><b>' + _('Risk') +
            '</b>: ' + str(risk))

        return widget

    @staticmethod
    def create_support_structure_popup(
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
            probability_of_collapse: float) -> HTML:
        """Creates a popup for a support structure marker (an HTML widget)

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
        widget = widgets.HTML()

        if math.isnan(year_of_construction):
            year_of_construction_string = _('unknown')
        else:
            year_of_construction_string = str(int(year_of_construction))

        if math.isnan(visible_area):
            visible_area_string = _('unknown')
        else:
            visible_area_string = str(visible_area) + ' m²'

        if math.isnan(condition_class):
            condition_class_string = _('unknown')
        else:
            condition_class_string = str(int(condition_class))

        widget.value = (
            '<b>' + _('Name') + '</b>: ' + support_structure_name + '<br><b>' +
            _('Year of construction') + '</b>: ' +
            year_of_construction_string + '<br><b><i>K<sub>1</sub>: ' +
            _('Human error factor') + '</b>: ' + str(human_error_factor) +
            '<br><b>' + _('Condition class') + '</b>: ' +
            condition_class_string + '<br><b>K<sub>4</sub>: ' +
            _('Condition factor') + '</b>: ' + str(condition_factor) +
            '<br><b>' + _('Type factor') + '</b>: ' +
            str(support_structure_type_factor) + '<br><b>' + _('Wall type') +
            '</b>: ' + str(wall_type) + '<br><b>' +
            _('Building material factor') + '</b>: ' + str(material_factor) +
            '<br><b>' + _('Visible area') + '</b>: ' + visible_area_string +
            '<br><b>' + _('Visible area factor') + '</b>: ' +
            str(visible_area_factor) + '<br><b>' + _('Height') + '</b>: ' +
            InteractiveMap.__get_dimension_string(height) + '<br><b>' +
            _('Precipitation zone') + '</b>: ' + str(precipitation_zone) +
            '<br><b>' + _('Precipitation zone factor') + '</b>: ' +
            str(precipitation_zone_factor) + '<br><b>' +
            _('Probability of collapse') + '</b>: ' +
            str(probability_of_collapse))

        return widget

    @staticmethod
    def create_earthquake_zones_choropleth(
            earthquake_zones: gpd.geodataframe.GeoDataFrame) -> Choropleth:
        return Choropleth(
            geo_data=json.loads(earthquake_zones.to_json()),
            choro_data={'0': 0, '1': 1, '2': 2, '3': 3, '4': 4},
            colormap=linear.YlOrRd_04,
            border_color='black',
            style={'fillOpacity': 0.5, 'dashArray': '5, 5'},
            name=_('Earthquake zones'))

    @staticmethod
    def create_precipitation_zones_choropleth(
            precipitation_zones: gpd.geodataframe.GeoDataFrame) -> Choropleth:
        # replace NaN values with '0'
        precipitation_zones.loc[precipitation_zones['DN'].isna(), 'DN'] = 0
        # we have to simplify the geometry, otherwise we get a MemoryError
        precipitation_zones['geometry'] = (
            precipitation_zones['geometry'].simplify(tolerance=0.0001))
        precipitation_geo_data = json.loads(precipitation_zones.to_json())
        # create dictionary of "id":"DN" as choro_data
        precipitation_choro_data = {
            str(feature["id"]): feature["properties"]["DN"] for feature in (
                precipitation_geo_data["features"])}
        return Choropleth(
            geo_data=precipitation_geo_data,
            choro_data=precipitation_choro_data,
            colormap=linear.Spectral_10,
            border_color='black',
            style={'fillOpacity': 0.5, 'dashArray': '5, 5'},
            name=_('Precipitation zones'))

    def add_marker(self,
                   point: gpd.geodataframe.GeoDataFrame,
                   popup: HTML) -> None:
        """Adds a marker to the internal list of markers.

        Parameters
        ----------
        point : gpd.geodataframe.GeoDataFrame
            The point of the marker on the map
        popup: HTML
            The popup to show at the marker
        """

        if not point.is_empty:
            circle_marker = CircleMarker()
            circle_marker.location = [point.xy[1][0], point.xy[0][0]]
            circle_marker.popup = popup
            self.markers.append(circle_marker)

    def add_marker_layer(self, values: pd.DataFrame) -> None:
        """Adds the marker layer to the map.

        Parameters
        ----------
        values : pandas.DataFrame
            The data frame with all the values we evaluated
        """

        max_value = values[self.marker_key].max()

        # values_colormap = linear.YlOrRd_04
        # values_colormap = linear.RdYlGn_10
        values_colormap = linear.Spectral_11
        values_colormap = values_colormap.scale(0, max_value)
        for i in range(0, len(self.markers)):
            value = values[self.marker_key][i]
            value_color = values_colormap(max_value - value)
            marker = self.markers[i]
            marker.value = value
            marker.radius = 5 + round((10 * value) / max_value)
            marker.color = value_color
            marker.fill_color = value_color

        # sort list by value, so that the markers with the highest
        # value are painted at the top
        self.markers.sort(key=lambda marker: marker.value)

        # update layer with clustered markers
        self.__remove_layer(self.clustered_markers)
        self.clustered_markers = MarkerCluster(
            markers=self.markers, name=_("Clustered Bridges"))

        # update layer with single markers
        self.__remove_layer(self.single_markers)
        self.single_markers = LayerGroup(
            layers=self.markers, name=_("Individual Bridges"))
        self.map.add(self.single_markers)

    def display(self):
        if self.show_headings:
            display(HTML("<hr><div style='text-align: center;'><h1>" +
                         _("Interactive maps") + "</h1></div>"))
        display(HTML("<hr><div style='text-align: center;'><h2>" +
                     self.marker_key + "</h2></div>"))
        display(self.map)

    def toggle_marker_layers(self):
        """Switches between the layers with clustered and individual bridges.
        """
        if self.cluster_button.value:
            self.map.remove_layer(self.single_markers)
            self.map.add_layer(self.clustered_markers)
        else:
            self.map.remove_layer(self.clustered_markers)
            self.map.add_layer(self.single_markers)

    def __remove_layer(self, layer: Layer) -> None:
        if ((layer is not None) and (layer in self.map.layers)):
            self.map.remove(layer)

    @staticmethod
    def __get_dimension_string(dimension) -> str:
        if ((dimension is None) or (math.isnan(dimension))):
            return _('unknown')
        else:
            return (str(dimension) + ' m')
