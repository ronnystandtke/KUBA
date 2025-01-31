import geopandas as gpd
import gettext
import ipywidgets as widgets
import json
import math
import os.path
import pandas as pd
import time
import traceback
from babel.dates import format_date
from datetime import datetime
from functools import cache
from IPython.display import display
from json import JSONDecodeError
from shapely.geometry import Point
import Labels
from BridgeDamageParameters import BridgeDamageParameters
from BridgePlots import BridgePlots
from BridgeRisks import BridgeRisks
from InteractiveBridgesTable import InteractiveBridgesTable
from InteractiveMap import InteractiveMap
from InteractiveSupportStructuresTable import InteractiveSupportStructuresTable
from ProgressBar import ProgressBar
from SupportStructureDamageParameters import SupportStructureDamageParameters
from SupportStructurePlots import SupportStructurePlots
from SupportStructureRisks import SupportStructureRisks


from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

gettext.bindtextdomain('kuba', 'translations')
gettext.textdomain('kuba')

earthquake_zones_dict_file_name = "data/earthquakezones.json"
precipitation_zones_dict_file_name = "data/precipitationzones.json"


@cache
def cached_ngettext(singular, plural, n):
    # speeds up calls to gettext by looking up already processed function
    # arguments from a dictionary
    return gettext.ngettext(singular, plural, n)


@cache
def cached_gettext(message):
    # dito
    return gettext.gettext(message)


_ = cached_gettext


