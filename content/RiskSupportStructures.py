from enum import Enum


class RiskSupportStructures:

    # TODO:
    # is "Revetment wall" the correct English term for "Verkleidungsmauer"?
    SupportWall = Enum(
        'SupportWall',
        ['GRAVITY_WALL', 'CANTILEVER_WALL', 'REVETMENT_WALL', 'OTHER_WALL'],
        start=0)

    @staticmethod
    def get_human_error_factor(year_of_construction: int) -> int:
        # factor K_1 ("Faktor für menschliche Fehler")

        # TODO: 30, if year_of_construction is None?
        if (year_of_construction is None) or (year_of_construction < 1900):
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

        # TODO: 300, if condition_class is None?
        if (condition_class is None) or (condition_class == 5):
            return 300
        elif condition_class == 4:
            return 100
        elif condition_class == 3:
            return 10
        else:
            return 1

    @staticmethod
    def get_type_factor(function_text: str, wall_type: str) -> float:
        # factor K_8 ("Typ")

        # TODO: consistency?
        #   table 4.7: "hangseitig"
        #   table 4.9: "Talseitig"

        # TODO: why a None value?
        k8_table = [
            [1.0, 2.0],
            [1.4, 1.0],
            [None, 1.0],
            [2.8, 2.8]]

        y = RiskSupportStructures.__get_support_wall_type(wall_type).value
        x = 0 if RiskSupportStructures.__is_on_slope_side(function_text) else 1

        return k8_table[y][x]

    @staticmethod
    def get_material_factor(wall_type: str) -> int:
        # factor K_9 ("Baustoff")

        # TODO:
        #   - table 4.10 name is probably not
        #     "Einteilung hangseitig bzw. bergseitig"
        #   - table 4.10 first column name is probably not
        #     "Funktion Text" but "Mauertyp Text"
        #   - table 4.11: Bergseitig == Talseitig? (just get rid of it?)
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
    def __is_on_slope_side(function_text: str) -> bool:

        # on the mountain side would be the following list:
        # TODO: typo in document: Schützt vor anderers
        # - 'Schützt vor anderes'
        # - 'Schützt vor Erdrutsch'
        # - 'Schützt vor Lawinen'
        # - 'Stützt anderes'
        # - 'Stützt anderes Infrastrukturobjekt'
        # - 'Stützt Bahnanlage'
        # - 'Stützt Hang'
        # - 'Stützt Natur'
        # - 'Trägt anderes'
        #
        # TODO: Contradiction in document:
        #   - Der Begriff «Stützt» wird immer als hangseitig angewendet.
        #   - There are many functions with "stützt" in the mountain side cell.

        # TODO: 'Schützt anderes' is missing in document
        return (
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
    def __get_support_wall_type(wall_type: str) -> SupportWall:

        # TODO: empty text means "Verkleidungsmauer"?
        if (wall_type is None or wall_type == ''):
            return RiskSupportStructures.SupportWall.REVETMENT_WALL

        if (wall_type == 'Schwergewichtsmauer in Beton' or
                wall_type == 'Schwergewichtsmauer in Mauerwerk' or
                wall_type == 'Schwergewichtsmauern' or
                wall_type == 'Steinkorbmauer' or
                wall_type == 'Trockenmauer' or
                wall_type == 'Mauerwerk'):
            return RiskSupportStructures.SupportWall.GRAVITY_WALL

        if (wall_type == 'Verankerte Winkelstützmauer' or
                wall_type == 'Winkelstützmauer' or
                wall_type == 'Winkelstützmauer mit Mauerwerksverkleidung' or
                wall_type == 'Winkelstützmauer mit Querträger(n)' or
                wall_type == 'Winkelstützmauer mit Wiederlager'):
            return RiskSupportStructures.SupportWall.CANTILEVER_WALL

        return RiskSupportStructures.SupportWall.OTHER_WALL
