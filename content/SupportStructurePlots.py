import gettext
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import pandas as pd
from functools import cache
from IPython.display import display, HTML
from ProgressBar import ProgressBar


@cache
def cached_gettext(message):
    # dito
    return gettext.gettext(message)


_ = cached_gettext


class SupportStructurePlots:

    def __init__(self):
        self.acp_scatter_columns = [
            _('Age'), _('Condition class'), _('Probability of collapse')]
        self.age_condition_poc_scatter = pd.DataFrame(
            columns=self.acp_scatter_columns)

        self.age_poc_scatter_columns = [_('Age'), _('Probability of collapse')]
        self.age_poc_scatter = pd.DataFrame(
            columns=self.age_poc_scatter_columns)

        self.condition_poc_scatter_columns = [
            _('Condition class'), _('Probability of collapse')]
        self.condition_poc_scatter = pd.DataFrame(
            columns=self.condition_poc_scatter_columns)

        self.height_poc_scatter_columns = [
            _('Height'), _('Probability of collapse')]
        self.height_poc_scatter = pd.DataFrame(
            columns=self.height_poc_scatter_columns)

        self.length_poc_scatter_columns = [
            _('Length'), _('Probability of collapse')]
        self.length_poc_scatter = pd.DataFrame(
            columns=self.length_poc_scatter_columns)

        self.material_poc_box_columns = [
            _('Building material'), _('Probability of collapse')]
        self.material_poc_box = pd.DataFrame(
            columns=self.material_poc_box_columns)

        self.age_material_stack_columns = [
            _('Age'), _('Building material')]
        self.age_material_stack = pd.DataFrame(
            columns=self.age_material_stack_columns)

        self.aadt_risk_scatter_columns = [
            _('Average annual daily traffic'), _('Risk')]
        self.aadt_risk_scatter = pd.DataFrame(
            columns=self.aadt_risk_scatter_columns)

        self.height_risk_scatter_columns = [_('Height'), _('Risk')]
        self.height_risk_scatter = pd.DataFrame(
            columns=self.height_risk_scatter_columns)

        self.length_risk_scatter_columns = [_('Length'), _('Risk')]
        self.length_risk_scatter = pd.DataFrame(
            columns=self.length_risk_scatter_columns)

        self.age_risk_scatter_columns = [_('Age'), _('Risk')]
        self.age_risk_scatter = pd.DataFrame(
            columns=self.age_risk_scatter_columns)

        self.material_risk_box_columns = [_('Building material'), _('Risk')]
        self.material_risk_box = pd.DataFrame(
            columns=self.material_risk_box_columns)

    def fillData(self, index, condition_class, probability_of_collapse, age,
                 length, height, building_material_string, aadt, risk,
                 damage_costs, vehicle_lost_costs, replacement_costs,
                 downtime_costs, victim_costs):

        if condition_class is not None and condition_class < 9:

            new_data_frame = pd.DataFrame(
                [[condition_class, probability_of_collapse]],
                columns=self.condition_poc_scatter_columns)

            self.condition_poc_scatter = self.__concat_dataframe(
                self.condition_poc_scatter, new_data_frame)

            if age is not None:
                new_data_frame = pd.DataFrame(
                    [[age, condition_class, probability_of_collapse]],
                    columns=self.acp_scatter_columns)
                self.age_condition_poc_scatter = self.__concat_dataframe(
                    self.age_condition_poc_scatter, new_data_frame)

                new_data_frame = pd.DataFrame(
                    [[age, building_material_string]],
                    columns=self.age_material_stack_columns)
                self.age_material_stack = self.__concat_dataframe(
                    self.age_material_stack, new_data_frame)

        if length is not None:
            new_data_frame = pd.DataFrame(
                [[length, probability_of_collapse]],
                columns=self.length_poc_scatter_columns)
            self.length_poc_scatter = self.__concat_dataframe(
                self.length_poc_scatter, new_data_frame)

            new_data_frame = pd.DataFrame(
                [[length, risk]],
                columns=self.length_risk_scatter_columns)
            self.length_risk_scatter = self.__concat_dataframe(
                self.length_risk_scatter, new_data_frame)

        if height is not None:
            new_data_frame = pd.DataFrame(
                [[height, probability_of_collapse]],
                columns=self.height_poc_scatter_columns)
            self.height_poc_scatter = self.__concat_dataframe(
                self.height_poc_scatter, new_data_frame)

            new_data_frame = pd.DataFrame(
                [[height, risk]],
                columns=self.height_risk_scatter_columns)
            self.height_risk_scatter = self.__concat_dataframe(
                self.height_risk_scatter, new_data_frame)

        new_data_frame = pd.DataFrame(
            [[building_material_string, probability_of_collapse]],
            columns=self.material_poc_box_columns)
        self.material_poc_box = self.__concat_dataframe(
            self.material_poc_box, new_data_frame)

        new_data_frame = pd.DataFrame([[aadt, risk]],
                                      columns=self.aadt_risk_scatter_columns)
        self.aadt_risk_scatter = self.__concat_dataframe(
            self.aadt_risk_scatter, new_data_frame)

        new_data_frame = pd.DataFrame([[age, risk]],
                                      columns=self.age_risk_scatter_columns)
        self.age_risk_scatter = self.__concat_dataframe(
            self.age_risk_scatter, new_data_frame)

        new_data_frame = pd.DataFrame(
            [[building_material_string, risk]],
            columns=self.material_risk_box_columns)
        self.material_risk_box = self.__concat_dataframe(
            self.material_risk_box, new_data_frame)

    def display(self, progress_bar: ProgressBar) -> None:

        self.progress_bar = progress_bar

        display(HTML("<hr><div style='text-align: center;'><h1>" +
                     _("Diagrams") + "</h1></div>"))

        self.plot_number = 0
        self.plot_counter = 16
        self.progress_bar.reset(self.plot_counter)

        # age (x) vs. condition class (y) and probability of collapse (size)
        self.__update_progress_bar()
        fig, ax = plt.subplots()
        plt.yticks([1, 2, 3, 4])
        # the circles became quite small,
        # therefore we multiply the values by this factor
        resize = 750
        ax.scatter(
            self.age_condition_poc_scatter[self.acp_scatter_columns[0]],
            self.age_condition_poc_scatter[self.acp_scatter_columns[1]],
            s=self.age_condition_poc_scatter[self.acp_scatter_columns[2]]
            * resize)
        ax.set_title(self.acp_scatter_columns[2])
        self.__show_scatter_plot(
            ax, self.acp_scatter_columns[0], self.acp_scatter_columns[1], fig)

        # age vs. probability of collapse
        self.__update_progress_bar()
        self.__add_simple_scatter(
            self.age_condition_poc_scatter,
            self.acp_scatter_columns[0], self.acp_scatter_columns[2])

        # condition class vs. probability of collapse
        self.__update_progress_bar()
        fig, ax = plt.subplots()
        plt.xticks([1, 2, 3, 4])
        ax.scatter(
            self.condition_poc_scatter[self.condition_poc_scatter_columns[0]],
            self.condition_poc_scatter[self.condition_poc_scatter_columns[1]])
        self.__show_scatter_plot(
            ax, self.condition_poc_scatter_columns[0],
            self.condition_poc_scatter_columns[1], fig)

        # height vs. probability of collapse
        self.__update_progress_bar()
        self.__add_simple_scatter(self.height_poc_scatter,
                                  self.height_poc_scatter_columns[0],
                                  self.height_poc_scatter_columns[1])

        # length vs. probability of collapse
        self.__update_progress_bar()
        self.__add_simple_scatter(self.length_poc_scatter,
                                  self.length_poc_scatter_columns[0],
                                  self.length_poc_scatter_columns[1])

        # box plot of materials vs. probability of collapse
        self.__update_progress_bar()
        self.__add_material_box_plot(
            self.material_poc_box, self.material_poc_box_columns)

        # stack plot age vs. building material
        self.__update_progress_bar()
        ages = pd.unique(self.age_material_stack[
            self.age_material_stack_columns[0]])
        ages.sort()
        materials = pd.unique(self.age_material_stack[
            self.age_material_stack_columns[1]])
        materials.sort()
        stackX = []
        for year in ages:
            stackX.append(year)
        stackY = []
        for material in materials:
            yearData = []
            for year in ages:
                tmp = self.age_material_stack[self.age_material_stack[
                    self.age_material_stack_columns[0]] == year]
                count = (tmp[self.age_material_stack_columns[1]].
                         value_counts().get(material, 0))
                yearData.append(count)
            stackY.append(yearData)
        cm = 1/2.54
        fig, ax = plt.subplots(figsize=(40*cm, 20*cm))
        ax.stackplot(stackX, stackY, labels=materials)
        loc = plticker.MultipleLocator(base=20)
        ax.xaxis.set_major_locator(loc)
        ax.set_xlabel(self.age_material_stack_columns[0])
        ax.set_ylabel(self.age_material_stack_columns[1])
        ax.legend(loc='upper left')
        plt.show()

        # aadt vs. risk
        self.__update_progress_bar()
        self.__add_simple_scatter(self.aadt_risk_scatter,
                                  self.aadt_risk_scatter_columns[0],
                                  self.aadt_risk_scatter_columns[1])

        # height vs. risk
        self.__update_progress_bar()
        self.__add_simple_scatter(self.height_risk_scatter,
                                  self.height_risk_scatter_columns[0],
                                  self.height_risk_scatter_columns[1])

        # length vs. risk
        self.__update_progress_bar()
        self.__add_simple_scatter(self.length_risk_scatter,
                                  self.length_risk_scatter_columns[0],
                                  self.length_risk_scatter_columns[1])

        # age vs. risk
        self.__update_progress_bar()
        self.__add_simple_scatter(self.age_risk_scatter,
                                  self.age_risk_scatter_columns[0],
                                  self.age_risk_scatter_columns[1])

        # box plot of materials vs. risk
        self.__update_progress_bar()
        self.__add_material_box_plot(self.material_risk_box,
                                     self.material_risk_box_columns)

    def __concat_dataframe(self, data_frame, new_data_frame):
        return pd.concat(
            [None if data_frame.empty else data_frame, new_data_frame])

    def __add_simple_scatter(self, data_frame, column1, column2):
        fig, ax = plt.subplots()
        ax.scatter(data_frame[column1], data_frame[column2])
        self.__show_scatter_plot(ax, column1, column2, fig)

    def __add_date_scatter(self, data_frame, column1, column2):
        fig, ax = plt.subplots()
        ax.scatter(data_frame[column1], data_frame[column2])
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        self.__show_scatter_plot(ax, column1, column2, fig)

    def __show_scatter_plot(self, ax, column1, column2, fig):
        ax.grid(True)
        fig.tight_layout()
        self.__show_plot(ax, column1, column2)

    def __add_material_box_plot(self, data_frame, columns):
        materials = pd.unique(data_frame[columns[0]])
        boxplots = []
        for material in materials:
            matches = data_frame[columns[0]] == material
            values = data_frame[matches][columns[1]]
            boxplots.append(values)
        fig, ax = plt.subplots()
        ax.boxplot(boxplots, labels=materials)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        self.__show_plot(ax, columns[0], columns[1])

    def __show_plot(self, ax, column1, column2):
        ax.set_xlabel(column1)
        ax.set_ylabel(column2)
        plt.show()

    def __update_progress_bar(self):
        description = (_('Loading plot') + ': ' +
                       str(self.plot_number) + '/' + str(self.plot_counter))
        self.progress_bar.update_progress(
            step=self.plot_number, description=description)
        self.plot_number += 1
