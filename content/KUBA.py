import geopandas as gpd
import gettext
import json
import math
import matplotlib.pyplot as plt
import os.path
import time
import pandas as pd
import ipywidgets as widgets
import traceback
from babel.dates import format_date
from branca.colormap import linear
from datetime import datetime
from functools import cache
from ipyleaflet import (basemaps, basemap_to_tiles, Choropleth, CircleMarker,
                        LayerGroup, LayersControl, LegendControl, Map,
                        MarkerCluster, WidgetControl)
from IPython.display import clear_output
from IPython.display import display
from itables import init_notebook_mode, show
from json import JSONDecodeError
from Risk import Risk
from shapely.geometry import Point

from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

init_notebook_mode(all_interactive=True)

gettext.bindtextdomain('kuba', 'translations')
gettext.textdomain('kuba')

# our constants
ALL_BUILDINGS_NUMBER_LABEL = 'Nummer'
NUMBER_LABEL = '\xa0Nummer'
X_LABEL = 'Landeskoordinaten\xa0E\xa0[m]'
Y_LABEL = 'Landeskoordinaten\xa0N\xa0[m]'
NORM_YEAR_LABEL = 'Belastungsnorm\xa0Text'
YEAR_OF_CONSTRUCTION_LABEL = 'Baujahr'
LARGEST_SPAN_LABEL = 'Grösste Spannweite \xa0[m]\xa0)'
SPAN_LABEL = 'Spannweite [m]'
TYPE_CODE_LABEL = 'Typ\xa0Hierarchie-Code'
TYPE_TEXT_LABEL = 'Typ\xa0Text'
MATERIAL_CODE_LABEL = 'Bauart\xa0Code'
MATERIAL_TEXT_LABEL = 'Bauart\xa0Text'
CONDITION_CLASS_LABEL = 'Zustands- Klasse'
FUNCTION_TEXT_LABEL = 'Funktion\xa0Text'
MAINTENANCE_ACCEPTANCE_DATE_LABEL = (
    'Erhaltungsmassnahme\xa0Datum\xa0der\xa0Abnahme')

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

    def __init__(self):
        statusText = widgets.Text(
            value='', layout=widgets.Layout(width='95%'), disabled=True)
        display(statusText)

        # read file with data
        statusText.value = _('Loading building data, please wait...')

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
        statusText.value = _(
            'Converting points to GeoDataFrames, please wait...')
        points = []
        for i in dfBridges.index:
            x = dfBridges[X_LABEL][i]
            y = dfBridges[Y_LABEL][i]
            points.append(Point(x, y))
        self.bridges = gpd.GeoDataFrame(
            dfBridges, geometry=points, crs='EPSG:2056')

        statusText.value = _('Loading earthquake zones, please wait...')
        self.earthquakeZones = gpd.read_file(
            "zip://data/erdbebenzonen.zip!Erdbebenzonen")

        # Leaflet always works in EPSG:4326
        # therefore we have to convert the CRS here
        statusText.value = _('Converting CRS, please wait...')
        self.bridges.to_crs('EPSG:4326', inplace=True)
        self.earthquakeZones.to_crs(crs="EPSG:4326", inplace=True)

        statusText.value = _('Creating base map, please wait...')
        worldImagery = basemap_to_tiles(basemaps.Esri.WorldImagery)
        worldImagery.base = True
        mapnik = basemap_to_tiles(basemaps.OpenStreetMap.Mapnik)
        mapnik.base = True
        self.map = Map(
            layers=[worldImagery, mapnik],
            center=(46.988, 8.17),
            scroll_wheel_zoom=True,
            zoom=8)
        self.map.layout.height = '800px'

        choro_data = {
            '0': 0,
            '1': 1,
            '2': 2,
            '3': 3,
            '4': 4
        }

        choropleth = Choropleth(
            geo_data=json.loads(self.earthquakeZones.to_json()),
            choro_data=choro_data,
            colormap=linear.YlOrRd_04,
            border_color='black',
            style={'fillOpacity': 0.5, 'dashArray': '5, 5'},
            name='Erdbebenzonen')
        self.map.add(choropleth)

        legend = LegendControl(
            {"Z1a": choropleth.colormap(0),
             "Z1b": choropleth.colormap(0.25),
             "Z2": choropleth.colormap(0.5),
             "Z3a": choropleth.colormap(0.75),
             "Z3b": choropleth.colormap(1)},
            title="Erdbebenzonen",
            position="topright")
        self.map.add(legend)

        self.clusterButton = widgets.ToggleButton(
            description=_("Cluster bridges"))
        widgetControl = WidgetControl(
            widget=self.clusterButton, position='topleft')
        self.map.add_control(widgetControl)

        self.map.add(LayersControl())

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

        # create a progress bar
        self.progressBar = widgets.IntProgress(
            value=0,
            min=0,
            max=self.bridges.index.stop,
            description=(
                _('Bridges are being loaded') +
                ': ' + str(0) + '/' + str(self.bridges.index.stop)),
            description_width=200,
            # bar_style can be 'success', 'info', 'warning', 'danger' or ''
            bar_style='success',
            style={'bar_color': 'green', 'description_width': 'initial'},
            orientation='horizontal',
            layout=widgets.Layout(width='auto')
        )

        clear_output()
        # display(self.sliderHBox)
        # display(self.loadButton)
        display(self.output)
        self.loadBridges()

    def updateReadout(self):
        self.sliderReadout.value = '{} / {}'.format(
            self.bridgesSlider.value, self.bridgesSlider.max)

    def toggleMarkerLayers(self):
        if self.clusterButton.value:
            self.map.remove_layer(self.markerGroup)
            self.map.add_layer(self.markerCluster)
        else:
            self.map.remove_layer(self.markerCluster)
            self.map.add_layer(self.markerGroup)

    @output.capture()
    def loadBridges(self):

        newDict = len(self.earthquakeZonesDict) == 0

        try:
            self.bridgesSlider.disabled = True
            self.bridgesIntText.disabled = True
            self.loadButton.disabled = True

            self.progressBar.value = 0
            self.progressBar.max = self.bridgesSlider.value
            self.progressBar.description = (
                _('Bridges are being loaded') + ': ' +
                str(self.progressBar.value) + '/' + str(self.progressBar.max))

            self.output.clear_output(wait=True)
            with self.output:
                display(self.progressBar)

            markers = []
            self.dataFrame = pd.DataFrame({
                _('Name'): [],
                _('Year of the norm'): [],
                _('Year of construction'): [],
                _('Human error factor'): [],
                _('Type'): [],
                _('Statical determinacy factor'): [],
                _('Age'): [],
                _('Condition factor'): [],
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

            self.bridgesWithoutCoordinates = 0
            self.lastProgressBarUpdate = 0
            self.progressBarValue = 0

            # add new DataFrames to simplify the scatter plots
            self.acpScatterColumns = [
                _('Age'), _('Condition class'), _('Probability of collapse')]
            self.ageConditionPocScatter = pd.DataFrame(
                columns=self.acpScatterColumns)
            self.cpScatterColumns = [
                _('Condition class'), _('Probability of collapse')]
            self.conditionPocScatter = pd.DataFrame(
                columns=self.cpScatterColumns)
            self.spScatterColumns = [
                _('Span'), _('Probability of collapse')]
            self.spanPocScatter = pd.DataFrame(
                columns=self.spScatterColumns)
            self.mpScatterColums = [
                _('Last maintenance acceptance date'),
                _('Probability of collapse')]
            self.maintenancePocScatter = pd.DataFrame(
                columns=self.mpScatterColums)

            for i in range(0, self.bridgesSlider.value):
                point = self.bridges['geometry'][i]

                # there ARE empty coordinates in the table! :-(
                if point.is_empty:
                    self.bridgesWithoutCoordinates += 1

                else:
                    self.progressBarValue += 1

                    bridgeName = str(self.bridges['Name'][i])

                    # K_1
                    normYear = Risk.getNormYear(
                        self.bridges[NORM_YEAR_LABEL][i])
                    yearOfConstruction = (
                        self.bridges[YEAR_OF_CONSTRUCTION_LABEL][i])
                    if not math.isnan(yearOfConstruction):
                        yearOfConstruction = int(yearOfConstruction)
                    humanErrorFactor = Risk.getHumanErrorFactor(
                        normYear, yearOfConstruction)

                    # K_3
                    typeCode = self.bridges[TYPE_CODE_LABEL][i]
                    typeText = self.bridges[TYPE_TEXT_LABEL][i]
                    staticalDeterminacyFactor = (
                        Risk.getStaticalDeterminacyFactor(typeCode))

                    # P_f * K_4
                    conditionClass = self.bridges[CONDITION_CLASS_LABEL][i]
                    age = Risk.getAge(yearOfConstruction)
                    conditionFactor = Risk.getConditionFactor(
                        conditionClass, age)

                    # K_6
                    # bridgeNumber = self.bridges[NUMBER_LABEL][i]
                    # building = self.dfBuildings[
                    #    self.dfBuildings[NUMBER_LABEL] == bridgeNumber]
                    # TODO:
                    # - many bridges are NOT in the buildings table
                    # - some bridges (e.g. N5/3BS30N) are there multiple times
                    # functionText = building[FUNCTION_TEXT_LABEL].iat[0]

                    # K_7
                    # TODO: There are bridges where the span is smaller than
                    # the largest span, e.g. N13 154, Averserrhein Brücke.
                    # What does this actually mean, physically?
                    span = Risk.getSpan(self.bridges[SPAN_LABEL][i])
                    if span is None:
                        span = Risk.getSpan(
                            self.bridges[LARGEST_SPAN_LABEL][i])
                    Risk.getSpan(self.bridges[SPAN_LABEL][i])
                    staticCalculationFactor = Risk.getStaticCalculationFactor(
                        span)

                    # K_8
                    bridgeTypeFactor = Risk.getBridgeTypeFactor(typeCode)

                    # K_9
                    materialCode = Risk.getMaterialCode(
                        self.bridges[MATERIAL_CODE_LABEL][i])
                    materialText = self.bridges[MATERIAL_TEXT_LABEL][i]
                    materialFactor = Risk.getMaterialFactor(materialCode)

                    # K_11
                    robustnessFactor = Risk.getRobustnessFactor(
                        yearOfConstruction)

                    # K_13
                    if newDict:
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

                    # fill data frames for diagramms
                    if conditionClass is not None and conditionClass < 9:

                        newDataFrame = pd.DataFrame(
                            [[conditionClass, probabilityOfCollapse]],
                            columns=self.cpScatterColumns)
                        self.conditionPocScatter = pd.concat(
                            [self.conditionPocScatter, newDataFrame])

                        if age is not None:
                            newDataFrame = pd.DataFrame(
                                [[age, conditionClass, probabilityOfCollapse]],
                                columns=self.acpScatterColumns)
                            self.ageConditionPocScatter = pd.concat(
                                [self.ageConditionPocScatter, newDataFrame])

                    if span is not None:
                        newDataFrame = pd.DataFrame(
                            [[span, probabilityOfCollapse]],
                            columns=self.spScatterColumns)
                        self.spanPocScatter = pd.concat(
                            [self.spanPocScatter, newDataFrame])

                    # TODO: There are bridges where the maintenance acceptance
                    # date is 01.01.1900 and the kind of maintenance is
                    # "Abbruch", e.g. S5731, BRÜCKE Gabi 4 N9S and
                    # S5191, BRÜCKE Eggamatt N9S.
                    # There are even obvious errors like the support wall
                    # 52.303.13, SM Oben Nordportal Tunnel Ried FBNO where the
                    # maintenance acceptance date is 31.12.3013.
                    # How do we deal with these dates?
                    bridgeNumber = self.bridges[NUMBER_LABEL][i]
                    maintenance = self.dfMaintenance[
                        self.dfMaintenance[NUMBER_LABEL] == bridgeNumber]
                    maintenanceAcceptanceDate = None
                    maintenanceAcceptanceDateString = _('unknown')
                    if not maintenance.empty:
                        maintenanceAcceptanceDate = maintenance[
                            MAINTENANCE_ACCEPTANCE_DATE_LABEL].iloc[0]
                        if isinstance(maintenanceAcceptanceDate, datetime):
                            newDataFrame = pd.DataFrame(
                                [[maintenanceAcceptanceDate,
                                  probabilityOfCollapse]],
                                columns=self.mpScatterColums)
                            self.maintenancePocScatter = pd.concat(
                                [self.maintenancePocScatter, newDataFrame])
                            maintenanceAcceptanceDateString = format_date(
                                maintenanceAcceptanceDate)

                    # create HTML for marker
                    if age is None:
                        ageText = _('unknown')
                    else:
                        ageText = cached_ngettext(
                            '{0} year', '{0} years', age)
                        ageText = ageText.format(age)

                    normYearString = (
                        _('unknown') if normYear is None
                        else str(normYear))
                    yearOfConstructionString = (
                        _('unknown') if yearOfConstruction is None
                        else str(yearOfConstruction))
                    buildingMaterialString = (
                        _('unknown') if not isinstance(materialText, str)
                        else materialText)

                    message = widgets.HTML()
                    message.value = (
                        '<b>' + _('Name') + '</b>: ' + bridgeName + '<br>' +
                        '<b>' + _('Year of the norm') + '</b>: ' +
                        normYearString + '<br>' +
                        '<b>' + _('Year of construction') + '</b>: ' +
                        yearOfConstructionString + '<br>' +
                        '<b><i>K<sub>1</sub>: ' + _('Human error factor') +
                        '</b>: ' + str(humanErrorFactor) + '</i><br>' +
                        '<b>' + _('Type') + '</b>: ' + typeText + '<br>' +
                        '<b><i>K<sub>3</sub>: ' +
                        _('Statical determinacy factor') + '</b>: ' +
                        str(staticalDeterminacyFactor) + '</i><br>' +
                        '<b>' + _('Age') + '</b>: ' + ageText + '<br>' +
                        '<b><i>P<sub>f</sub>&times;K<sub>4</sub>: ' +
                        _('Condition factor') + '</b>: ' +
                        str(conditionFactor) + '</i><br><b>' + _('Span') +
                        '</b>: ' + (_('unknown') if span is None
                                    else (str(span) + ' m')) +
                        '<br><b><i>K<sub>7</sub>: ' +
                        _('Static calculation factor') + '</b>: ' +
                        str(staticCalculationFactor) + '</i><br>' +
                        '<b><i>K<sub>8</sub>: ' + _('Bridge type factor') +
                        '</b>: ' + str(bridgeTypeFactor) + '</i><br>' +
                        '<b>' + _('Building material') + '</b>: ' +
                        buildingMaterialString + '<br>' +
                        '<b><i>K<sub>9</sub>: ' +
                        _('Building material factor') + '</b>: ' +
                        str(materialFactor) + '</i><br>' +
                        '<b><i>K<sub>11</sub>: ' + _('Robustness factor') +
                        '</b>: ' + str(robustnessFactor) + '</i><br>' +
                        '<b>' + _('Earthquake zone') + '</b>: ' + zoneName +
                        '<br>' + '<b><i>K<sub>13</sub>: ' +
                        _('Earthquake zone factor') + '</b>: ' +
                        str(earthQuakeZoneFactor) + '</i><br>' + '<b>' +
                        _('Last maintenance acceptance date') + '</b>: ' +
                        maintenanceAcceptanceDateString + '<br>' +
                        _('Probability of collapse') + '</b>: ' +
                        str(probabilityOfCollapse) + '<br>')

                    circle_marker = CircleMarker()
                    circle_marker.location = [point.xy[1][0], point.xy[0][0]]
                    circle_marker.popup = message

                    markers.append(circle_marker)

                    newDataFrame = pd.DataFrame({
                        _('Name'): [bridgeName],
                        _('Year of the norm'): [normYearString],
                        _('Year of construction'): [yearOfConstructionString],
                        _('Human error factor'): [humanErrorFactor],
                        _('Type'): [typeText],
                        _('Statical determinacy factor'): [
                            staticalDeterminacyFactor],
                        _('Age'): [ageText],
                        _('Condition factor'): [conditionFactor],
                        _('Span'): [span],
                        _('Static calculation factor'): [
                            staticCalculationFactor],
                        _('Bridge type factor'): [bridgeTypeFactor],
                        _('Building material'): [buildingMaterialString],
                        _('Building material factor'): [materialFactor],
                        _('Robustness factor'): [robustnessFactor],
                        _('Earthquake zone'): [zoneName],
                        _('Earthquake zone factor'): [earthQuakeZoneFactor],
                        _('Last maintenance acceptance date'): [
                            maintenanceAcceptanceDateString],
                        _('Probability of collapse'): [probabilityOfCollapse]})

                    self.dataFrame = pd.concat(
                        [self.dataFrame, newDataFrame], ignore_index=True)

                self.__updateProgressBarAfterTimeout()

            # final update of the progress bar
            self.__updateProgressBar()

            # save earthquakeZonesDict if just created
            if newDict:
                with open(earthquakeZonesDictFileName, 'w') as file:
                    json.dump(self.earthquakeZonesDict, file, indent=4)

            # apply probybility color map to all markers
            maxProbability = self.dataFrame[_('Probability of collapse')].max()
            # probabilityColormap = linear.YlOrRd_04
            # probabilityColormap = linear.RdYlGn_10
            probabilityColormap = linear.Spectral_11
            probabilityColormap = probabilityColormap.scale(0, maxProbability)
            for i in range(0, len(markers)):
                probability = self.dataFrame[_('Probability of collapse')][i]
                probabilityColor = probabilityColormap(
                    maxProbability - probability)
                marker = markers[i]
                marker.probability = probability
                marker.radius = 5 + round(10 * probability / maxProbability)
                marker.color = probabilityColor
                marker.fill_color = probabilityColor

            # sort list by probability
            markers.sort(key=lambda markers: markers.probability)

            # update markerCluster
            if ((self.markerCluster is not None) and
                    (self.markerCluster in self.map.layers)):
                self.map.remove(self.markerCluster)
            self.markerCluster = MarkerCluster(
                markers=markers, name=_("Clustered Bridges"))
            # self.map.add(self.markerCluster)

            # update marker layer
            if ((self.markerGroup is not None) and
                    (self.markerGroup in self.map.layers)):
                self.map.remove(self.markerGroup)
            self.markerGroup = LayerGroup(
                layers=markers, name=_("Individual Bridges"))
            self.map.add(self.markerGroup)

            with self.output:
                display(self.map)
                show(self.dataFrame,
                     buttons=[
                         "pageLength",
                         {"extend": "csvHtml5", "title": _("Bridges")}],
                     column_filters="footer",
                     layout={"top": "searchBuilder"},
                     maxBytes=0)
                self.__showPlots()

            self.bridgesSlider.disabled = False
            self.bridgesIntText.disabled = False
            self.loadButton.disabled = False

        except Exception:
            with self.output:
                print(traceback.format_exc())

    def __showPlots(self):
        # age (x) vs. condition class (y) and probability of collapse (size)
        fig, ax = plt.subplots()
        ax.scatter(
            self.ageConditionPocScatter[self.acpScatterColumns[0]],
            self.ageConditionPocScatter[self.acpScatterColumns[1]],
            s=self.ageConditionPocScatter[self.acpScatterColumns[2]])
        ax.set_xlabel(self.acpScatterColumns[0])
        ax.set_ylabel(self.acpScatterColumns[1])
        ax.set_title(self.acpScatterColumns[2])
        ax.grid(True)
        fig.tight_layout()
        plt.show()

        # age vs. probability of collapse
        fig, ax = plt.subplots()
        ax.scatter(
            self.ageConditionPocScatter[self.acpScatterColumns[0]],
            self.ageConditionPocScatter[self.acpScatterColumns[2]])
        ax.set_xlabel(self.acpScatterColumns[0])
        ax.set_ylabel(self.acpScatterColumns[2])
        ax.grid(True)
        fig.tight_layout()
        plt.show()

        # condition class vs. probability of collapse
        fig, ax = plt.subplots()
        ax.scatter(
            self.conditionPocScatter[self.cpScatterColumns[0]],
            self.conditionPocScatter[self.cpScatterColumns[1]])
        ax.set_xlabel(self.cpScatterColumns[0])
        ax.set_ylabel(self.cpScatterColumns[1])
        ax.grid(True)
        fig.tight_layout()
        plt.show()

        # span vs. probability of collapse
        fig, ax = plt.subplots()
        ax.scatter(
            self.spanPocScatter[self.spScatterColumns[0]],
            self.spanPocScatter[self.spScatterColumns[1]])
        ax.set_xlabel(self.spScatterColumns[0])
        ax.set_ylabel(self.spScatterColumns[1])
        ax.grid(True)
        fig.tight_layout()
        plt.show()

        # maintenance acceptance date vs. probability of collapse
        fig, ax = plt.subplots()
        ax.scatter(
            self.maintenancePocScatter[self.mpScatterColums[0]],
            self.maintenancePocScatter[self.mpScatterColums[1]])
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        ax.set_xlabel(self.mpScatterColums[0])
        ax.set_ylabel(self.mpScatterColums[1])
        ax.grid(True)
        fig.tight_layout()
        plt.show()

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
        # update value
        self.progressBar.value = self.progressBarValue

        # update description
        description = (
            _('Bridges are being loaded') + ': ' +
            str(self.progressBar.value) + '/' +
            str(self.progressBar.max))
        if self.bridgesWithoutCoordinates > 0:
            description += (' (' + str(self.bridgesWithoutCoordinates) +
                            ' ' + _("without coordinates") + ')')
        self.progressBar.description = description
