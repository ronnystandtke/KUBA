import branca
import folium
import geopandas as gpd
import gettext
import math
import pandas as pd
import ipywidgets as widgets
import traceback
from datetime import datetime
from IPython.display import display
from IPython.display import clear_output
from shapely.geometry import Point

gettext.bindtextdomain('kuba', 'translations')
gettext.textdomain('kuba')
_ = gettext.gettext

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
CURRENT_YEAR = datetime.now().year


class KUBA:

    output = widgets.Output()

    bridges = None
    osmBridges = None
    earthquakeZones = None
    map = None

    def __init__(self):
        statusText = widgets.Text(
            value='', layout=widgets.Layout(width='95%'), disabled=True)
        display(statusText)

        # read file with data
        statusText.value = _('Loading building data, please wait...')

        # dfAllBuildings = pd.read_excel(open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
        #                    sheet_name='Alle Bauwerke mit Zusatzinfo')

        dfBridges = pd.read_excel(
            open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
            sheet_name='Alle Brücken mit Zusatzinfos')

        # dfBuildings = pd.read_excel(open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
        #                    sheet_name='Bauwerke mitErdbebenüberprüfung')

        # check how many bridges we find in the other sheets
        # bridgeInAllBuildings = 0
        # bridgeNotInAllBuildings = 0
        # bridgeInBuildings = 0
        # bridgeNotInBuildings = 0
        # for bridgeNumber in dfBridges[NUMBER_LABEL]:

        #     if bridgeNumber in dfAllBuildings[ALL_BUILDINGS_NUMBER_LABEL].values:
        #         bridgeInAllBuildings += 1
        #     else:
        #         bridgeNotInAllBuildings += 1

        #     if bridgeNumber in dfBuildings[NUMBER_LABEL].values:
        #         bridgeInBuildings += 1
        #     else:
        #         bridgeNotInBuildings += 1

        # print("number of bridges found in sheet 'Alle Bauwerke mit Zusatzinfo':", bridgeInAllBuildings)
        # print("number of bridges NOT found in sheet 'Alle Bauwerke mit Zusatzinfo':", bridgeNotInAllBuildings)
        # print("number of bridges found in sheet 'Bauwerke mitErdbebenüberprüfung':", bridgeInBuildings)
        # print("number of bridges NOT found in sheet 'Bauwerke mitErdbebenüberprüfung':", bridgeNotInBuildings)

        # code to get the correct labels
        # print(dfBuildings.columns.values)

        # convert to GeoDataFrame
        statusText.value = _('Converting points to GeoDataFrames, please wait...')
        points = []
        for i in dfBridges.index:
            x = dfBridges[X_LABEL][i]
            y = dfBridges[Y_LABEL][i]
            points.append(Point(x, y))
        self.bridges = gpd.GeoDataFrame(dfBridges, geometry=points, crs='EPSG:2056')

        statusText.value = _('Loading earthquake zones, please wait...')
        self.earthquakeZones = gpd.read_file(
            "zip://data/erdbebenzonen.zip!Erdbebenzonen")

        # Leaflet always works in EPSG:4326
        # therefore we have to convert the CRS here
        statusText.value = _('Converting CRS, please wait...')
        self.osmBridges = self.bridges.to_crs('EPSG:4326')

        initialWidthStyle = {'description_width': 'initial'}
        sliderLayout = widgets.Layout(width='95%')
        self.bridgesSlider = widgets.IntSlider(
            description=_('Number of bridges'),
            value=20,
            min=1,
            max=self.bridges.index.stop,
            style=initialWidthStyle,
            layout=sliderLayout
        )

        self.bridgesIntText = widgets.BoundedIntText(
            description=_('Number of bridges'),
            min=1,
            max=self.bridges.index.stop,
            style=initialWidthStyle
        )
        widgets.link((self.bridgesSlider, 'value'), (self.bridgesIntText, 'value'))

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
            description=_('Bridges are being loaded') + ': ' + str(0) + '/' + str(self.bridges.index.stop),
            description_width=200,
            # bar_style can be 'success', 'info', 'warning', 'danger' or ''
            bar_style='success',
            style={'bar_color': 'green', 'description_width': 'initial'},
            orientation='horizontal',
            layout=widgets.Layout(width='auto')
        )

        clear_output()
        display(self.bridgesSlider)
        display(self.bridgesIntText)
        display(self.loadButton)
        display(self.output)

    @output.capture()
    def getNormYear(self, normText):
        try:
            if isinstance(normText, str):
                segments = normText.split(',')
                if len(segments) > 1:
                    year = segments[0]
                    if '/' in year:
                        # some years are formatted like this: "1913/15"
                        return int(year.split('/')[0])
                    else:
                        return int(year)
                else:
                    # text without year prefix
                    return None
            else:
                # empty text
                return None
        except Exception:
            with self.output:
                print(traceback.format_exc())

    @output.capture()
    def getHumanErrorFactor(self, normYear, yearOfConstruction):
        # factor K_1 ("Faktor für menschliche Fehler")
        try:
            # if the year of the norm generation is unknown
            # we use the year of construction
            if normYear is None:
                if yearOfConstruction is None:
                    # TODO: is this correct if both years are unknown?
                    return 90
                else:
                    relevantYear = yearOfConstruction
            else:
                relevantYear = normYear

            if (relevantYear is None) or (relevantYear < 1967):
                return 90
            elif relevantYear < 1973:
                return 60
            elif relevantYear < 1979:
                return 40
            elif relevantYear < 1985:
                return 20
            elif relevantYear < 2003:
                return 10
            else:
                return 5
        except Exception:
            with self.output:
                print(traceback.format_exc())

    def getStaticalDeterminacyFactor(self, type):
        # factor K_3 ("statische Bestimmtheit")
        if type == 1111:
            # Brücke mit Einfeldträger
            return 1
        elif type == 1112:
            # Brücke mit Durchlaufträger
            return 0.014
        else:
            # TODO: what about all other types?
            return None

    def getAge(self, yearOfConstruction):
        # TODO:
        # there are bridges without a year of construction in the dataset!
        if math.isnan(yearOfConstruction):
            return None
        else:
            return CURRENT_YEAR - int(yearOfConstruction)

    def getConditionFactor(self, conditionClass, age):
        # factor P_f * K_4 ("Zustandsklasse")

        if conditionClass is None:
            # TODO: correct value for unknown condition classes?
            h1 = 3e-5
        elif conditionClass < 3:
            h1 = 1e-6
        elif conditionClass < 4:
            h1 = 3e-6
        elif conditionClass < 5:
            h1 = 1e-5
        else:
            h1 = 3e-5

        if age is None:
            # TODO: value for unknown ages?
            h2 = 1.019e-4 * 90.31
        elif age <= 1:
            h2 = 1.128e-6
        elif age <= 2:
            h2 = 2.112e-6 * 1.87
        elif age <= 5:
            h2 = 5.067e-6 * 4.49
        elif age <= 10:
            h2 = 9.712e-6 * 8.61
        elif age <= 15:
            h2 = 1.612e-5 * 14.29
        elif age <= 20:
            h2 = 2.066e-5 * 18.31
        elif age <= 30:
            h2 = 3.148e-5 * 27.91
        elif age <= 40:
            h2 = 4.025e-5 * 35.68
        elif age <= 50:
            h2 = 5.102e-5 * 45.22
        elif age <= 60:
            h2 = 6.079e-5 * 53.89
        elif age <= 70:
            h2 = 7.235e-5 * 64.13
        elif age <= 80:
            h2 = 8.117e-5 * 71.95
        elif age <= 90:
            h2 = 9.095e-5 * 80.62
        else:
            h2 = 1.019e-4 * 90.31

        return 0.7 * h1 + 0.3 * h2

    def getSpan(self, spanText):
        # TODO: there are bridges without span data!
        if math.isnan(spanText):
            return None
        else:
            return float(spanText)

    def getStaticCalculationFactor(self, span):
        # factor K_7 ("Statische Berechnung")

        if span is None:
            # TODO: value for unknown spans?
            h1 = 0.0238
        elif span < 6:
            h1 = 0.0023
        elif span < 12:
            h1 = 0.0047
        elif span < 18:
            h1 = 0.0291
        else:
            h1 = 0.0238

        return 0.9 + 0.1 + h1

    def getBridgeTypeFactor(self, type):
        # factor K_8 ("Brückentyp")

        if type == 1193:
            # table:
            # 1193: "Plattenbrücke"
            # document:
            # "Plattenbalken"
            return 1

        elif (type == 1111) or (type == 1112) or (type == 1113):
            # table:
            # 1111: "Brücke mit Einfeldträger"
            # 1112: "Brücke mit Durchlaufträger"
            # 1113: "Brücke mit Gerberträger"
            # document:
            # "Balkenbrücke"
            return 0.6

        elif (type == 1123) or (type == 1124) or (type == 11) or (type == 1125) or (type == 112):
            # table:
            # 1123: "Brücke mit Bogentragwerk"
            # 1124: "Brücke mit versteiftem Stabbogen / Langerscher Balken"
            # 11: "Brücke, Viadukt"
            # 1125: "Gewölbekonstruktion"
            # 112: "Rahmen-, Bogenbrücken"
            # document:
            # "Bogen"
            return 1.6

        elif (type == 1192) or (type == 1131) or (type == 191) or (type == 1133) or (type == 119):
            # table:
            # 1192: "Brücke auf Wanne"
            # 1131: "Schrägseilbrücke"
            # 191: "Brückenanlage"
            # 1133: "Spannbandbrücke"
            # 119: "Spezielle Brücke"
            # document:
            # "Andere"
            return 5

        elif (type == 1121) or (type == 1122):
            # table:
            # 1121: "Brücke mit Rahmentragwerk"
            # 1122: "Brücke mit Sprengwerk"
            # document:
            # "Rahmen"
            return 0.4

        elif type == 1132:
            # both: "Hängebrücke"
            return 17.5

        else:
            # TODO: default value?
            return 1

    def getMaterialCode(self, codeText):
        # TODO: there are bridges without material data!
        if codeText == '\\' or math.isnan(codeText):
            return None
        else:
            return float(codeText)

    def getMaterialFactor(self, materialCode):
        # factor K_9 ("Baustoff")

        if (materialCode == 1123) or (materialCode == 1125) or (materialCode == 1121) or (materialCode == 1124):
            # table:
            # 1123: "Stahlbetonkonstruktion"
            # 1125: "Spannbetonkonstruktion"
            # 1121: "Betonkonstruktion"
            # 1124: "Verkleidete Stahlbetonkonstruktion"
            # document:
            # "Beton"
            return 1

        elif materialCode == 1141:
            # table:
            # 1141: "Stahlkonstruktion"
            # document:
            # "Stahl"
            return 5.67

        elif (materialCode == 1112) or (materialCode == 117) or (materialCode == 1111):
            # table:
            # 1112: "Ausbetoniertes Mauerwerk"
            # 117: "Holzkonstruktion"
            # 1111: "Mauerwerk"
            # document:
            # "Holz/Mauerwerk"
            return 6.67

        elif (materialCode == 1152) or (materialCode == 1153):
            # table:
            # 1152: "Verbundkonstruktion"
            # 1153: "Verbundkonstruktion mit Vorspannung"
            # document:
            # "Verbund"
            return 1

        elif (materialCode == 1162) or (materialCode == 1133):
            # table:
            # 1162: "Vorgespannte Seilkonstruktion"
            # 1133: "Wellblechkonstruktion"
            # document:
            # "Sonstiges"
            return 6.67

        else:
            # TODO: default value?
            return 1

    def getRobustnessFactor(self, yearOfConstruction):
        # TODO:
        # there are bridges without a year of construction in the dataset!
        if math.isnan(yearOfConstruction):
            # TODO: value for unkonwn year?
            return 5
        else:
            if yearOfConstruction < 1968:
                return 5
            elif yearOfConstruction < 1973:
                return 4.5
            elif yearOfConstruction < 1980:
                return 3.3
            elif yearOfConstruction < 1986:
                return 1.4
            elif yearOfConstruction < 2003:
                return 1.2
            else:
                return 1

    @output.capture()
    def loadBridges(self):

        try:
            self.bridgesSlider.disabled = True
            self.bridgesIntText.disabled = True
            self.loadButton.disabled = True

            self.progressBar.value = 0
            self.progressBar.max = self.bridgesSlider.value
            self.progressBar.description = _('Bridges are being loaded') + ': ' + str(self.progressBar.value) + '/' + str(self.progressBar.max)

            self.output.clear_output(wait=True)
            with self.output:
                display(self.progressBar)

            # create a fresh map (we can't remove existing markers from the map)
            # map = folium.Map(location=[47.15826, 7.27716], tiles="OpenStreetMap", zoom_start=9)
            self.map = self.earthquakeZones.explore("ZONE", cmap="OrRd")

            for i in range(0, self.bridgesSlider.value):
                point = self.osmBridges['geometry'][i]
                # there ARE empty coordinates in the table! :-(
                if not point.is_empty:

                    self.progressBar.value += 1
                    self.progressBar.description = _('Bridges are being loaded') + ': ' + str(self.progressBar.value) + '/' + str(self.progressBar.max)

                    # K_1
                    normYear = self.getNormYear(self.osmBridges[NORM_YEAR_LABEL][i])
                    yearOfConstruction = self.osmBridges[YEAR_OF_CONSTRUCTION_LABEL][i]
                    if not math.isnan(yearOfConstruction):
                        yearOfConstruction = int(yearOfConstruction)
                    humanErrorFactor = self.getHumanErrorFactor(normYear, yearOfConstruction)

                    # K_3
                    typeCode = self.osmBridges[TYPE_CODE_LABEL][i]
                    typeText = self.osmBridges[TYPE_TEXT_LABEL][i]
                    staticalDeterminacyFactor = self.getStaticalDeterminacyFactor(typeCode)

                    # P_f * K_4
                    conditionClass = self.osmBridges[CONDITION_CLASS_LABEL][i]
                    age = self.getAge(yearOfConstruction)
                    conditionFactor = self.getConditionFactor(conditionClass, age)

                    # K_7
                    span = self.getSpan(self.osmBridges[SPAN_LABEL][i])
                    staticCalculationFactor = self.getStaticCalculationFactor(span)

                    # K_8
                    bridgeTypeFactor = self.getBridgeTypeFactor(typeCode)

                    # K_9
                    materialCode = self.getMaterialCode(
                        self.osmBridges[MATERIAL_CODE_LABEL][i])
                    materialText = self.osmBridges[MATERIAL_TEXT_LABEL][i]
                    materialFactor = self.getMaterialFactor(materialCode)

                    # K_11
                    robustnessFactor = self.getRobustnessFactor(yearOfConstruction)

                    zone = self.earthquakeZones[self.earthquakeZones.contains(self.bridges['geometry'][i])]['ZONE']
                    if zone.empty:
                        zoneName = _("none")
                    else:
                        zoneName = zone.iloc[0]

                    if age is None:
                        ageText = _('unknown')
                    else:
                        ageText = gettext.ngettext('{0} year', '{0} years', age)
                        ageText = ageText.format(age)

                    html = str('<b>' + _('Name') + '</b>: ' + str(self.osmBridges['Name'][i]) + '<br>' +
                        '<b>' + _('Year of the norm') + '</b>: ' + (_('unknown') if normYear is None else str(normYear)) + '<br>' +
                        '<b>' + _('Year of construction') + '</b>: ' + (_('unknown') if yearOfConstruction is None else str(yearOfConstruction)) + '<br>' +
                        '<b><i>K<sub>1</sub>: ' + _('Human error factor') + '</b>: ' + str(humanErrorFactor) + '</i><br>' +
                        '<b>' + _('Type') + '</b>: ' + typeText + '<br>' +
                        '<b><i>K<sub>3</sub>: ' + _('Statical determinacy factor') + '</b>: ' + str(staticalDeterminacyFactor) + '</i><br>' +
                        '<b>' + _('Age') + '</b>: ' + ageText + '<br>' +
                        '<b><i>P<sub>f</sub>&times;K<sub>4</sub>: ' + _('Condition factor') + '</b>: ' + str(conditionFactor) + '</i><br>' +
                        '<b>' + _('Span') + '</b>: ' + str(span) + ' m<br>' +
                        '<b><i>K<sub>7</sub>: ' + _('Static calculation factor') + '</b>: ' + str(staticCalculationFactor) + '</i><br>' +
                        '<b><i>K<sub>8</sub>: ' + _('Bridge type factor') + '</b>: ' + str(bridgeTypeFactor) + '</i><br>' +
                        '<b>' + _('Building material') + '</b>: ' + (_('unknown') if not isinstance(materialText, str) else materialText) + '<br>' +
                        '<b><i>K<sub>9</sub>: ' + _('Building material factor') + '</b>: ' + str(materialFactor) + '</i><br>' +
                        '<b><i>K<sub>11</sub>: ' + _('Robustness factor') + '</b>: ' + str(robustnessFactor) + '</i><br>' +
                        '<b>' + _('Earthquake zone') + '</b>: ' + zoneName + '<br>')
                    iframe = branca.element.IFrame(html=html, width=450, height=400)
                    popup = folium.Popup(iframe)
                    icon = folium.Icon(color="lightblue")
                    marker = folium.Marker(location=[point.xy[1][0], point.xy[0][0]], popup=popup, icon=icon)
                    self.map.add_child(marker)

            self.output.clear_output(wait=True)
            with self.output:
                display(self.map)

            self.bridgesSlider.disabled = False
            self.bridgesIntText.disabled = False
            self.loadButton.disabled = False

        except Exception:
            with self.output:
                print(traceback.format_exc())
