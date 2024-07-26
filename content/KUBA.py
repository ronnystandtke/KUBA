import geopandas as gpd
import gettext
import json
import Labels
import math
import os.path
import time
import pandas as pd
import ipywidgets as widgets
import traceback
from babel.dates import format_date
from datetime import datetime
from functools import cache
from InteractiveMap import InteractiveMap
from InteractiveTable import InteractiveTable
from IPython.display import display
from itables import show
from json import JSONDecodeError
from Plots import Plots
from ProgressBar import ProgressBar
from Risk import Risk
from shapely.geometry import Point

from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

gettext.bindtextdomain('kuba', 'translations')
gettext.textdomain('kuba')

earthquakeZonesDictFileName = "data/earthquakezones.json"


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
    earthquakeZones = None
    map = None
    markerCluster = None
    markerGroup = None

    def __init__(self, progress_bar: ProgressBar) -> None:
        self.progress_bar = progress_bar

        # read file with data
        self.progress_bar.update_progress(
            description=_('Loading building data'))

        # dfAllBuildings = pd.read_excel(
        #     open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
        #     sheet_name='Alle Bauwerke mit Zusatzinfo')

        dfBridges = pd.read_excel(
            open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
            sheet_name='Alle Brücken mit Zusatzinfos')

        self.dfBuildings = pd.read_excel(
            open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
            sheet_name='Bauwerke mitErdbebenüberprüfung')

        self.dfMaintenance = pd.read_excel(
            open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
            sheet_name='BW letzte Erhaltungsmassnahme')

        # load pre-calculated earthquake zone data
        self.earthquakeZonesDict = {}
        try:
            if os.path.isfile(earthquakeZonesDictFileName):
                with open(earthquakeZonesDictFileName) as file:
                    self.earthquakeZonesDict = json.load(file)
        except JSONDecodeError:
            # This only happens when we empty earthquakezones.json to enforce a
            # recalculation.
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
        # print(self.dfBuildings.columns.values)

        # convert to GeoDataFrame
        self.progress_bar.update_progress(
            description=_('Converting points to GeoDataFrames'))
        points = []
        for i in dfBridges.index:
            x = dfBridges[Labels.X_LABEL][i]
            y = dfBridges[Labels.Y_LABEL][i]
            points.append(Point(x, y))
        self.bridges = gpd.GeoDataFrame(
            dfBridges, geometry=points, crs='EPSG:2056')

        self.progress_bar.update_progress(
            description=_('Loading earthquake zones'))
        self.earthquakeZones = gpd.read_file(
            "zip://data/erdbebenzonen.zip!Erdbebenzonen")

        # Leaflet always works in EPSG:4326
        # therefore we have to convert the CRS here
        self.progress_bar.update_progress(
            description=_('Converting coordinate reference systems'))
        self.bridges.to_crs('EPSG:4326', inplace=True)
        self.earthquakeZones.to_crs(crs="EPSG:4326", inplace=True)

        self.interactive_map = InteractiveMap(
            self.progress_bar, self.earthquakeZones)
        self.interactive_table = InteractiveTable()
        self.plots = Plots()

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

        self.loadBridges()

    def updateReadout(self):
        self.sliderReadout.value = '{} / {}'.format(
            self.bridgesSlider.value, self.bridgesSlider.max)

    def loadBridges(self):

        self.newDict = len(self.earthquakeZonesDict) == 0

        try:
            self.bridgesSlider.disabled = True
            self.bridgesIntText.disabled = True
            self.loadButton.disabled = True

            self.progress_bar.reset(self.bridgesSlider.value)
            self.progressBarValue = 0
            self.bridgesWithoutCoordinates = 0
            self.lastProgressBarUpdate = 0

            for i in range(0, self.bridgesSlider.value):
                self.__load_bridge_details(i)

            # final update of the progress bar
            self.__updateProgressBar()

            # save earthquakeZonesDict if just created
            if self.newDict:
                with open(earthquakeZonesDictFileName, 'w') as file:
                    json.dump(self.earthquakeZonesDict, file, indent=4)

            self.interactive_map.add_marker_layer(
                self.interactive_table.data_frame)

            display(self.output)
            with self.output:
                display(self.interactive_map.map)
                show(self.interactive_table.data_frame,
                     buttons=[
                         "pageLength",
                         {"extend": "csvHtml5", "title": _("Bridges")}],
                     column_filters="footer",
                     layout={"top": "searchBuilder"},
                     maxBytes=0)
                self.plots.showPlots()

            self.bridgesSlider.disabled = False
            self.bridgesIntText.disabled = False
            self.loadButton.disabled = False

        except Exception:
            print(traceback.format_exc())
            with self.output:
                print(traceback.format_exc())

    def __load_bridge_details(self, i):
        point = self.bridges['geometry'][i]

        # there ARE empty coordinates in the table! :-(
        if point.is_empty:
            self.bridgesWithoutCoordinates += 1
            return

        self.progressBarValue += 1

        bridgeName = str(self.bridges['Name'][i])

        # K_1
        normYear = Risk.getNormYear(self.bridges[Labels.NORM_YEAR_LABEL][i])
        yearOfConstruction = self.bridges[Labels.YEAR_OF_CONSTRUCTION_LABEL][i]
        if not math.isnan(yearOfConstruction):
            yearOfConstruction = int(yearOfConstruction)
        humanErrorFactor = Risk.getHumanErrorFactor(
            normYear, yearOfConstruction)

        # K_3
        typeCode = self.bridges[Labels.TYPE_CODE_LABEL][i]
        typeText = self.bridges[Labels.TYPE_TEXT_LABEL][i]
        staticalDeterminacyFactor = (
            Risk.getStaticalDeterminacyFactor(typeCode))

        # P_f * K_4
        conditionClass = self.bridges[Labels.CONDITION_CLASS_LABEL][i]
        age = Risk.getAge(yearOfConstruction)
        conditionFactor = Risk.getConditionFactor(conditionClass, age)

        # K_6
        bridgeNumber = self.bridges[Labels.NUMBER_LABEL][i]
        building = self.dfBuildings[
            (self.dfBuildings[Labels.NUMBER_LABEL] == bridgeNumber) &
            (self.dfBuildings[Labels.FUNCTION_TEXT_LABEL]
             .str.startswith('Überquert'))]
        if building.empty:
            functionText = None
        else:
            functionText = building[Labels.FUNCTION_TEXT_LABEL].iat[0]
        overpassFactor = Risk.getOverpassFactor(functionText)
        if functionText is None:
            functionText = _('unknown')

        # K_7
        # The dataset is is quite chaotic. There are bridges where
        # the span is smaller than the largest span,
        # e.g. N13 154, Averserrhein Brücke.
        # Therefore we use the following fallback strategy:
        # We start with the largest span.
        span = Risk.getSpan(self.bridges[Labels.LARGEST_SPAN_LABEL][i])
        if span is None:
            # If the largest span is unknown, use the span.
            span = Risk.getSpan(self.bridges[Labels.SPAN_LABEL][i])
            if span is None:
                # If the span is unknown, use the length.
                span = Risk.getSpan(self.bridges[Labels.LENGTH_LABEL][i])
                if span is None:
                    # If the length is unknown, assume 25 m.
                    span = 25
        staticCalculationFactor = Risk.getStaticCalculationFactor(span)

        # K_8
        bridgeTypeFactor = Risk.getBridgeTypeFactor(typeCode)

        # K_9
        materialCode = Risk.getMaterialCode(
            self.bridges[Labels.MATERIAL_CODE_LABEL][i])
        materialText = self.bridges[Labels.MATERIAL_TEXT_LABEL][i]
        materialFactor = Risk.getMaterialFactor(materialCode)
        buildingMaterialString = (
            _('unknown') if not isinstance(materialText, str)
            else materialText)

        # K_11
        robustnessFactor = Risk.getRobustnessFactor(yearOfConstruction)

        # K_13
        if self.newDict:
            zone = self.earthquakeZones[
                self.earthquakeZones.contains(point)]['ZONE']
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
                intersections = self.earthquakeZones.intersects(
                    circle.iloc[0, 0])
                zone = self.earthquakeZones[intersections]['ZONE']
            if zone.empty:
                zoneName = _("none")
            else:
                zoneName = zone.iloc[0]
            self.earthquakeZonesDict[
                str(point.x) + ' ' + str(point.y)] = zoneName
        else:
            zoneName = self.earthquakeZonesDict[
                str(point.x) + ' ' + str(point.y)]

        earthQuakeZoneFactor = Risk.getEarthQuakeZoneFactor(
            zoneName, yearOfConstruction, type)

        probabilityOfCollapse = (
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
            (1 if robustnessFactor is None
                else robustnessFactor) *
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
        yearOfConstructionString = (
            _('unknown') if yearOfConstruction is None
            else str(yearOfConstruction))

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

        # add new marker to interactive map
        self.interactive_map.add_marker(
            point, bridgeName, normYearString, yearOfConstructionString,
            humanErrorFactor, typeText, staticalDeterminacyFactor, ageText,
            conditionFactor, span, functionText, overpassFactor,
            staticCalculationFactor, bridgeTypeFactor, buildingMaterialString,
            materialFactor, robustnessFactor, zoneName, earthQuakeZoneFactor,
            maintenanceAcceptanceDateString, probabilityOfCollapse)

        # add dataframe to interactive table
        self.interactive_table.add_entry(
            bridgeName, normYearString, yearOfConstructionString,
            humanErrorFactor, typeText, staticalDeterminacyFactor, ageText,
            conditionFactor, functionText, overpassFactor, span,
            staticCalculationFactor, bridgeTypeFactor, buildingMaterialString,
            materialFactor, robustnessFactor, zoneName, earthQuakeZoneFactor,
            maintenanceAcceptanceDateString, probabilityOfCollapse)

        # add data to plots
        self.plots.fillData(i, conditionClass, probabilityOfCollapse, age,
                            span, buildingMaterialString, yearOfConstruction,
                            maintenanceAcceptanceDate)

        self.__updateProgressBarAfterTimeout()

    def __updateProgressBarAfterTimeout(self):
        # updating the progressbar is a very time consuming operation
        # therefore we only update it after some time elapsed
        # and not at every iteration
        now = time.time()
        elapsedTime = now - self.lastProgressBarUpdate
        if elapsedTime > 1:
            self.__updateProgressBar()
            self.lastProgressBarUpdate = now

    def __updateProgressBar(self):
        description = (
            _('Bridges are being loaded') + ': ' +
            str(self.progressBarValue) + '/' +
            str(self.bridgesSlider.value))
        if self.bridgesWithoutCoordinates > 0:
            description += (' (' + str(self.bridgesWithoutCoordinates) +
                            ' ' + _("without coordinates") + ')')
        self.progress_bar.update_progress(
            step=self.progressBarValue, description=description)
