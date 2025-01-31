import math


class SupportStructureDamageParameters:

    @staticmethod
    def get_damage_costs(replacement_costs, victim_costs,
                         vehicle_lost_costs, downtime_costs):

        damage_costs = 0

        if not math.isnan(replacement_costs):
            damage_costs += replacement_costs
        if not math.isnan(victim_costs):
            damage_costs += victim_costs
        if not math.isnan(vehicle_lost_costs):
            damage_costs += vehicle_lost_costs
        if not math.isnan(downtime_costs):
            damage_costs += downtime_costs

        return damage_costs

    @staticmethod
    def get_replacement_costs(length, average_height):
        cost_per_square_meter = 2500  # CHF
        return length * average_height * cost_per_square_meter

    @staticmethod
    def get_dampening_factor(consequence_of_collapse):
        if consequence_of_collapse == "Grosser Einfluss auf NS":
            return 1
        elif consequence_of_collapse == "Mittelerer Einfluss auf NS":
            return 0.25
        elif consequence_of_collapse == "Kleiner Einfluss auf NS":
            return 0.1
        elif (consequence_of_collapse == "Kein Einfluss auf NS" or
              consequence_of_collapse == "Winkelstützmauer hmax <= 1.5m"):
            return 0.01
        else:
            return 1

    @staticmethod
    def get_victim_costs(length, dampening_factor):
        value_of_statistical_life = 7_000_000  # in CHF
        number_of_deaths = (
            SupportStructureDamageParameters.get_number_of_deaths(
                length, dampening_factor))
        number_of_injuries = number_of_deaths

        return value_of_statistical_life * (
            number_of_deaths + 0.01 * number_of_injuries)

    @staticmethod
    def get_number_of_deaths(length, dampening_factor):
        # put division at the end for reasons of calculation accuracy
        return 0.3 * 1.74 * dampening_factor * length / 30

    @staticmethod
    def get_vehicle_loss_costs(length, aadt, percentage_of_cars):
        # aadt: average annual daily traffic

        # cost of vehicles
        car_value = 15_000
        truck_value = 250_000

        distance_between_vehicles = 30  # given in meters

        percentage_of_trucks = 1 - percentage_of_cars

        return length / distance_between_vehicles * (
            percentage_of_cars * car_value +
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
