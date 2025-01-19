import gettext
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import numpy as np
import pandas as pd
import plotly.express as px
from functools import cache
from IPython.display import display, HTML
from ProgressBar import ProgressBar


@cache
def cached_gettext(message):
    # dito
    return gettext.gettext(message)


_ = cached_gettext


class Plots:

    def __init__(self):
        self.acpScatterColumns = [
            _('Age'), _('Condition class'), _('Probability of collapse')]
        self.ageConditionPocScatter = pd.DataFrame(
            columns=self.acpScatterColumns)

        self.cpScatterColumns = [
            _('Condition class'), _('Probability of collapse')]
        self.conditionPocScatter = pd.DataFrame(
            columns=self.cpScatterColumns)

        self.spScatterColumns = [_('Span'), _('Probability of collapse')]
        self.spanPocScatter = pd.DataFrame(columns=self.spScatterColumns)

        self.maintenancePocScatterColumns = [
            _('Last maintenance acceptance date'),
            _('Probability of collapse')]
        self.maintenancePocScatter = pd.DataFrame(
            columns=self.maintenancePocScatterColumns)

        self.materialPocBoxColumns = [
            _('Building material'), _('Probability of collapse')]
        self.materialPocBox = pd.DataFrame(columns=self.materialPocBoxColumns)

        self.yearMaterialStackColumns = [
            _('Year of construction'), _('Building material')]
        self.yearMaterialStack = pd.DataFrame(
            columns=self.yearMaterialStackColumns)

        self.aadtRiskScatterColumns = [
            _('Average annual daily traffic'), _('Risk')]
        self.aadtRiskScatter = pd.DataFrame(
            columns=self.aadtRiskScatterColumns)

        self.spanRiskScatterColumns = [_('Span'), _('Risk')]
        self.spanRiskScatter = pd.DataFrame(
            columns=self.spanRiskScatterColumns)

        self.ageRiskScatterColumns = [_('Age'), _('Risk')]
        self.ageRiskScatter = pd.DataFrame(
            columns=self.ageRiskScatterColumns)

        self.maintenanceRiskScatterColumns = [
            _('Last maintenance acceptance date'), _('Risk')]
        self.maintenanceRiskScatter = pd.DataFrame(
            columns=self.maintenanceRiskScatterColumns)

        self.materialRiskBoxColumns = [_('Building material'), _('Risk')]
        self.materialRiskBox = pd.DataFrame(
            columns=self.materialRiskBoxColumns)

        self.poc_cost_risk_columns = [
            _('Probability of collapse'), _('Damage costs'), _('Risk')]
        self.poc_cost_risk_dataframe = pd.DataFrame(
            columns=self.poc_cost_risk_columns)

        self.standardized_damage_columns = [
            _('Vehicle lost costs'), _('Replacement costs'),
            _('Downtime costs'), _('Victim costs')]
        self.standardized_damage_dataframe = pd.DataFrame(
            columns=self.standardized_damage_columns)

    def fillData(self, index, conditionClass, probabilityOfCollapse, age, span,
                 buildingMaterialString, yearOfConstruction,
                 maintenanceAcceptanceDate, aadt, risk, damage_costs,
                 vehicle_lost_costs, replacement_costs, downtime_costs,
                 victim_costs):

        if conditionClass is not None and conditionClass < 9:

            newDataFrame = pd.DataFrame(
                [[conditionClass, probabilityOfCollapse]],
                columns=self.cpScatterColumns)

            self.conditionPocScatter = self.__concat_dataframe(
                self.conditionPocScatter, newDataFrame)

            if age is not None:
                newDataFrame = pd.DataFrame(
                    [[age, conditionClass, probabilityOfCollapse]],
                    columns=self.acpScatterColumns)
                self.ageConditionPocScatter = self.__concat_dataframe(
                    self.ageConditionPocScatter, newDataFrame)

        if span is not None:
            newDataFrame = pd.DataFrame([[span, probabilityOfCollapse]],
                                        columns=self.spScatterColumns)
            self.spanPocScatter = self.__concat_dataframe(
                self.spanPocScatter, newDataFrame)

            newDataFrame = pd.DataFrame([[span, risk]],
                                        columns=self.spanRiskScatterColumns)
            self.spanRiskScatter = self.__concat_dataframe(
                self.spanRiskScatter, newDataFrame)

        if maintenanceAcceptanceDate is not None:
            newDataFrame = pd.DataFrame(
                [[maintenanceAcceptanceDate, probabilityOfCollapse]],
                columns=self.maintenancePocScatterColumns)
            self.maintenancePocScatter = self.__concat_dataframe(
                self.maintenancePocScatter, newDataFrame)

            newDataFrame = pd.DataFrame(
                [[maintenanceAcceptanceDate, risk]],
                columns=self.maintenanceRiskScatterColumns)
            self.maintenanceRiskScatter = self.__concat_dataframe(
                self.maintenanceRiskScatter, newDataFrame)

        newDataFrame = pd.DataFrame(
            [[buildingMaterialString, probabilityOfCollapse]],
            columns=self.materialPocBoxColumns)
        self.materialPocBox = self.__concat_dataframe(
            self.materialPocBox, newDataFrame)

        if yearOfConstruction != -1:
            newDataFrame = pd.DataFrame(
                [[yearOfConstruction, buildingMaterialString]],
                columns=self.yearMaterialStackColumns)
            self.yearMaterialStack = self.__concat_dataframe(
                self.yearMaterialStack, newDataFrame)

        newDataFrame = pd.DataFrame([[aadt, risk]],
                                    columns=self.aadtRiskScatterColumns)
        self.aadtRiskScatter = self.__concat_dataframe(
            self.aadtRiskScatter, newDataFrame)

        newDataFrame = pd.DataFrame([[age, risk]],
                                    columns=self.ageRiskScatterColumns)
        self.ageRiskScatter = self.__concat_dataframe(
            self.ageRiskScatter, newDataFrame)

        newDataFrame = pd.DataFrame(
            [[buildingMaterialString, risk]],
            columns=self.materialRiskBoxColumns)
        self.materialRiskBox = self.__concat_dataframe(
            self.materialRiskBox, newDataFrame)

        newDataFrame = pd.DataFrame(
            [[vehicle_lost_costs, replacement_costs, downtime_costs,
              victim_costs]], columns=self.standardized_damage_columns)
        self.standardized_damage_dataframe = self.__concat_dataframe(
            self.standardized_damage_dataframe, newDataFrame)

        newDataFrame = pd.DataFrame(
            [[probabilityOfCollapse, damage_costs, risk]],
            columns=self.poc_cost_risk_columns)
        self.poc_cost_risk_dataframe = self.__concat_dataframe(
            self.poc_cost_risk_dataframe, newDataFrame)

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
            self.ageConditionPocScatter[self.acpScatterColumns[0]],
            self.ageConditionPocScatter[self.acpScatterColumns[1]],
            s=self.ageConditionPocScatter[self.acpScatterColumns[2]] * resize)
        ax.set_title(self.acpScatterColumns[2])
        self.__show_scatter_plot(
            ax, self.acpScatterColumns[0], self.acpScatterColumns[1], fig)

        # age vs. probability of collapse
        self.__update_progress_bar()
        self.__add_simple_scatter(
            self.ageConditionPocScatter,
            self.acpScatterColumns[0], self.acpScatterColumns[2])

        # condition class vs. probability of collapse
        self.__update_progress_bar()
        fig, ax = plt.subplots()
        plt.xticks([1, 2, 3, 4])
        ax.scatter(
            self.conditionPocScatter[self.cpScatterColumns[0]],
            self.conditionPocScatter[self.cpScatterColumns[1]])
        self.__show_scatter_plot(
            ax, self.cpScatterColumns[0], self.cpScatterColumns[1], fig)

        # span vs. probability of collapse
        self.__update_progress_bar()
        self.__add_simple_scatter(
            self.spanPocScatter,
            self.spScatterColumns[0], self.spScatterColumns[1])

        # maintenance acceptance date vs. probability of collapse
        self.__update_progress_bar()
        self.__add_date_scatter(self.maintenancePocScatter,
                                self.maintenancePocScatterColumns[0],
                                self.maintenancePocScatterColumns[1])

        # box plot of materials vs. probability of collapse
        self.__update_progress_bar()
        self.__add_material_box_plot(
            self.materialPocBox, self.materialPocBoxColumns)

        # stack plot year of construction vs. building material
        self.__update_progress_bar()
        years = pd.unique(self.yearMaterialStack[
            self.yearMaterialStackColumns[0]])
        years.sort()
        materials = pd.unique(self.yearMaterialStack[
            self.yearMaterialStackColumns[1]])
        materials.sort()
        stackX = []
        for year in years:
            stackX.append(year)
        stackY = []
        for material in materials:
            yearData = []
            for year in years:
                tmp = self.yearMaterialStack[self.yearMaterialStack[
                    self.yearMaterialStackColumns[0]] == year]
                count = (tmp[self.yearMaterialStackColumns[1]].
                         value_counts().get(material, 0))
                yearData.append(count)
            stackY.append(yearData)
        cm = 1/2.54
        fig, ax = plt.subplots(figsize=(40*cm, 20*cm))
        ax.stackplot(stackX, stackY, labels=materials)
        loc = plticker.MultipleLocator(base=20)
        ax.xaxis.set_major_locator(loc)
        ax.set_xlabel(self.yearMaterialStackColumns[0])
        ax.set_ylabel(self.yearMaterialStackColumns[1])
        ax.legend(loc='upper left')
        plt.show()

        # aadt vs. risk
        self.__update_progress_bar()
        self.__add_simple_scatter(
            self.aadtRiskScatter,
            self.aadtRiskScatterColumns[0], self.aadtRiskScatterColumns[1])

        # span vs. risk
        self.__update_progress_bar()
        self.__add_simple_scatter(
            self.spanRiskScatter,
            self.spanRiskScatterColumns[0], self.spanRiskScatterColumns[1])

        # age vs. risk
        self.__update_progress_bar()
        self.__add_simple_scatter(
            self.ageRiskScatter,
            self.ageRiskScatterColumns[0], self.ageRiskScatterColumns[1])

        # maintenance acceptance date vs. risk
        self.__update_progress_bar()
        self.__add_date_scatter(self.maintenanceRiskScatter,
                                self.maintenanceRiskScatterColumns[0],
                                self.maintenanceRiskScatterColumns[1])

        # box plot of materials vs. risk
        self.__update_progress_bar()
        self.__add_material_box_plot(
            self.materialRiskBox, self.materialRiskBoxColumns)

        # standardized damage
        self.__update_progress_bar()
        df = self.standardized_damage_dataframe
        replacement_sum = df[_('Replacement costs')].sum()
        standardized_damages = [
            df[_('Vehicle lost costs')].sum() / replacement_sum,
            1,  # this is always "1" (Replacement costs / Replacement costs)
            df[_('Downtime costs')].sum() / replacement_sum,
            df[_('Victim costs')].sum() / replacement_sum]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(self.standardized_damage_columns,
               standardized_damages, width=0.5)
        ax.set_ylabel(_('Ratio of damage costs to replacement costs'))
        plt.show()

        # 3D plot:
        #   - x: probability of collapse
        #   - y: damage costs
        #   - z: risk
        self.__update_progress_bar()
        df = self.poc_cost_risk_dataframe
        columns = self.poc_cost_risk_columns
        fig = px.scatter_3d(
            df,
            x=columns[0],
            y=columns[1],
            z=columns[2],
            height=1000,
            size=[1] * len(df),
            size_max=10,
            color=columns[2],
            color_continuous_scale='Viridis')
        html_str = fig.to_html()
        display(HTML(html_str))

        # 3D plot with logarithmic x & y axes
        self.__update_progress_bar()
        column_log_0 = 'ln(' + columns[0] + ')'
        column_log_1 = 'ln(' + columns[1] + ')'
        df[column_log_0] = np.log(df[columns[0]])
        df[column_log_1] = np.log(df[columns[1]])
        fig = px.scatter_3d(
            df,
            x=column_log_0,
            y=column_log_1,
            z=columns[2],
            height=1000,
            size=[1] * len(df),
            size_max=10,
            color=columns[2],
            color_continuous_scale='Viridis')
        html_str = fig.to_html()
        display(HTML(html_str))

        # 3D plot with all logarithmic axes
        self.__update_progress_bar()
        column_log_2 = 'ln(' + columns[2] + ')'
        df[column_log_2] = np.log(df[columns[2]])
        fig = px.scatter_3d(
            df,
            x=column_log_0,
            y=column_log_1,
            z=column_log_2,
            height=1000,
            size=[1] * len(df),
            size_max=10,
            color=column_log_2,
            color_continuous_scale='Viridis')
        html_str = fig.to_html()
        display(HTML(html_str))

    def __concat_dataframe(self, dataFrame, newDataFrame):
        return pd.concat(
            [None if dataFrame.empty else dataFrame, newDataFrame])

    def __add_simple_scatter(self, dataFrame, column1, column2):
        fig, ax = plt.subplots()
        ax.scatter(dataFrame[column1], dataFrame[column2])
        self.__show_scatter_plot(ax, column1, column2, fig)

    def __add_date_scatter(self, dataFrame, column1, column2):
        fig, ax = plt.subplots()
        ax.scatter(dataFrame[column1], dataFrame[column2])
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        self.__show_scatter_plot(ax, column1, column2, fig)

    def __show_scatter_plot(self, ax, column1, column2, fig):
        ax.grid(True)
        fig.tight_layout()
        self.__show_plot(ax, column1, column2)

    def __add_material_box_plot(self, dataFrame, columns):
        materials = pd.unique(dataFrame[columns[0]])
        boxplots = []
        for material in materials:
            matches = dataFrame[columns[0]] == material
            values = dataFrame[matches][columns[1]]
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
