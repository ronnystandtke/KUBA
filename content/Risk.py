import math
from datetime import datetime
CURRENT_YEAR = datetime.now().year


class Risk:

    @staticmethod
    def getNormYear(normText):
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

    @staticmethod
    def getHumanErrorFactor(normYear, yearOfConstruction):
        # factor K_1 ("Faktor für menschliche Fehler")

        # if the year of the norm generation is unknown
        # we use the year of construction
        if normYear is None:
            if yearOfConstruction is None:
                return 90
            else:
                relevantYear = yearOfConstruction
        else:
            relevantYear = normYear

        if (relevantYear is None) or (relevantYear < 1967):
            return 9
        elif relevantYear < 1973:
            return 6
        elif relevantYear < 1979:
            return 4
        elif relevantYear < 1985:
            return 2
        elif relevantYear < 2003:
            return 1
        else:
            return 0.5

    @staticmethod
    def getStaticalDeterminacyFactor(type):
        # factor K_3 ("statische Bestimmtheit")
        if type == 1111:
            # Brücke mit Einfeldträger
            return 1
        elif type == 1112:
            # Brücke mit Durchlaufträger
            return 0.014
        else:
            return None

    @staticmethod
    def getAge(yearOfConstruction):
        if math.isnan(yearOfConstruction) or yearOfConstruction == -1:
            return None
        else:
            return CURRENT_YEAR - int(yearOfConstruction)

    @staticmethod
    def getConditionFactor(conditionClass, age):
        # factor P_f * K_4 ("Zustandsklasse")
        h1 = Risk.__getConditionFactorH1(conditionClass)
        h2 = Risk.__getConditionFactorH2(age)
        return 0.7 * h1 + 0.3 * h2

    @staticmethod
    def __getConditionFactorH1(conditionClass):
        # see table 3.23 ("Festlegung H1")
        if conditionClass is None:
            # use worst value if condition class is unknown
            return 3e-5
        if conditionClass < 3:
            return 1e-6
        if conditionClass < 4:
            return 3e-6
        if conditionClass < 5:
            return 1e-5
        else:
            return 3e-5

    @staticmethod
    def __getConditionFactorH2(age):
        # see table 3.24 ("Festlegung H2")
        if age is None:
            # use worst value if age is unknown
            return 1.019e-4 * 90.31
        if age <= 1:
            return 1.128e-6
        if age <= 2:
            return 2.112e-6 * 1.87
        if age <= 5:
            return 5.067e-6 * 4.49
        if age <= 10:
            return 9.712e-6 * 8.61
        if age <= 15:
            return 1.612e-5 * 14.29
        if age <= 20:
            return 2.066e-5 * 18.31
        if age <= 30:
            return 3.148e-5 * 27.91
        if age <= 40:
            return 4.025e-5 * 35.68
        if age <= 50:
            return 5.102e-5 * 45.22
        if age <= 60:
            return 6.079e-5 * 53.89
        if age <= 70:
            return 7.235e-5 * 64.13
        if age <= 80:
            return 8.117e-5 * 71.95
        if age <= 90:
            return 9.095e-5 * 80.62
        else:
            return 1.019e-4 * 90.31

    @staticmethod
    def getOverpassFactor(functionText):
        # factor K_6 ("Berücksichtigung der Überführung")

        if functionText is None:
            # return the highest factor for unknown overpass situations
            return 8.7

        # the function texts contain non-breaking spaces
        # improve readability of the code below by
        # replacing them with normal spaces
        myFunctionText = functionText.replace(u'\xa0', u' ')

        if ((myFunctionText == 'Überquert anderes Infrastrukturobjekt') or
                (myFunctionText == 'Überquert Bahnanlage') or
                (myFunctionText == 'Überquert Strasse / Weg') or
                (myFunctionText == 'Überquert übrige Infrastruktur') or
                (myFunctionText == 'Überquert Verkehrsweg') or
                (myFunctionText == 'Überquert anderes')):
            return 5

        elif ((myFunctionText == 'Überquert Fluss') or
              (myFunctionText == 'Überquert Gewässer') or
              (myFunctionText == 'Überquert Kanal')):
            return 8.7

        elif ((myFunctionText == 'Überquert Natur') or
              (myFunctionText == 'Überquert Leitungen')):
            return 1

        else:
            # should not happen with current dataset...
            # but treat it like an unknown situation and
            # return the highest factor
            print("WARNING: unknown function text: \"" + myFunctionText + "\"")
            return 8.7

    @staticmethod
    def getSpan(spanText):
        if math.isnan(spanText):
            return None
        else:
            return float(spanText)

    @staticmethod
    def getStaticCalculationFactor(span):
        # factor K_7 ("Statische Berechnung")

        # If the span is unknown we use the minimal H3 value
        if span is None or span < 6:
            h3 = 0.0023
        elif span < 12:
            h3 = 0.0047
        elif span < 18:
            h3 = 0.0291
        else:
            h3 = 0.0238

        return 0.7 + 5 * h3

    @staticmethod
    def getBridgeTypeFactor(type):
        # factor K_8 ("Brückentyp")

        if type == 1193:
            # table:
            # 1193: "Plattenbrücke"
            # document:
            # "Plattenbalken"
            return 0.6

        elif (type == 1111) or (type == 1112) or (type == 1113):
            # table:
            # 1111: "Brücke mit Einfeldträger"
            # 1112: "Brücke mit Durchlaufträger"
            # 1113: "Brücke mit Gerberträger"
            # document:
            # "Balkenbrücke"
            return 0.36

        elif ((type == 1123) or
              (type == 1124) or
              (type == 11) or
              (type == 1125) or
              (type == 112)):
            # table:
            # 1123: "Brücke mit Bogentragwerk"
            # 1124: "Brücke mit versteiftem Stabbogen / Langerscher Balken"
            # 11: "Brücke, Viadukt"
            # 1125: "Gewölbekonstruktion"
            # 112: "Rahmen-, Bogenbrücken"
            # document:
            # "Bogen"
            return 0.96

        elif ((type == 1192) or
              (type == 1131) or
              (type == 191) or
              (type == 1133) or
              (type == 119)):
            # table:
            # 1192: "Brücke auf Wanne"
            # 1131: "Schrägseilbrücke"
            # 191: "Brückenanlage"
            # 1133: "Spannbandbrücke"
            # 119: "Spezielle Brücke"
            # document:
            # "Andere"
            return 3

        elif (type == 1121) or (type == 1122):
            # table:
            # 1121: "Brücke mit Rahmentragwerk"
            # 1122: "Brücke mit Sprengwerk"
            # document:
            # "Rahmen"
            return 0.24

        elif type == 1132:
            # both: "Hängebrücke"
            return 3

        else:
            # default value for unknown types
            return 0.36

    @staticmethod
    def getMaterialCode(codeText):
        if codeText == '\\' or math.isnan(codeText):
            return None
        else:
            return float(codeText)

    @staticmethod
    def getMaterialFactor(materialCode):
        # factor K_9 ("Baustoff")

        # TODO:
        # There are unhandled materials:
        # "Seilkonstruktion"
        # (code: 1161, e.g. 1.043-1, UEF FG Mühlematt Liestal)
        # "Spannbetonkonstruktion (ohne Verbund)"
        # (code: 1126, e.g. S0161, BRÜCKE Bachhalden)
        # "Trockensteinmauer mit behauenen Steinen aufgebaut"
        # (code: 1114, e.g. S5811, BRÜCKE Hohsteg U57)
        # "Verkleidete Betonkonstruktion"
        # (code: 1122, e.g. 6A - AK 1, BRÜCKE AK Herbizug Sisikon)
        #
        # TODO:
        # "Erd- und Wellblechkonstruktion" doesn't appear as one in the table
        # only as separated materials
        # 1133: "Wellblechkonstruktion"
        # 1135: "Erdkonstruktion"
        #
        # TODO:
        # "alte Stahlfachwerkbrücken" is not in the table...

        if (
                (materialCode == 1123) or
                (materialCode == 1125) or
                (materialCode == 1121) or
                (materialCode == 1124)):
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

        elif ((materialCode == 1112) or
              (materialCode == 117) or
              (materialCode == 1111)):
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

        elif ((materialCode == 1162) or
              (materialCode == 1133) or
              (materialCode == 1135)):
            # table:
            # 1162: "Vorgespannte Seilkonstruktion"
            # 1133: "Wellblechkonstruktion"
            # 1135: "Erdkonstruktion"
            # document:
            # "Sonstiges"
            return 6.67

        else:
            # default value is larges value in list
            return 6.67

    @staticmethod
    def getRobustnessFactor(yearOfConstruction):
        # factor K_11 ("Baustoff")

        # changed after meeting of 2024-07-22
        return 1

        # if math.isnan(yearOfConstruction):
        #     # if year of construction is unkown we use the maximum value
        #     return 5
        # else:
        #     if yearOfConstruction < 1968:
        #         return 5
        #     elif yearOfConstruction < 1973:
        #         return 4.5
        #     elif yearOfConstruction < 1980:
        #         return 3.3
        #     elif yearOfConstruction < 1986:
        #         return 1.4
        #     elif yearOfConstruction < 2003:
        #         return 1.2
        #     else:
        #         return 1

    @staticmethod
    def getEarthQuakeZoneFactor(zoneName, yearOfConstruction, type):
        # factor K_13 ("Erdbeben")

        # if a successful earthquake test is available, the factor 1 is used
        # TODO:
        # In the table "Bauwerke mitErdbebenüberprüfung" are many buildings
        # where the column "Erdbebenbeurteilung Datum der Überprüfung" is
        # empty. Treat them as "no test available?"
        # There are buildings with a date but without any
        # "Erdbebenbeurteilung erfüllt XXX". How to treat them?

        successfull_earthquake_test_available = False

        if successfull_earthquake_test_available:
            return 1

        earthQuakeFactorH4 = Risk.__getEarthQuakeFactorH4(type)
        if earthQuakeFactorH4 is not None:
            return earthQuakeFactorH4

        return Risk.__getCollapseProbabilityIncreasingFactor(
                zoneName, yearOfConstruction)

    @staticmethod
    def __getCollapseProbabilityIncreasingFactor(zoneName, yearOfConstruction):
        # see table 3.30 ("Erhöhungsfaktor der Einsturzwahrscheinlichkeit")
        if (zoneName == 'Z1a') or (zoneName == 'Z1b'):
            return Risk.__getEHF(yearOfConstruction, 0)
        if (zoneName == 'Z2'):
            return Risk.__getEHF(yearOfConstruction, 1)
        if (zoneName == 'Z3a') or (zoneName == 'Z3b'):
            return Risk.__getEHF(yearOfConstruction, 2)
        else:
            # When there are bridges outside of
            # earthquake zones we assume zone 2.
            return Risk.__getEHF(yearOfConstruction, 1)

    @staticmethod
    def __getEHF(yearOfConstruction, index):
        values = [[3.0, 10.0, 15],
                  [1.8,  3.0,  4],
                  [1.1,  1.5,  2]]
        if yearOfConstruction < 1970:
            return values[0][index]
        elif yearOfConstruction < 1989:
            return values[1][index]
        elif yearOfConstruction < 2003:
            return values[2][index]
        else:
            return 1

    @staticmethod
    def __getEarthQuakeFactorH4(type):
        # see table 3.31 ("Faktor H 4 basierend auf Wenk, Basöz et al.")
        if (type == 1121) or (type == 1122):
            # 1121: "Brücke mit Rahmentragwerk"
            # 1122: "Brücke mit Sprengwerk"
            # simplified formula (0.25 / 0.6 == 5/12)
            return 5 / 12
        elif (type == 1113):
            # 1113: "Brücke mit Gerberträger"
            #
            # TODO:
            # "Rampen": string search in name?
            #
            # TODO: Schief > 30°
            # There are bridges with strange values (N01Z34: 78031)
            #
            # simplified formula (5 * 0.6 == 3)
            return 3
        else:
            return None
