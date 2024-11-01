class DamageParameters:

    @staticmethod
    def get_damage_costs(length, width, bridge_type, bridge_function):
        replacement_costs = DamageParameters.get_replacement_costs(
            length, width)
        victim_costs = DamageParameters.get_victim_costs(
            bridge_type, bridge_function)
        # TODO
        vehicle_loss_costs = DamageParameters.get_vehicle_loss_costs()
        downtime_costs = 0
        return (replacement_costs + victim_costs + vehicle_loss_costs +
                downtime_costs)

    @staticmethod
    def get_replacement_costs(length, width):
        return length * width * 5000

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
    def get_vehicle_loss_costs():
        # cost of vehicles
        car_value = 15_000
        truck_value = 250_000
        # TODO: n and m still have to be defined
        # If there is no data, use n=0.9 m=0.1
        n = 1
        m = 1
        return n * car_value + m * truck_value

    @staticmethod
    def get_downtime_costs():
        # TODO: n and m still have to be defined
        n = 1
        m = 1
        # TODO: what is AADT and where is it defined?
        # Average annual daily traffic
        aadt = 1
        # TODO: how is st defined?
        st = 1
        l_diff = 20
        # TODO: there are three definitions of c_pkw on page 61
        #       but only one for c_lkw
        # which definitions do we use in our formula?
        car_cost = 1.7
        truck_cost = 1.93
        return (aadt * n * l_diff * st * car_cost +
                aadt * m * l_diff * st * truck_cost)
