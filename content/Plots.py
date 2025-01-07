import gettext
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import pandas as pd
from functools import cache
from IPython.display import display, HTML


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
        self.aadtRiskScatter = pd.DataFrame(columns=self.aadtRiskScatterColumns)

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

    def fillData(self, index, conditionClass, probabilityOfCollapse, age, span,
                 buildingMaterialString, yearOfConstruction,
                 maintenanceAcceptanceDate, aadt, risk):

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

    def display(self):

        display(HTML("<hr><div style='text-align: center;'><h1>" +
                     _("Diagrams") + "</h1></div>"))

        # age (x) vs. condition class (y) and probability of collapse (size)
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
        self.__add_simple_scatter(
            self.ageConditionPocScatter,
            self.acpScatterColumns[0], self.acpScatterColumns[2])

        # condition class vs. probability of collapse
        fig, ax = plt.subplots()
        plt.xticks([1, 2, 3, 4])
        ax.scatter(
            self.conditionPocScatter[self.cpScatterColumns[0]],
            self.conditionPocScatter[self.cpScatterColumns[1]])
        self.__show_scatter_plot(
            ax, self.cpScatterColumns[0], self.cpScatterColumns[1], fig)

        # span vs. probability of collapse
        self.__add_simple_scatter(
            self.spanPocScatter,
            self.spScatterColumns[0], self.spScatterColumns[1])

        # maintenance acceptance date vs. probability of collapse
        self.__add_date_scatter(self.maintenancePocScatter,
                                self.maintenancePocScatterColumns[0],
                                self.maintenancePocScatterColumns[1])

        # box plot of materials vs. probability of collapse
        self.__add_material_box_plot(
            self.materialPocBox, self.materialPocBoxColumns)

        # stack plot year of construction vs. building material
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
        self.__add_simple_scatter(
            self.aadtRiskScatter,
            self.aadtRiskScatterColumns[0], self.aadtRiskScatterColumns[1])

        # span vs. risk
        self.__add_simple_scatter(
            self.spanRiskScatter,
            self.spanRiskScatterColumns[0], self.spanRiskScatterColumns[1])

        # age vs. risk
        self.__add_simple_scatter(
            self.ageRiskScatter,
            self.ageRiskScatterColumns[0], self.ageRiskScatterColumns[1])

        # maintenance acceptance date vs. risk
        self.__add_date_scatter(self.maintenanceRiskScatter,
                                self.maintenanceRiskScatterColumns[0],
                                self.maintenanceRiskScatterColumns[1])

        # box plot of materials vs. risk
        self.__add_material_box_plot(
            self.materialRiskBox, self.materialRiskBoxColumns)

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

        # TODO:
        #    - erst einmal aussen vor lassen: Normierte Schadensanteile (normiert auf den Wiederbeschaffungswert der Brücke, Beispiel anbei)
        #    - Bild: 3D: x-Achse Versagenswahrscheinlichkeit, y-Achse Schadensumfang, z-Achse: Risiko oder Zustandsklasse, Farbcodierung: Risiko oder Zustandsklasse
        #    - Bild: 3D: x-Achse Versagenswahrscheinlichkeit (Spannweite), y-Achse Schadensumfang (Spannweite), z-Achse: Risiko (Spannweite)
