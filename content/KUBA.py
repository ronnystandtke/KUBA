import folium
import geopandas as gpd
import gettext
import math
import pandas as pd
import ipywidgets as widgets
from datetime import datetime
from IPython.display import display
from IPython.display import clear_output
from shapely.geometry import Point

gettext.bindtextdomain('kuba', 'translations')
gettext.textdomain('kuba')
_ = gettext.gettext

# our constants
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
CURRENT_YEAR = datetime.now().year


class KUBA:

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
        df = pd.read_excel(open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
                           sheet_name='Alle Brücken mit Zusatzinfos')

        # code to get the correct labels
        # print(df.columns.values)

        # convert to GeoDataFrame
        statusText.value = _('Converting points to GeoDataFrames, please wait...')
        points = []
        for i in df.index:
            x = df[X_LABEL][i]
            y = df[Y_LABEL][i]
            points.append(Point(x, y))
        self.bridges = gpd.GeoDataFrame(df, geometry=points, crs='EPSG:2056')

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
            max=self.bridges.index.stop,
            style=initialWidthStyle,
            layout=sliderLayout
        )

        self.bridgesIntText = widgets.IntText(
            description=_('Number of bridges'),
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

        self.output = widgets.Output()

        clear_output()
        display(self.bridgesSlider)
        display(self.bridgesIntText)
        display(self.loadButton)
        display(self.output)

    def getNormYear(self, normText):
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

    def getNormFactor(self, year):
        if year is None:
            # TODO: value for unknown year?
            return 90
        elif year < 1967:
            return 90
        elif year < 1973:
            return 60
        elif year < 1979:
            return 40
        elif year < 1985:
            return 20
        elif year < 2003:
            return 10
        else:
            return 5

    def getAge(self, yearOfConstruction):
        # TODO:
        # there are bridges without a year of construction in the dataset!
        if math.isnan(yearOfConstruction):
            return None
        else:
            return CURRENT_YEAR - int(yearOfConstruction)

    def getConditionFactor(self, age):
        if age is None:
            # TODO: value for unknown ages?
            return 1.019e-4 * 90.31
        elif age < 1:
            return 1.128e-6
        elif age < 2:
            return 2.112e-6 * 1.87
        elif age < 5:
            return 5.067e-6 * 4.49
        elif age < 10:
            return 9.712e-6 * 8.61
        elif age < 15:
            return 1.612e-5 * 14.29
        elif age < 20:
            return 2.066e-5 * 18.31
        elif age < 30:
            return 3.148e-5 * 27.91
        elif age < 40:
            return 4.025e-5 * 35.68
        elif age < 50:
            return 5.102e-5 * 45.22
        elif age < 60:
            return 6.079e-5 * 53.89
        elif age < 70:
            return 7.235e-5 * 64.13
        elif age < 80:
            return 8.117e-5 * 71.95
        elif age < 90:
            return 9.095e-5 * 80.62
        else:
            return 1.019e-4 * 90.31

    def getSpan(self, spanText):
        # TODO: there are bridges without span data!
        if math.isnan(spanText):
            return None
        else:
            return float(spanText)

    def getSpanFactor(self, span):
        # TODO: Erhöhungsfaktor Tragfähigkeit?
        if span is None:
            # TODO: value for unknown spans?
            return 0.0238
        elif span < 6:
            return 0.0023
        elif span < 12:
            return 0.0047
        elif span < 18:
            return 0.0291
        else:
            return 0.0238

    def getTypeFactor(self, type):
        # TODO: check matching between document and table
        if type == 1193:
            # table: "Plattenbrücke"
            # document: "Plattenbalken"
            return 1
        elif type == 1124:
            # table:
            # "Brücke mit versteiftem Stabbogen / Langerscher Balken"
            # document:
            # "Balkenbrücke"
            return 0.6
        elif type == 1132:
            # both: "Hängebrücke"
            return 17.5
        else:
            # TODO: default value (not needed yet, as all bridges in the
            # current data set have a type)
            return 1

    def getMaterialCode(self, codeText):
        # TODO: there are bridges without material data!
        if codeText == '\\' or math.isnan(codeText):
            return None
        else:
            return float(codeText)

    def getMaterialFactor(self, materialCode):
        # TODO: complete mappings?
        if materialCode == 1121:
            # table: "Betonkonstruktion"
            # document: "Beton"
            return 1
        elif materialCode == 1141:
            # table: "Stahlkonstruktion"
            # document: "Stahl"
            return 5.67
        elif materialCode == 117 or materialCode == 1111:
            # table: "Holzkonstruktion" (117)
            # table: "Mauerwerk" (1111)
            # document: "Holz/Mauerwerk"
            return 6.67
        elif materialCode == 1152:
            # table: "Verbundkonstruktion"
            # document: "Verbund"
            return 1
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

    def loadBridges(self):

        self.bridgesSlider.disabled = True
        self.bridgesIntText.disabled = True
        self.loadButton.disabled = True

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

                normYear = self.getNormYear(self.osmBridges[NORM_YEAR_LABEL][i])
                normFactor = self.getNormFactor(normYear)

                yearOfConstruction = self.osmBridges[YEAR_OF_CONSTRUCTION_LABEL][i]
                age = self.getAge(yearOfConstruction)
                conditionFactor = self.getConditionFactor(age)

                span = self.getSpan(self.osmBridges[SPAN_LABEL][i])
                spanFactor = self.getSpanFactor(span)

                typeCode = self.osmBridges[TYPE_CODE_LABEL][i]
                typeText = self.osmBridges[TYPE_TEXT_LABEL][i]
                typeFactor = self.getTypeFactor(typeCode)

                materialCode = self.getMaterialCode(
                    self.osmBridges[MATERIAL_CODE_LABEL][i])
                materialText = self.osmBridges[MATERIAL_TEXT_LABEL][i]
                materialFactor = self.getMaterialFactor(materialCode)

                robustnessFactor = self.getRobustnessFactor(yearOfConstruction)

                zone = self.earthquakeZones[self.earthquakeZones.contains(self.bridges['geometry'][i])]['ZONE']
                if zone.empty:
                    zoneName = _("none")
                else:
                    zoneName = zone.iloc[0]

                self.map.add_child(
                    folium.Marker(
                        location=[point.xy[1][0], point.xy[0][0]],
                        popup=
                            '<b>' + _('Name') + '</b>: ' + str(self.osmBridges['Name'][i] + '<br>' +
                            '<b>' + _('Year of the norm') + '</b>: ' + (_('unknown') if normYear is None else str(normYear)) + '<br>' +
                            '<b>' + _('Error correction factor') + '</b>: ' + str(normFactor) + '<br>' +
                            '<b>' + _('Age') + '</b>: ' + (_('unknown') if age is None else str(age)) + '<br>' +
                            '<b>' + _('Condition factor') + '</b>: ' + str(conditionFactor) + '<br>' +
                            '<b>' + _('Span') + '</b>: ' + str(span) + ' m<br>' +
                            '<b>' + _('Static factor') + '</b>: ' + str(spanFactor) + '<br>' +
                            '<b>' + _('Type') + '</b>: ' + typeText + '<br>' +
                            '<b>' + _('Type factor') + '</b>: ' + str(typeFactor) + '<br>' +
                            '<b>' + _('Building material') + '</b>: ' + (_('unknown') if not isinstance(materialText, str) else materialText) + '<br>' +
                            '<b>' + _('Building material factor') + '</b>: ' + str(materialFactor) + '<br>' +
                            '<b>' + _('Robustness factor') + '</b>: ' + str(robustnessFactor) + '<br>' +
                            '<b>' + _('Earthquake zone') + '</b>: ' + zoneName + '<br>'),
                            # icon=folium.Icon(color="%s" % type_color)
                            icon=folium.Icon(color="lightblue")
                    )
                )

        self.output.clear_output(wait=True)
        with self.output:
            display(self.map)

        self.bridgesSlider.disabled = False
        self.bridgesIntText.disabled = False
        self.loadButton.disabled = False
