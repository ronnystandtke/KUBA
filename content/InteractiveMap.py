import geopandas as gpd
import gettext
import ipywidgets as widgets
import json
import pandas as pd
from branca.colormap import linear
from functools import cache
from ipyleaflet import (basemaps, basemap_to_tiles, Choropleth, CircleMarker,
                        Layer, LayerGroup, LayersControl, LegendControl, Map,
                        MarkerCluster, WidgetControl)
from ProgressBar import ProgressBar


@cache
def cached_gettext(message):
    return gettext.gettext(message)


_ = cached_gettext


class InteractiveMap:
    """An interactive map for exploring the KUBA dataset.
    """

    def __init__(self, progress_bar: ProgressBar,
                 earthquake_zones: gpd.geodataframe.GeoDataFrame) -> None:
        """Initialize the InteractiveMap with the known number of steps.

        Parameters
        ----------
        progress_bar : ProgressBar
            The progress bar for showing the progress while loading the map
        earthquake_zones : geopandas.geodataframe.GeoDataFrame
            The earthquake zones
        """

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
        self.map.layout.height = '800px'

        # add layer for earthquake zones (as a choropleth)
        earthquake_zones_choropleth = Choropleth(
            geo_data=json.loads(earthquake_zones.to_json()),
            choro_data={'0': 0, '1': 1, '2': 2, '3': 3, '4': 4},
            colormap=linear.YlOrRd_04,
            border_color='black',
            style={'fillOpacity': 0.5, 'dashArray': '5, 5'},
            name=_('Erdbebenzonen'))
        self.map.add(earthquake_zones_choropleth)

        # add control to enable or disable the base and earthquake layers
        self.map.add(LayersControl())

        # add legend for earthquake zones
        self.map.add(LegendControl(
            {"Z1a": earthquake_zones_choropleth.colormap(0),
             "Z1b": earthquake_zones_choropleth.colormap(0.25),
             "Z2": earthquake_zones_choropleth.colormap(0.5),
             "Z3a": earthquake_zones_choropleth.colormap(0.75),
             "Z3b": earthquake_zones_choropleth.colormap(1)},
            title=_('Erdbebenzonen'),
            position="topright"))

        # add toggle button to switch between clustered and single markers
        self.cluster_button = widgets.ToggleButton(
            description=_("Cluster bridges"))
        self.map.add_control(WidgetControl(
            widget=self.cluster_button, position='topleft'))

    def add_marker(self,
                   point: gpd.geodataframe.GeoDataFrame,
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
        """Adds a marker to the internal list of markers.

        Parameters
        ----------
        point : gpd.geodataframe.GeoDataFrame
            The point of the marker on the map
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

        message = widgets.HTML()

        message.value = (
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
            (_('unknown') if span is None else (str(span) + ' m')) +
            '<br><b>' + _('Function') + '</b>: ' + bridge_function +
            '<br><b><i>K<sub>6</sub>: ' + _('Overpass factor') + '</b>: ' +
            str(overpass_factor) + '</i><br><b><i>K<sub>7</sub>: ' +
            _('Static calculation factor') + '</b>: ' +
            str(static_calculation_factor) + '</i><br><b><i>K<sub>8</sub>: ' +
            _('Bridge type factor') + '</b>: ' + str(bridge_type_factor) +
            '</i><br><b>' + _('Building material') + '</b>: ' +
            building_material + '<br><b><i>K<sub>9</sub>: ' +
            _('Building material factor') + '</b>: ' + str(material_factor) +
            '</i><br><b><i>K<sub>11</sub>: ' + _('Robustness factor') +
            '</b>: ' + str(robustness_factor) + '</i><br><b>' +
            _('Earthquake zone') + '</b>: ' + earthquake_zone_name +
            '<br><b><i>K<sub>13</sub>: ' + _('Earthquake zone factor') +
            '</b>: ' + str(earthquake_zone_factor) + '</i><br><b>' +
            _('Last maintenance acceptance date') + '</b>: ' +
            maintenance_acceptance_date + '<br><b>' +
            _('Probability of collapse') + '</b>: ' +
            str(probability_of_collapse))

        circle_marker = CircleMarker()
        circle_marker.location = [point.xy[1][0], point.xy[0][0]]
        circle_marker.popup = message

        self.markers.append(circle_marker)

    def add_marker_layer(self, bridges: pd.DataFrame) -> None:
        """Adds the marker layer to the map.

        Parameters
        ----------
        bridges : pandas.DataFrame
            The data frame with all the bridges we evaluated
        """

        max_probability_of_collapse = (
            bridges[_('Probability of collapse')].max())

        # probability_colormap = linear.YlOrRd_04
        # probability_colormap = linear.RdYlGn_10
        probability_colormap = linear.Spectral_11
        probability_colormap = probability_colormap.scale(
            0, max_probability_of_collapse)
        for i in range(0, len(self.markers)):
            probability = bridges[_('Probability of collapse')][i]
            probabilityColor = probability_colormap(
                max_probability_of_collapse - probability)
            marker = self.markers[i]
            marker.probability = probability
            marker.radius = 5 + round(
                (10 * probability) / max_probability_of_collapse)
            marker.color = probabilityColor
            marker.fill_color = probabilityColor

        # sort list by probability, so that the bridges with the highest
        # probability of collapse are painted at the top
        self.markers.sort(key=lambda marker: marker.probability)

        # update layer with clustered markers
        self.__remove_layer(self.clustered_markers)
        self.clustered_markers = MarkerCluster(
            markers=self.markers, name=_("Clustered Bridges"))

        # update layer with single markers
        self.__remove_layer(self.single_markers)
        self.single_markers = LayerGroup(
            layers=self.markers, name=_("Individual Bridges"))
        self.map.add(self.single_markers)

    def toggle_marker_layers(self):
        """Switches between the layers with clustered and Individual bridges.
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
