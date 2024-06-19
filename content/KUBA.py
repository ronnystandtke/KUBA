import geopandas as gpd
import gettext
import json
import math
import os.path
import time
import pandas as pd
import ipywidgets as widgets
import traceback
from branca.colormap import linear
from functools import cache
from ipyleaflet import (basemaps, Choropleth, CircleMarker, LayerGroup,
                        LayersControl, LegendControl, Map, MarkerCluster,
                        WidgetControl)
from IPython.display import clear_output
from IPython.display import display
from itables import init_notebook_mode, show
from Risk import Risk
from shapely.geometry import Point

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
SPAN_LABEL = 'Spannweite [m]'
TYPE_CODE_LABEL = 'Typ\xa0Hierarchie-Code'
TYPE_TEXT_LABEL = 'Typ\xa0Text'
MATERIAL_CODE_LABEL = 'Bauart\xa0Code'
MATERIAL_TEXT_LABEL = 'Bauart\xa0Text'
CONDITION_CLASS_LABEL = 'Zustands- Klasse'
FUNCTION_TEXT_LABEL = 'Funktion\xa0Text'

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

        # load pre-calculated earthquake zone data
        self.earthquakeZonesDict = {}
        if os.path.isfile(earthquakeZonesDictFileName):
            with open(earthquakeZonesDictFileName) as file:
                self.earthquakeZonesDict = json.load(file)

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
        # print(dfBuildings.columns.values)

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
        self.map = Map(
            basemap=basemaps.OpenStreetMap.Mapnik,
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
            value=200,
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
        display(self.sliderHBox)
        display(self.loadButton)
        display(self.output)

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

            markers = ()
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
                _('Probability of collapse'): []})

            riskColormap = linear.YlOrRd_04

            self.bridgesWithoutCoordinates = 0
            self.lastProgressBarUpdate = 0
            self.progressBarValue = 0

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
                    span = Risk.getSpan(self.bridges[SPAN_LABEL][i])
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
                    point = self.bridges['geometry'][i]
                    if newDict:
                        zone = self.earthquakeZones[
                            self.earthquakeZones.contains(point)]['ZONE']
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
                        str(conditionFactor) + '</i><br>' +
                        '<b>' + _('Span') + '</b>: ' + str(span) + ' m<br>' +
                        '<b><i>K<sub>7</sub>: ' +
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
                        _('Probability of collapse') + '</b>: ' +
                        str(probabilityOfCollapse) + '<br>')

                    circle_marker = CircleMarker()
                    circle_marker.location = [point.xy[1][0], point.xy[0][0]]
                    circle_marker.radius = 10
                    circle_marker.popup = message

                    markers = markers + (circle_marker,)

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

            # apply risk color map to all markers
            riskColormap = riskColormap.scale(
                0, self.dataFrame[_('Probability of collapse')].max())
            for i in range(0, len(markers)):
                risk = self.dataFrame[_('Probability of collapse')][i]
                riskColor = riskColormap(risk)
                marker = markers[i]
                marker.color = riskColor
                marker.fill_color = riskColor

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

            self.bridgesSlider.disabled = False
            self.bridgesIntText.disabled = False
            self.loadButton.disabled = False

        except Exception:
            with self.output:
                print(traceback.format_exc())

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