class KUBA:

    output = widgets.Output()

    bridges = None
    osmBridges = None
    earthquake_zones = None
    markerCluster = None
    markerGroup = None

    # TODO:
    #   - mapping is not from sheet "Alle Brücken mit Zusatzinfos", there
    #     are mappings not found in document "Bauwerksdaten aus KUBA":
    #           - "N=2 CHS"
    #           - "6 Delémont - Biel -"
    #   - we calculate the mean value over all months by ourselves because
    #     whenever a month is missing there is no yearly average value:
    #       - a month is missing e.g. in "H 17" or "H 18"
    #       - sometimes there is no data at all e.g. "A 1R"
    # TODO: "A 21" is not in the Bulletin database!
    # ATTENTION!
    #   - there are non-breaking spaces in the KUBA database keys
    #   - they might not be visible in your editor but they are important
    traffic_mapping = {
        "N01": "A 1", "N1": "A 1", "N1-": "A 1", "N1+": "A 1",
        "N1=BEW": "A 1",
        "A51": "A 11",
        "N12": "A 12", "N12-": "A 12", "N12+": "A 12",
        "N13": "A 13", "N13-": "A 13", "N13+": "A 13",
        "N13+ und N13-": "A 13", "N13+ e N13-": "A 13",
        "N14": "A 14",
        "N15": "A 15",
        "N16": "A 16",
        "N17": "A 17",
        "N18": "A 18", "N18=": "A 18",
        "N1A": "A 1a", "N01A": "A 1a", "N01a": "A 1a",
        "N1H": "A 1H",
        "N1R": "A 1R",
        "N02": "A 2", "N02 BAL": "A 2", "N=2 CHS": "A 2", "N02 FA": "A 2",
        "N02 LUN": "A 2", "N02 LUS": "A 2", "N02 RI": "A 2", "N02P": "A 2",
        "N20": "A 20",
        "A21": "A 21", "A21 Martigny-Gd St B": "A 21",
        "N22": "A 22",
        "N23": "A 23",
        "N28": "A 28",
        "N03": "A 3",
        "N04": "A 4",
        "N05": "A 5", "N5": "A 5",
        "N06": "A 6", "N06+": "A 6", "N 06": "A 6", "N06.56": "A 6",
        "N6+": "A 6", "N6-": "A 6", "6": "A 6",
        "6 Delémont - Biel -": "A 6",
        "N07": "A 7",
        "N08": "A 8", "N8": "A 8", "N8+": "A 8", "N8-": "A 8",
        "N09": "A 9", "N9": "A 9", "N9/6025 Rue de débo.": "A 9",
        "N9_GDS": "A 9", "N09_GDSB": "A 9", "N9+": "A 9", "N9S": "A 9",
        "N9S=": "A 9",
        "H1": "H 1",
        "H 20+": "H 20",
        "H21": "H 21"
    }

    def __init__(self, progress_bar: ProgressBar) -> None:
        self.progress_bar = progress_bar

        # read file with data
        self.progress_bar.update_progress(
            description=_('Loading building data'))

        # dfAllBuildings = pd.read_excel(
        #     open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
        #     sheet_name='Alle Bauwerke mit Zusatzinfo')

        self.dfBuildings = pd.read_excel(
            open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
            sheet_name='Alle Bauwerke mit Zusatzinfo')

        dfBridges = pd.read_excel(
            open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
            sheet_name='Alle Brücken mit Zusatzinfos')

        self.dfEarthquakeCheck = pd.read_excel(
            open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
            sheet_name='Bauwerke mitErdbebenüberprüfung')

        self.dfMaintenance = pd.read_excel(
            open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
            sheet_name='BW letzte Erhaltungsmassnahme')

        self.df_support_structures = pd.read_excel(
            open('data/Abfrage alle Infrastrukturobj ' +
                 'Zusatzinfos inkl Nutzung.xlsx', 'rb'),
            sheet_name='2024-04-18 aus KUBA+Funktion')

        # load traffic data
        self.progress_bar.update_progress(
            description=_('Loading traffic data'))
        self.df_traffic_data = pd.read_excel(
            open('data/Bulletin_2023_de.xlsx', 'rb'),
            sheet_name='DTV mit Klassen')

        # load pre-calculated earthquake zone data
        self.earthquake_zones_dict = {}
        try:
            if os.path.isfile(earthquake_zones_dict_file_name):
                with open(earthquake_zones_dict_file_name) as file:
                    self.earthquake_zones_dict = json.load(file)
        except JSONDecodeError:
            # This only happens when we empty earthquakezones.json to enforce a
            # recalculation.
            pass

        # load pre-calculated precipitation zone data
        self.precipitation_zones_dict = {}
        try:
            if os.path.isfile(precipitation_zones_dict_file_name):
                with open(precipitation_zones_dict_file_name) as file:
                    self.precipitation_zones_dict = json.load(file)
        except JSONDecodeError:
            # This only happens when we empty precipitationzones.json to
            # enforce a recalculation.
            pass

        # check how many bridges we find in the other sheets
        # bridgeInAllBuildings = 0
        # bridgeNotInAllBuildings = 0
        # bridgeInBuildings = 0
        # bridgeNotInBuildings = 0
        # for bridgeNumber in dfBridges[NUMBER_LABEL]:
        #
        #     allBuildingsNumbers = (
        #         dfAllBuildings[ALL_BUILDINGS_NUMBER_LABEL].values)
        #     if bridgeNumber in allBuildingsNumbers:
        #         bridgeInAllBuildings += 1
        #     else:
        #         bridgeNotInAllBuildings += 1
        #
        #     if bridgeNumber in self.dfBuildings[NUMBER_LABEL].values:
        #         bridgeInBuildings += 1
        #     else:
        #         bridgeNotInBuildings += 1
        #
        # print("number of bridges found in sheet \
        #     'Alle Bauwerke mit Zusatzinfo':", bridgeInAllBuildings)
        # print("number of bridges NOT found in sheet \
        #     'Alle Bauwerke mit Zusatzinfo':", bridgeNotInAllBuildings)
        # print("number of bridges found in sheet \
        #     'Bauwerke mitErdbebenüberprüfung':", bridgeInBuildings)
        # print("number of bridges NOT found in sheet \
        #     'Bauwerke mitErdbebenüberprüfung':", bridgeNotInBuildings)

        # code to get the correct labels
        # print(self.df_support_structures.columns.values)

        # convert to GeoDataFrame
        self.progress_bar.update_progress(
            description=_('Converting points to GeoDataFrames'))
        bridge_points = []
        for i in dfBridges.index:
            x = dfBridges[Labels.X_LABEL][i]
            y = dfBridges[Labels.Y_LABEL][i]
            bridge_points.append(Point(x, y))
        self.bridges = gpd.GeoDataFrame(
            dfBridges, geometry=bridge_points, crs='EPSG:2056')

        support_structure_points = []
        for i in self.df_support_structures.index:
            x = self.df_support_structures[Labels.SUPPORT_X_LABEL][i]
            y = self.df_support_structures[Labels.SUPPORT_Y_LABEL][i]
            support_structure_points.append(Point(x, y))
        self.support_structures = gpd.GeoDataFrame(
            self.df_support_structures, geometry=support_structure_points,
            crs='EPSG:2056')

        self.progress_bar.update_progress(
            description=_('Loading earthquake zones'))
        self.earthquake_zones = gpd.read_file(
            "zip://data/erdbebenzonen.zip!Erdbebenzonen")

        self.progress_bar.update_progress(
            description=_('Loading precipitation zones'))
        self.precipitation_zones = gpd.read_file(
            "zip://data/niederschlag.zip!niederschlag")

        # Leaflet always works in EPSG:4326
        # therefore we have to convert the CRS here
        self.progress_bar.update_progress(
            description=_('Converting coordinate reference systems'))
        self.bridges.to_crs('EPSG:4326', inplace=True)
        self.support_structures.to_crs('EPSG:4326', inplace=True)
        self.earthquake_zones.to_crs(crs="EPSG:4326", inplace=True)
        self.precipitation_zones.to_crs(crs="EPSG:4326", inplace=True)

        earthquake_zones_choropleth = (
            InteractiveMap.create_earthquake_zones_choropleth(
                self.earthquake_zones))
        precipitation_zones_choropleth = (
            InteractiveMap.create_precipitation_zones_choropleth(
                self.precipitation_zones))

        self.bridges_poc_map = InteractiveMap(
            self.progress_bar, earthquake_zones_choropleth,
            precipitation_zones_choropleth, _('Probability of collapse'), True)

        self.bridges_risk_map = InteractiveMap(
            self.progress_bar, earthquake_zones_choropleth,
            precipitation_zones_choropleth, _('Risk'), False)

        self.bridges_table = InteractiveBridgesTable()

        self.bridge_plots = BridgePlots()

        self.support_structures_poc_map = InteractiveMap(
            self.progress_bar, earthquake_zones_choropleth,
            precipitation_zones_choropleth, _('Probability of collapse'),
            False)

        self.support_structures_risk_map = InteractiveMap(
            self.progress_bar, earthquake_zones_choropleth,
            precipitation_zones_choropleth, _('Risk'), False)

        self.support_structures_table = InteractiveSupportStructuresTable()

        self.support_structures_plots = SupportStructurePlots()

        initialWidthStyle = {'description_width': 'initial'}

        self.bridgesIntText = widgets.BoundedIntText(
            description=_('Number of bridges'),
            min=1,
            max=self.bridges.index.stop,
            layout=widgets.Layout(flex='0 0 auto', width='auto'),
            style=initialWidthStyle
        )

        self.bridgesSlider = widgets.IntSlider(
            value=self.bridges.index.stop,
            min=1,
            max=self.bridges.index.stop,
            style=initialWidthStyle,
            layout=widgets.Layout(
                flex='1 1 auto',
                width='auto',
                margin='0px 0px 0px 10px'),
            readout=False  # we add a readout with custom formatting
        )

        self.sliderReadout = widgets.Label()
        self.updateReadout()
        self.sliderHBox = widgets.HBox(
            [self.bridgesIntText, self.bridgesSlider, self.sliderReadout])

        widgets.link(
            (self.bridgesSlider, 'value'), (self.bridgesIntText, 'value'))

        buttonLayout = widgets.Layout(width='auto')
        self.loadButton = widgets.Button(
            description=_('Load selected number of bridges'),
            layout=buttonLayout
        )

        display(self.output)

        # uncomment for test runs with a low number of bridges
        # with self.output:
        #     display(self.sliderHBox)
        #     display(self.loadButton)

        self.loadBridges()
        self.load_support_structures()

        self.progress_bar.reset(1)
        description = (_('Done'))
        self.progress_bar.update_progress(step=1, description=description)

    def updateReadout(self):
        self.sliderReadout.value = '{} / {}'.format(
            self.bridgesSlider.value, self.bridgesSlider.max)

    def loadBridges(self):

        self.new_earthquake_zones_dict = len(self.earthquake_zones_dict) == 0

        try:
            self.bridgesSlider.disabled = True
            self.bridgesIntText.disabled = True
            self.loadButton.disabled = True

            self.progress_bar.reset(self.bridgesSlider.value)
            self.progress_bar_value = 0
            self.bridgesWithoutCoordinates = 0
            self.last_bridges_progress_bar_update = 0

            for i in range(0, self.bridgesSlider.value):
                self.__load_bridge(i)

            # final update of the progress bar
            self.__update_bridges_progress_bar()

            # save earthquake_zones_dict if just created
            if self.new_earthquake_zones_dict:
                with open(earthquake_zones_dict_file_name, 'w') as file:
                    json.dump(self.earthquake_zones_dict, file, indent=4)

            self.progress_bar.reset(3)
            description = (
                _('Loading the map of bridge collapse probabilities'))
            self.progress_bar.update_progress(step=0, description=description)
            self.bridges_poc_map.add_marker_layer(
                self.bridges_table.data_frame)

            description = (_('Loading the map of bridge risks'))
            self.progress_bar.update_progress(step=1, description=description)
            self.bridges_risk_map.add_marker_layer(
                self.bridges_table.data_frame)

            with self.output:
                self.bridges_poc_map.display()
                self.bridges_risk_map.display()
                description = _('Loading the table of bridges')
                self.progress_bar.update_progress(
                    step=2, description=description)
                self.bridges_table.display()
                self.bridge_plots.display(self.progress_bar)

            self.bridgesSlider.disabled = False
            self.bridgesIntText.disabled = False
            self.loadButton.disabled = False

        except Exception:
            print(traceback.format_exc())
            with self.output:
                print(traceback.format_exc())

    def load_support_structures(self):

        self.progress_bar.reset(len(self.support_structures))
        self.progress_bar_value = 0
        self.last_support_structures_progress_bar_update = 0

        self.new_precipitation_zones_dict = (
            len(self.precipitation_zones_dict) == 0)

        try:

            for i in range(0, len(self.support_structures)):
                self.__load_support_structure(i)
                self.progress_bar_value += 1
                self.__update_support_structures_progress_bar_after_timeout()

            # save precipitation_zones_dict if just created
            if self.new_precipitation_zones_dict:
                with open(precipitation_zones_dict_file_name, 'w') as file:
                    json.dump(self.precipitation_zones_dict, file, indent=4)

            self.progress_bar.reset(3)
            description = (
                _('Loading the map of support structure collapse probabilities'))
            self.progress_bar.update_progress(step=0, description=description)
            self.support_structures_poc_map.add_marker_layer(
                self.support_structures_table.data_frame)

            description = (_('Loading the map of support structure risks'))
            self.progress_bar.update_progress(step=1, description=description)
            self.support_structures_risk_map.add_marker_layer(
                self.support_structures_table.data_frame)

            with self.output:
                self.support_structures_poc_map.display()
                self.support_structures_risk_map.display()
                description = _('Loading the table of support structures')
                self.progress_bar.update_progress(
                    step=2, description=description)
                self.support_structures_table.display()
                self.support_structures_plots.display(self.progress_bar)

        except Exception:
            print(traceback.format_exc())
            with self.output:
                print(traceback.format_exc())

    def __load_support_structure(self, i):

        point = self.support_structures['geometry'][i]
        if point.is_empty:
            # we ignore support structures without coordinates
            return

        # skip everything that is not "Stützbauwerk",
        # "Stützkonstruktion", "Stützmauer", "Stützmaueranlage",
        # "Schwergewichtsmauern in Mauerwerk"
        type_text = self.support_structures[Labels.TYPE_TEXT_LABEL][i]
        if (type_text != 'Schwergewichtsmauern in Mauerwerk' and
                type_text != 'Stützbauwerk' and
                type_text != 'Stützkonstruktion' and
                type_text != 'Stützmauer' and
                type_text != 'Stützmaueranlage'):
            return

        support_structure_name = str(
            self.support_structures[Labels.NAME_LABEL][i])

        # K_1
        year_of_construction = self.support_structures[
            Labels.YEAR_OF_CONSTRUCTION_LABEL][i]
        if not math.isnan(year_of_construction):
            year_of_construction = int(year_of_construction)
        human_error_factor = SupportStructureRisks.get_human_error_factor(
            year_of_construction)

        # K_2
        correlation_factor = 1.3

        # K_4
        condition_class = self.support_structures[
            Labels.SUPPORT_CONDITION_LABEL][i]
        condition_class_factor = (
            SupportStructureRisks.get_condition_class_factor(condition_class))

        # K_8
        function_text = self.support_structures[Labels.FUNCTION_TEXT_LABEL][i]
        is_on_slope_side = SupportStructureRisks.is_on_slope_side(
            function_text)
        wall_type = self.support_structures[Labels.SUPPORT_WALL_TYPE_LABEL][i]
        if type(wall_type) is not str:
            wall_type = ""
        type_factor = SupportStructureRisks.get_type_factor(
            is_on_slope_side, wall_type)

        # K_9
        material_factor = SupportStructureRisks.get_material_factor(wall_type)

        # K_14
        length = self.support_structures[Labels.SUPPORT_LENGTH_LABEL][i]
        average_height = self.support_structures[
            Labels.SUPPORT_AVERAGE_HEIGHT_LABEL][i]
        # we handle empty values for length and average_height only later in
        # the risk calculation!
        visible_area = SupportStructureRisks.get_visible_area(
            length, average_height)
        visible_area_factor = (
            SupportStructureRisks.get_visible_area_factor(visible_area))

        # K_15
        max_height = length = self.support_structures[
            Labels.SUPPORT_MAX_HEIGHT_LABEL][i]
        height_factor = SupportStructureRisks.get_height_factor(max_height)

        # K_16
        # we use the default value for "no information"
        grade_factor = 2.0

        # K_17
        precipitation_zone_value = None
        if self.new_precipitation_zones_dict:
            precipitation_zone = self.precipitation_zones[
                self.precipitation_zones.contains(point)]['DN']
            if precipitation_zone.empty:
                # support structures outside of known precipitation_zones
                precipitation_zone_factor = 1.5
            else:
                precipitation_zone_value = int(precipitation_zone.iloc[0])
                self.precipitation_zones_dict[
                    str(point.x) + ' ' + str(point.y)] = (
                        precipitation_zone_value)
        else:
            precipitation_zone_value = self.precipitation_zones_dict[
                str(point.x) + ' ' + str(point.y)]

        if precipitation_zone_value is None:
            # support structures outside of known precipitation_zones
            precipitation_zone_factor = 1.5
        else:
            precipitation_zone_factor = (
                SupportStructureRisks.get_precipitation_zone_factor(
                    precipitation_zone_value))

        probability_of_failure = 10e-6

        probability_of_collapse = (
            probability_of_failure *
            (1 if human_error_factor is None
                else human_error_factor) *
            (1 if correlation_factor is None
                else correlation_factor) *
            (1 if condition_class_factor is None
                else condition_class_factor) *
            (1 if type_factor is None
                else type_factor) *
            (1 if material_factor is None
                else material_factor) *
            (1 if visible_area_factor is None
                else visible_area_factor) *
            (1 if height_factor is None
                else height_factor) *
            (1 if grade_factor is None
                else grade_factor) *
            (1 if precipitation_zone_factor is None
                else precipitation_zone_factor)
            )

        if ((length is None) or (length == 0) or (math.isnan(length))):
            # if the length is unknown, assume 80 m
            length = 80

        if (
                (average_height is None) or
                (average_height == 0) or
                (math.isnan(average_height))):
            # if the average_height is unknown, assume 20 m
            average_height = 20

        width = self.support_structures[Labels.SUPPORT_WIDTH_LABEL][i]

        kuba_axis = self.support_structures[Labels.AXIS_LABEL][i]
        traffic_axis, aadt, percentage_of_cars = (
            self.__get_traffic_data(kuba_axis))

        consequence_of_collapse = self.support_structures[
            Labels.SUPPORT_CONSEQUENCE_OF_COLLAPSE][i]
        dampening_factor = (
            SupportStructureDamageParameters.get_dampening_factor(
                consequence_of_collapse))

        replacement_costs = (
            SupportStructureDamageParameters.get_replacement_costs(
                length, average_height))
        victim_costs = SupportStructureDamageParameters.get_victim_costs(
            length, dampening_factor)
        vehicle_lost_costs = (
            SupportStructureDamageParameters.get_vehicle_loss_costs(
                length, aadt, percentage_of_cars))
        downtime_costs = SupportStructureDamageParameters.get_downtime_costs(
            aadt, percentage_of_cars)
        damage_costs = SupportStructureDamageParameters.get_damage_costs(
            replacement_costs, victim_costs,
            vehicle_lost_costs, downtime_costs)
        risk = probability_of_collapse * damage_costs

        axis_string = str(kuba_axis) + " → " + str(traffic_axis)

        age = SupportStructureRisks.getAge(year_of_construction)

        material_text = self.support_structures[Labels.MATERIAL_TEXT_LABEL][i]
        building_material_string = (
            _('unknown') if not isinstance(material_text, str)
            else material_text)

        try:
            # add marker to interactive map
            popup = InteractiveMap.create_support_structure_popup(
                support_structure_name, year_of_construction,
                human_error_factor, condition_class, condition_class_factor,
                type_factor, wall_type, material_factor, visible_area,
                visible_area_factor, max_height, height_factor,
                precipitation_zone_value, precipitation_zone_factor,
                probability_of_collapse, length, width, replacement_costs,
                victim_costs, axis_string, aadt, vehicle_lost_costs,
                downtime_costs, damage_costs, risk)
            self.support_structures_poc_map.add_marker(point, popup)
            self.support_structures_risk_map.add_marker(point, popup)

            # add dataframe to interactive table
            self.support_structures_table.add_entry(
                support_structure_name, year_of_construction,
                human_error_factor, condition_class, condition_class_factor,
                type_factor, wall_type, material_factor, visible_area,
                visible_area_factor, max_height, height_factor,
                precipitation_zone_value, precipitation_zone_factor,
                probability_of_collapse, length, width, replacement_costs,
                victim_costs, axis_string, aadt, vehicle_lost_costs,
                downtime_costs, damage_costs, risk)

            # add data to plots
            self.support_structures_plots.fillData(
                i, condition_class, probability_of_collapse, age,
                length, max_height, building_material_string, aadt, risk,
                damage_costs, vehicle_lost_costs, replacement_costs,
                downtime_costs, victim_costs)

        except Exception:
            print(traceback.format_exc())
            with self.output:
                print(traceback.format_exc())
                print('support_structure_name:', support_structure_name)
                print('year_of_construction:', year_of_construction)
                print('human_error_factor:', human_error_factor)
                print('condition_class:', condition_class)
                print('condition_class_factor:', condition_class_factor)
                print('type_factor:', type_factor)
                print('wall_type:', wall_type)
                print('material_factor:', material_factor)
                print('visible_area:', visible_area)
                print('visible_area_factor:', visible_area_factor)
                print('max_height:', max_height)
                print('height_factor:', height_factor)
                print('age:', age)
                print('risk:', risk)

    def __load_bridge(self, i):
        point = self.bridges['geometry'][i]

        # there ARE empty coordinates in the table! :-(
        if point.is_empty:
            self.bridgesWithoutCoordinates += 1
            return

        self.progress_bar_value += 1

        bridgeName = str(self.bridges[Labels.NAME_LABEL][i])

        # K_1
        normYear = BridgeRisks.getNormYear(
            self.bridges[Labels.NORM_YEAR_LABEL][i])
        year_of_construction = self.bridges[
            Labels.YEAR_OF_CONSTRUCTION_LABEL][i]
        if not math.isnan(year_of_construction):
            year_of_construction = int(year_of_construction)
        humanErrorFactor = BridgeRisks.getHumanErrorFactor(
            normYear, year_of_construction)

        # K_3
        typeCode = self.bridges[Labels.TYPE_CODE_LABEL][i]
        typeText = self.bridges[Labels.TYPE_TEXT_LABEL][i]
        staticalDeterminacyFactor = (
            BridgeRisks.getStaticalDeterminacyFactor(typeCode))

        # P_f * K_4
        conditionClass = self.bridges[Labels.CONDITION_CLASS_LABEL][i]
        age = BridgeRisks.getAge(year_of_construction)
        conditionFactor = BridgeRisks.getConditionFactor(conditionClass, age)

        # K_6
        bridgeNumber = self.bridges[Labels.NUMBER_LABEL][i]
        building = self.dfBuildings[
            (self.dfBuildings[Labels.ALL_BUILDINGS_NUMBER_LABEL]
             == bridgeNumber) &
            (self.dfBuildings[Labels.FUNCTION_LABEL]
             .str.startswith('Überquert'))]
        if building.empty:
            functionText = None
        else:
            functionText = building[Labels.FUNCTION_LABEL].iat[0]
        overpassFactor = BridgeRisks.getOverpassFactor(functionText)
        if functionText is None:
            functionText = _('unknown')

        # K_7
        # The dataset is is quite chaotic. There are bridges where
        # the span is smaller than the largest span,
        # e.g. N13 154, Averserrhein Brücke.
        # Therefore we use the following fallback strategy:
        # We start with the largest span.
        span = BridgeRisks.getSpan(self.bridges[Labels.LARGEST_SPAN_LABEL][i])
        if span is None:
            # If the largest span is unknown, use the span.
            span = BridgeRisks.getSpan(self.bridges[Labels.SPAN_LABEL][i])
            if span is None:
                # If the span is unknown, use the length.
                span = BridgeRisks.getSpan(
                    self.bridges[Labels.LENGTH_LABEL][i])
                if span is None:
                    # If the length is unknown, assume 25 m.
                    span = 25
        staticCalculationFactor = BridgeRisks.getStaticCalculationFactor(span)

        # K_8
        bridgeTypeFactor = BridgeRisks.getBridgeTypeFactor(typeCode)

        # K_9
        materialCode = BridgeRisks.getMaterialCode(
            self.bridges[Labels.MATERIAL_CODE_LABEL][i])
        material_text = self.bridges[Labels.MATERIAL_TEXT_LABEL][i]
        materialFactor = BridgeRisks.getMaterialFactor(materialCode)
        building_material_string = (
            _('unknown') if not isinstance(material_text, str)
            else material_text)

        # K_11
        robustness_factor = BridgeRisks.getRobustnessFactor(
            year_of_construction)

        # K_13
        if self.new_earthquake_zones_dict:
            zone = self.earthquake_zones[
                self.earthquake_zones.contains(point)]['ZONE']
            if zone.empty:
                # The earthquake zones don't cover bodies of water.
                # Therefore we have some coordinates of bridges
                # outside of any earthquake zone.
                # Our workaround is to create a 1000 m circle
                # around the coordinates of the bridge to find an
                # intersecting earthquake zone (1000m should be
                # large enough to catch all such cases).
                circle = gpd.GeoDataFrame(
                    {'geometry': [point]}, crs='EPSG:4326')
                # map to CRS 'EPSG:3857', so that we can give the
                # parameter to buffer() below in meters
                circle.to_crs('EPSG:3857', inplace=True)
                circle.geometry = circle.buffer(1000)
                # map back to the Leaflet default of EPSG:4326
                circle = circle.to_crs('EPSG:4326')
                intersections = self.earthquake_zones.intersects(
                    circle.iloc[0, 0])
                zone = self.earthquake_zones[intersections]['ZONE']
            if zone.empty:
                zoneName = _("none")
            else:
                zoneName = zone.iloc[0]
            self.earthquake_zones_dict[
                str(point.x) + ' ' + str(point.y)] = zoneName
        else:
            zoneName = self.earthquake_zones_dict[
                str(point.x) + ' ' + str(point.y)]

        earthQuakeCheckEntry = self.dfEarthquakeCheck[
            self.dfEarthquakeCheck[Labels.NUMBER_LABEL] == bridgeNumber]
        if earthQuakeCheckEntry.empty:
            earthQuakeCheckValue = False
        else:
            earthQuakeCheckValue = earthQuakeCheckEntry[
                Labels.EARTHQUAKE_CHECK_LABEL].iloc[0]

        skewEntry = self.dfBuildings[
            self.dfBuildings[Labels.ALL_BUILDINGS_NUMBER_LABEL]
            == bridgeNumber]
        if skewEntry.empty:
            skewValue = None
        else:
            skewValue = skewEntry[Labels.SKEW_LABEL].iloc[0]

        earthQuakeZoneFactor = BridgeRisks.getEarthQuakeZoneFactor(
            earthQuakeCheckValue, typeCode, bridgeName, skewValue,
            zoneName, year_of_construction)

        probability_of_collapse = (
            (1 if humanErrorFactor is None
                else humanErrorFactor) *
            (1 if staticalDeterminacyFactor is None
                else staticalDeterminacyFactor) *
            (1 if conditionFactor is None
                else conditionFactor) *
            (1 if overpassFactor is None
                else overpassFactor) *
            (1 if staticCalculationFactor is None
                else staticCalculationFactor) *
            (1 if bridgeTypeFactor is None
                else bridgeTypeFactor) *
            (1 if materialFactor is None
                else materialFactor) *
            (1 if robustness_factor is None
                else robustness_factor) *
            (1 if earthQuakeZoneFactor is None
                else earthQuakeZoneFactor)
            )

        if age is None:
            ageText = _('unknown')
        else:
            ageText = cached_ngettext('{0} year', '{0} years', age)
            ageText = ageText.format(age)

        normYearString = (
            _('unknown') if normYear is None
            else str(normYear))
        year_of_constructionString = (
            _('unknown') if year_of_construction is None
            else str(year_of_construction))

        # TODO: There are obvious errors like the support wall
        # 52.303.13, SM Oben Nordportal Tunnel Ried FBNO where the
        # maintenance acceptance date is 31.12.3013.
        # How do we deal with these dates?

        # There are bridges where the maintenance acceptance
        # date is 01.01.1900 and the kind of maintenance is
        # "Abbruch", e.g. S5731, BRÜCKE Gabi 4 N9S and
        # S5191, BRÜCKE Eggamatt N9S.
        # We ignore entries with such a silly date.
        silly_date = datetime(1900, 1, 1, 0, 0)

        maintenanceAcceptanceDate = None
        maintenanceAcceptanceDateString = _('unknown')
        maintenance = self.dfMaintenance[
            self.dfMaintenance[Labels.NUMBER_LABEL] == bridgeNumber]
        if not maintenance.empty:
            maintenanceAcceptanceDate = maintenance[
                Labels.MAINTENANCE_ACCEPTANCE_DATE_LABEL].iloc[0]
            if (isinstance(maintenanceAcceptanceDate, datetime) and
                    (maintenanceAcceptanceDate != silly_date)):
                maintenanceAcceptanceDateString = format_date(
                    maintenanceAcceptanceDate)
            else:
                maintenanceAcceptanceDate = None

        # get AADT (average annual daily traffic) and percentages
        kuba_axis = self.bridges[Labels.AXIS_LABEL][i]
        traffic_axis, aadt, percentage_of_cars = (
            self.__get_traffic_data(kuba_axis))

        length = self.bridges[Labels.LENGTH_LABEL][i]
        if ((length is None) or (length == 0) or (math.isnan(length))):
            # if the length is unknown, assume 200 m
            length = 200
        width = self.bridges[Labels.WIDTH_LABEL][i]
        if ((width is None) or (width == 0) or (math.isnan(width))):
            # if the width is unknown, assume 30 m
            width = 30
        replacement_costs = BridgeDamageParameters.get_replacement_costs(
            length, width)
        victim_costs = BridgeDamageParameters.get_victim_costs(
            typeText, functionText)
        vehicle_lost_costs = BridgeDamageParameters.get_vehicle_loss_costs(
            length, aadt, percentage_of_cars)
        downtime_costs = BridgeDamageParameters.get_downtime_costs(
            aadt, percentage_of_cars)
        damage_costs = (replacement_costs + victim_costs +
                        vehicle_lost_costs + downtime_costs)

        risk = probability_of_collapse * damage_costs

        axis_string = str(kuba_axis) + " → " + str(traffic_axis)

        # add new marker to interactive maps
        bridge_popup = InteractiveMap.create_bridge_popup(
            bridgeName, normYearString, year_of_constructionString,
            humanErrorFactor, typeText, staticalDeterminacyFactor, ageText,
            conditionFactor, span, functionText, overpassFactor,
            staticCalculationFactor, bridgeTypeFactor,
            building_material_string, materialFactor, robustness_factor,
            zoneName, earthQuakeZoneFactor, maintenanceAcceptanceDateString,
            probability_of_collapse, length, width, replacement_costs,
            victim_costs, axis_string, aadt, vehicle_lost_costs,
            downtime_costs, damage_costs, risk)
        self.bridges_poc_map.add_marker(point, bridge_popup)
        self.bridges_risk_map.add_marker(point, bridge_popup)

        # add dataframe to interactive table
        self.bridges_table.add_entry(
            bridgeName, normYearString, year_of_constructionString,
            humanErrorFactor, typeText, staticalDeterminacyFactor,
            conditionClass, ageText, conditionFactor, functionText, span,
            overpassFactor, staticCalculationFactor, bridgeTypeFactor,
            building_material_string, materialFactor, robustness_factor,
            zoneName, earthQuakeZoneFactor, maintenanceAcceptanceDateString,
            probability_of_collapse, length, width, replacement_costs,
            victim_costs, axis_string, aadt, vehicle_lost_costs,
            downtime_costs, damage_costs, risk)

        # add data to plots
        self.bridge_plots.fillData(
            i, conditionClass, probability_of_collapse, age, span,
            building_material_string, year_of_construction,
            maintenanceAcceptanceDate, aadt, risk, damage_costs,
            vehicle_lost_costs, replacement_costs, downtime_costs,
            victim_costs)

        self.__update_bridges_progress_bar_after_timeout()

    def __update_bridges_progress_bar_after_timeout(self):
        # updating the progressbar is a very time consuming operation
        # therefore we only update it after some time elapsed
        # and not at every iteration
        now = time.time()
        elapsedTime = now - self.last_bridges_progress_bar_update
        if elapsedTime > 1:
            self.__update_bridges_progress_bar()
            self.last_bridges_progress_bar_update = now

    def __update_bridges_progress_bar(self):
        description = (
            _('Bridges are being loaded') + ': ' +
            str(self.progress_bar_value) + '/' +
            str(self.bridgesSlider.value))
        if self.bridgesWithoutCoordinates > 0:
            description += (' (' + str(self.bridgesWithoutCoordinates) +
                            ' ' + _("without coordinates") + ')')
        self.progress_bar.update_progress(
            step=self.progress_bar_value, description=description)

    def __update_support_structures_progress_bar_after_timeout(self):
        # updating the progressbar is a very time consuming operation
        # therefore we only update it after some time elapsed
        # and not at every iteration
        now = time.time()
        elapsedTime = now - self.last_support_structures_progress_bar_update
        if elapsedTime > 1:
            self.__update_support_structures_progress_bar()
            self.last_support_structures_progress_bar_update = now

    def __update_support_structures_progress_bar(self):
        description = (
            _('Support structures are being loaded') + ': ' +
            str(self.progress_bar_value) + '/' +
            str(len(self.support_structures)))
        self.progress_bar.update_progress(
            step=self.progress_bar_value, description=description)

    def __get_traffic_data(self, kuba_axis: str):
        traffic_axis = self.traffic_mapping.get(kuba_axis, "")

        if traffic_axis:
            # We have two options to caclulate the mean value:
            #   - .mean().mean(): the mean value of mean values
            #   - .stack().mean(): the mean value of all values
            #   What is the "better" variant?
            dtv_lines = self.df_traffic_data[(self.df_traffic_data[
                Labels.TRAFFIC_AXIS_LABEL] == traffic_axis)]
            start_label = Labels.TRAFFIC_January_LABEL
            stop_label = Labels.TRAFFIC_December_LABEL
            # we use "axis=1" to first calculate the mean value of a certain
            # measuring point
            aadt = dtv_lines.loc[:, start_label:stop_label].mean(axis=1).mean()

            if math.isnan(aadt):
                # no useful data found in Bulletin
                aadt = 5000
                percentage_of_cars = 0.95

            else:
                # get average number of heavy duty vehicles
                # "DTV" = "Durchschnittlicher Tagesverkehr"
                # "DWV SV" =
                #       "Durchschnittlicher Werktagesverkehr"
                #       "Schwerverkehr (Klassen 1, 8, 9, 10)"
                #  is 4 lines below the line with the "DVT" value
                heavy_duty_offset = 4
                aadt_indices = self.df_traffic_data[(self.df_traffic_data[
                    Labels.TRAFFIC_AXIS_LABEL] == traffic_axis)].index
                heavy_duty_indices = aadt_indices + heavy_duty_offset
                heavy_duty_lines = self.df_traffic_data.iloc[
                    heavy_duty_indices]
                # here we use .mean().mean() again
                heavy_duty_mean = heavy_duty_lines.loc[
                    :, start_label:stop_label].mean(axis=1).mean()

                # The average values are very wide spread!
                # e.g. for "A 1", the minimum is 20'481, the maximum is 145'759
                # Decision: we accept this like it is.
                percentage_of_trucks = (heavy_duty_mean * 100) / aadt
                percentage_of_cars = 1 - percentage_of_trucks

                # convert aadt from float to the next rounded int
                # (the values are large enough)
                aadt = round(aadt)

        else:
            aadt = 5000
            percentage_of_cars = 0.95

        return traffic_axis, aadt, percentage_of_cars
