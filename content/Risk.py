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
            # TODO: what about all other types?
            return None

    @staticmethod
    def getAge(yearOfConstruction):
        # TODO:
        # there are bridges without a year of construction in the dataset!
        if math.isnan(yearOfConstruction):
            return None
        else:
            return CURRENT_YEAR - int(yearOfConstruction)

    @staticmethod
    def getConditionFactor(conditionClass, age):
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

    @staticmethod
    def getSpan(spanText):
        # TODO: there are bridges without span data!
        if math.isnan(spanText):
            return None
        else:
            return float(spanText)

    @staticmethod
    def getStaticCalculationFactor(span):
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

    @staticmethod
    def getBridgeTypeFactor(type):
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
            return 1.6

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

    @staticmethod
    def getMaterialCode(codeText):
        # TODO: there are bridges without material data!
        if codeText == '\\' or math.isnan(codeText):
            return None
        else:
            return float(codeText)

    @staticmethod
    def getMaterialFactor(materialCode):
        # factor K_9 ("Baustoff")

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

    @staticmethod
    def getRobustnessFactor(yearOfConstruction):
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