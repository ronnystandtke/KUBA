# TODO: i18n, L10n

# imports
import folium
import geopandas as gpd
import math
import pandas as pd
import ipywidgets as widgets
from datetime import datetime
from IPython.display import display
from IPython.display import clear_output
from shapely.geometry import Point


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
    earthquakeZones = None
    map = None

    def __init__(self):
        # read file with data
        df = pd.read_excel(open('data/Bauwerksdaten aus KUBA.xlsx', 'rb'),
                           sheet_name='Alle Brücken mit Zusatzinfos')

        # code to get the correct labels
        # print(df.columns.values)

        # convert to GeoDataFrame
        points = []
        for i in df.index:
            x = df[X_LABEL][i]
            y = df[Y_LABEL][i]
            points.append(Point(x, y))
        self.bridges = gpd.GeoDataFrame(df, geometry=points, crs='EPSG:2056')
        self.earthquakeZones = gpd.read_file(
            "zip://data/erdbebenzonen.zip!Erdbebenzonen")

        # risk calculations

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

    def start(self):

        # map = folium.Map(location=[47.15826, 7.27716], tiles="OpenStreetMap", zoom_start=9)
        self.map = self.earthquakeZones.explore("ZONE", cmap="OrRd")

        # Leaflet always works in EPSG:4326
        # therefore we have to convert the CRS here
        osmBridges = self.bridges.to_crs('EPSG:4326')

        # create a progress bar
        progressBar = widgets.IntProgress(
            value=0,
            min=0,
            max=self.bridges.index.stop,
            description='Brücken werden geladen:',
            description_width=200,
            # bar_style can be 'success', 'info', 'warning', 'danger' or ''
            bar_style='success',
            style={'bar_color': 'green', 'description_width': 'initial'},
            orientation='horizontal',
            layout=widgets.Layout(width='auto')
        )

        display(progressBar)

        # for i in osmBridges.index:
        for i in range(0, 100):
            point = osmBridges['geometry'][i]
            # there ARE empty coordinates in the table! :-(
            if not point.is_empty:

                normYear = self.getNormYear(osmBridges[NORM_YEAR_LABEL][i])
                normFactor = self.getNormFactor(normYear)

                yearOfConstruction = osmBridges[YEAR_OF_CONSTRUCTION_LABEL][i]
                age = self.getAge(yearOfConstruction)
                conditionFactor = self.getConditionFactor(age)

                span = self.getSpan(osmBridges[SPAN_LABEL][i])
                spanFactor = self.getSpanFactor(span)

                typeCode = osmBridges[TYPE_CODE_LABEL][i]
                typeText = osmBridges[TYPE_TEXT_LABEL][i]
                typeFactor = self.getTypeFactor(typeCode)

                materialCode = self.getMaterialCode(
                    osmBridges[MATERIAL_CODE_LABEL][i])
                materialText = osmBridges[MATERIAL_TEXT_LABEL][i]
                materialFactor = self.getMaterialFactor(materialCode)

                robustnessFactor = self.getRobustnessFactor(yearOfConstruction)

                zone = self.earthquakeZones[self.earthquakeZones.contains(self.bridges['geometry'][i])]['ZONE']
                if zone.empty:
                    zoneName = "keine"
                else:
                    zoneName = zone.iloc[0]

                self.map.add_child(
                    folium.Marker(
                        location=[point.xy[1][0], point.xy[0][0]],
                        popup=
                            '<b>Name</b>: ' + str(osmBridges['Name'][i] + '<br>' +
                            '<b>Jahr der Norm</b>: ' + ("unbekannt" if normYear is None else str(normYear)) + '<br>' +
                            '<b>Fehlerkorrekturfaktor</b>: ' + str(normFactor) + '<br>' +
                            '<b>Alter</b>: ' + ("unbekannt" if age is None else str(age)) + '<br>' +
                            '<b>Zustandsfaktor</b>: ' + str(conditionFactor) + '<br>' +
                            '<b>Spannweite</b>: ' + str(span) + ' m<br>' +
                            '<b>Statikfaktor</b>: ' + str(spanFactor) + '<br>' +
                            '<b>Typ</b>: ' + typeText + '<br>' +
                            '<b>Typfaktor</b>: ' + str(typeFactor) + '<br>' +
                            '<b>Baustoff</b>: ' + ('unbekannt' if not isinstance(materialText, str) else materialText) + '<br>' +
                            '<b>Baustoff-Faktor</b>: ' + str(materialFactor) + '<br>' +
                            '<b>Robustheitsfaktor</b>: ' + str(robustnessFactor) + '<br>' +
                            '<b>Erdbebenzone</b>: ' + zoneName + '<br>'),
                            # icon=folium.Icon(color="%s" % type_color)
                            icon=folium.Icon(color="lightblue")
                    )
                )
                progressBar.value += 1
                progressBar.description = 'Brücken werden geladen: ' + str(progressBar.value) + '/' + str(progressBar.max)

        clear_output()
        display(self.map)
