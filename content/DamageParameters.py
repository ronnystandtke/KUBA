
class DamageParameters:

    @staticmethod
    def get_damage_costs():
        pass

    @staticmethod
    def get_replacement_costs(length, width):
        return length * width * 5000

    @staticmethod
    def get_victim_costs():
        # vosl = "value of statistical life" in CHF
        vosl = 7_000_000
        number_of_deaths = None
        number_of_injuries = None
        return vosl * (number_of_deaths + 0.01 * number_of_injuries)

    @staticmethod
    def get_number_of_deaths(bridge_type, bridge_function):
        # TODO: depending on cause of collapse?
        #
        # TODO: group of "Plattenbrücke" is identical to
        # group of "Brücke, Viadukt"?
        #
        k_U_values = [[0.001, 0.6],
                      [0.001, 0.2],
                      [0.001, 0.6],
                      [0.001, 0.2],
                      [0.001, 0.3],
                      [0.01, 0.3],
                      [0.001, 0.1]]

        pass
