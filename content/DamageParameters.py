import math


class DamageParameters:

    @staticmethod
    def get_replacement_costs(length, width):

        cost_per_square_meter = 5500  # CHF

        if ((length is None) or (length == 0) or (math.isnan(length))):
            # if the length is unknown, assume 200 m
            length = 200

        if ((width is None) or (width == 0) or (math.isnan(width))):
            # if the width is unknown, assume 30 m
            width = 30

        # There are bridges where only the length is unknown, e.g.
        # ZH_230-007: UEF Zürcherstrasse Süd, Töss
        # We still use the given width here!

        # There are bridges with nonsensical data:
        # ZH_242-023: UEF Rampe Einfahrt Wettswil, Birmensdorf:
        #     width of 1045 m!
        # Decision: keep values as is, ASTRA needs to fix the data themselves.

        return length * width * cost_per_square_meter

    @staticmethod
    def get_victim_costs(bridge_type, bridge_function):
        # vosl = "value of statistical life" in CHF
        vosl = 7_000_000
        number_of_deaths = DamageParameters.get_number_of_deaths(
            bridge_type, bridge_function)
        number_of_injuries = number_of_deaths
        return vosl * (number_of_deaths + 0.01 * number_of_injuries)

    @staticmethod
    def get_number_of_deaths(bridge_type, bridge_function):

        if ((bridge_type == "Plattenbrücke") or
                (bridge_type == "Brücke mit Einfeldträger") or
                (bridge_type == "Brücke mit Durchlaufträger") or
                (bridge_type == "Brücke mit Gerberträger") or
                (bridge_type == "Brücke auf Wanne") or
                (bridge_type == "Brückenanlage") or
                (bridge_type == "Spezielle Brücke") or
                (bridge_type == "Brücke mit Rahmentragwerk") or
                (bridge_type == "Brücke mit Sprengwerk")):

            kuGroup = 1

        elif ((bridge_type == "Brücke, Viadukt") or
              (bridge_type == "Gewölbekonstruktion")):

            kuGroup = 2

        elif ((bridge_type == "Brücke mit Bogentragwerk") or
              (bridge_type ==
               "Brücke mit versteiftem Stabbogen/Langerscher Balken") or
              (bridge_type == "Rahmen-, Bogenbrücken")):

            kuGroup = 3

        else:
            kuGroup = 4

        # There are other functions ("stützt", "trägt", "unterquert", ...)
        # but they are sorted into the group of "über Wasser und sonstige".
        # There are only two cases:
        # - "Überquert Strasse / Weg" or "Überquert Verkehrsweg"
        # - everything else

        if ((bridge_function == "Überquert Strasse / Weg") or
                (bridge_function == "Überquert Verkehrsweg")):
            kuFunction = 2
        else:
            kuFunction = 1

        # some constant values
        m = 15
        sk = 1

        # group of "Plattenbrücke" is identical to group of "Brücke, Viadukt"
        if ((kuGroup == 1) or (kuGroup == 2)):
            if (kuFunction == 1):
                number_of_deaths = (
                    0.6 * 0.001 * m * sk +
                    0.3 * 0.01 * m * sk +
                    0.1 * 0.8 * m * sk)
            else:
                number_of_deaths = (
                    0.2 * 0.001 * m * sk +
                    0.6 * 0.01 * m * sk +
                    0.2 * 0.8 * m * sk)

        elif (kuGroup == 3):
            # "Stürme" instead of "Kollision, Erdbeben" is on purpose
            # it's fine this way...
            if (kuFunction == 1):
                number_of_deaths = (
                    0.3 * 0.001 * m * sk +
                    0.4 * 0.8 * m * sk +
                    0.3 * 0.001 * m * sk)
            else:
                number_of_deaths = (
                    0.3 * 0.01 * m * sk +
                    0.4 * 0.8 * m * sk +
                    0.3 * 0.001 * m * sk)
        else:
            number_of_deaths = (
                0.1 * 0.001 * m * sk +
                0.3 * 0.01 * m * sk +
                0.3 * 0.001 * m * sk +
                0.3 * 0.8 * m * sk)

        return number_of_deaths

    @staticmethod
    def get_vehicle_loss_costs(length, aadt, percentage_of_cars):
        # aadt: average annual daily traffic

        # cost of vehicles
        car_value = 15_000
        truck_value = 250_000

        percentage_of_trucks = 1 - percentage_of_cars

        return length / 30 * (percentage_of_cars * car_value +
                              percentage_of_trucks * truck_value)

    @staticmethod
    def get_downtime_costs(aadt, percentage_of_cars):
        # aadt: average annual daily traffic

        # cost of vehicles per kilometer (detour)
        car_cost = 1.7
        truck_cost = 1.93

        percentage_of_trucks = 1 - percentage_of_cars

        # road type factor ("S_t" in document)
        # decision: will stay "1" for the time being
        road_type_factor = 1

        # difference of detour to standard tour
        l_diff = 20

        return (aadt * l_diff * road_type_factor * (
            percentage_of_cars * car_cost + percentage_of_trucks * truck_cost))
