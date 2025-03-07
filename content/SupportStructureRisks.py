from enum import Enum
import math
from datetime import datetime
CURRENT_YEAR = datetime.now().year


class SupportStructureRisks:

    SupportWall = Enum(
        'SupportWall',
        ['GRAVITY_WALL', 'CANTILEVER_WALL', 'CLADDING_WALL', 'OTHER_WALL'],
        start=0)

    @staticmethod
    def getAge(year_of_construction):

        if (math.isnan(year_of_construction) or
                year_of_construction == -1 or
                year_of_construction == 0):
            return None
        else:
            return CURRENT_YEAR - int(year_of_construction)

    @staticmethod
    def get_human_error_factor(year_of_construction: int) -> int:
        # factor K_1 ("Faktor für menschliche Fehler")

        if ((year_of_construction is None) or
                (year_of_construction < 1900) or
                (year_of_construction == 0) or
                (year_of_construction == -1)):
            return 30
        elif year_of_construction < 1930:
            return 20
        elif year_of_construction < 1970:
            return 10
        elif year_of_construction < 1990:
            return 5
        else:
            return 1

    @staticmethod
    def get_condition_class_factor(condition_class: int) -> int:
        # factor K_4 ("Zustandsklasse")

        if (condition_class is None) or (condition_class == 5):
            return 300
        elif condition_class == 4:
            return 100
        elif condition_class == 3:
            return 10
        else:
            return 1

    @staticmethod
    def is_on_slope_side(function_text: str) -> bool:

        # on the mountain side would be the following list:
        # - 'Schützt vor anderes'
        # - 'Schützt vor Erdrutsch'
        # - 'Schützt vor Lawinen'
        # - 'Stützt anderes'
        # - 'Stützt anderes Infrastrukturobjekt'
        # - 'Stützt Bahnanlage'
        # - 'Stützt Hang'
        # - 'Stützt Natur'
        # - 'Trägt anderes'
        return (
            function_text == 'Schützt anderes' or
            function_text == 'Schützt anderes Infrastrukturobjekt' or
            function_text == 'Schützt Bahnanlage' or
            function_text == 'Schützt Fluss' or
            function_text == 'Schützt Gewässer' or
            function_text == 'Schützt Leitungen' or
            function_text == 'Schützt Natur' or
            function_text == 'Schützt Strasse / Weg' or
            function_text == 'Schützt übrige Infrastruktur' or
            function_text == 'Schützt Verkehrswege' or
            function_text == 'Stützt Strasse / Weg' or
            function_text == 'Stützt übrige Infrastruktur' or
            function_text == 'Stützt Verkehrswege' or
            function_text == 'Trägt Strasse / Weg')

    @staticmethod
    def get_type_factor(is_on_slope_side: bool, wall_type: str) -> float:
        # factor K_8 ("Typ")

        k8_table = [
            [1.0, 2.0],
            [1.4, 1.0],
            [1.0, 1.0],
            [2.8, 2.8]]

        y = SupportStructureRisks.__get_support_wall_type(wall_type).value
        x = 1 if is_on_slope_side else 0

        return k8_table[y][x]

    @staticmethod
    def get_material_factor(wall_type: str) -> int:
        # factor K_9 ("Baustoff")

        if (
                wall_type == 'Schwergewichtsmauer in Beton' or
                wall_type == 'Fertigbetonelement Mauer' or
                wall_type == 'Beton' or
                wall_type == 'Spritzbeton' or
                wall_type == 'Verankerter Spritzbeton'):
            return 1
        else:
            return 2

    @staticmethod
    def get_visible_area(length: float, average_height: float) -> float:
        if length is None or average_height is None:
            return None
        else:
            return length * average_height

    @staticmethod
    def get_visible_area_factor(visible_area: float) -> float:

        # factor K_14 ("sichtbare Fläche")

        if visible_area is None:
            return 2.0

        else:
            if visible_area < 5:
                return 2.0
            elif visible_area <= 20:
                return 1.0
            elif visible_area <= 100:
                return 1.2
            elif visible_area <= 500:
                return 1.4
            elif visible_area <= 1000:
                return 1.8
            else:
                return 2.0

    @staticmethod
    def get_height_factor(max_height: float) -> float:

        # factor K_15 ("Höhe")

        if max_height is None:
            return 2.0
        elif max_height < 2:
            return 1.0
        elif max_height < 5:
            return 1.2
        elif max_height < 10:
            return 1.5
        else:
            return 2.0

    @staticmethod
    def get_precipitation_zone_factor(precipitation_zone: int) -> float:

        # factor K_17 ("Niederschlagszone")

        k17_dict = {
            1: 1.09, 2: 1.09, 3: 1.15, 4: 1, 5: 1.12, 6: 1.5, 7: 1.12, 8: 1.03}
        return k17_dict[precipitation_zone]

    @staticmethod
    def __get_support_wall_type(wall_type: str) -> SupportWall:

        if (wall_type == 'Schwergewichtsmauer in Beton' or
                wall_type == 'Schwergewichtsmauer in Mauerwerk' or
                wall_type == 'Schwergewichtsmauern' or
                wall_type == 'Steinkorbmauer' or
                wall_type == 'Trockenmauer' or
                wall_type == 'Mauerwerk'):
            return SupportStructureRisks.SupportWall.GRAVITY_WALL

        if (wall_type is None or wall_type == '' or
                wall_type == 'Verankerte Winkelstützmauer' or
                wall_type == 'Winkelstützmauer' or
                wall_type == 'Winkelstützmauer mit Mauerwerksverkleidung' or
                wall_type == 'Winkelstützmauer mit Querträger(n)' or
                wall_type == 'Winkelstützmauer mit Wiederlager'):
            return SupportStructureRisks.SupportWall.CANTILEVER_WALL

        return SupportStructureRisks.SupportWall.OTHER_WALL
