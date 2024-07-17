import gettext
import Labels
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import pandas as pd
from babel.dates import format_date
from datetime import datetime
from functools import cache


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

    def fillData(self, index, conditionClass, probabilityOfCollapse,
                 age, span, buildingMaterialString, yearOfConstruction, kuba):

        if conditionClass is not None and conditionClass < 9:

            newDataFrame = pd.DataFrame(
                [[conditionClass, probabilityOfCollapse]],
                columns=self.cpScatterColumns)
            self.conditionPocScatter = pd.concat(
                [self.conditionPocScatter, newDataFrame])

            if age is not None:
                newDataFrame = pd.DataFrame(
                    [[age, conditionClass, probabilityOfCollapse]],
                    columns=self.acpScatterColumns)
                self.ageConditionPocScatter = pd.concat(
                    [self.ageConditionPocScatter, newDataFrame])

        if span is not None:
            newDataFrame = pd.DataFrame(
                [[span, probabilityOfCollapse]],
                columns=self.spScatterColumns)
            self.spanPocScatter = pd.concat(
                [self.spanPocScatter, newDataFrame])

        # TODO: There are bridges where the maintenance acceptance
        # date is 01.01.1900 and the kind of maintenance is
        # "Abbruch", e.g. S5731, BRÜCKE Gabi 4 N9S and
        # S5191, BRÜCKE Eggamatt N9S.
        # There are even obvious errors like the support wall
        # 52.303.13, SM Oben Nordportal Tunnel Ried FBNO where the
        # maintenance acceptance date is 31.12.3013.
        # How do we deal with these dates?
        bridgeNumber = kuba.bridges[Labels.NUMBER_LABEL][index]
        maintenance = kuba.dfMaintenance[
            kuba.dfMaintenance[Labels.NUMBER_LABEL] == bridgeNumber]
        maintenanceAcceptanceDate = None
        kuba.maintenanceAcceptanceDateString = _('unknown')
        if not maintenance.empty:
            maintenanceAcceptanceDate = maintenance[
                Labels.MAINTENANCE_ACCEPTANCE_DATE_LABEL].iloc[0]
            if isinstance(maintenanceAcceptanceDate, datetime):
                newDataFrame = pd.DataFrame(
                    [[maintenanceAcceptanceDate, probabilityOfCollapse]],
                    columns=self.maintenancePocScatterColumns)
                self.maintenancePocScatter = pd.concat(
                    [self.maintenancePocScatter, newDataFrame])
                kuba.maintenanceAcceptanceDateString = format_date(
                    maintenanceAcceptanceDate)

        newDataFrame = pd.DataFrame(
            [[buildingMaterialString, probabilityOfCollapse]],
            columns=self.materialPocBoxColumns)
        self.materialPocBox = pd.concat(
            [self.materialPocBox, newDataFrame])

        if yearOfConstruction != -1:
            newDataFrame = pd.DataFrame(
                [[yearOfConstruction, buildingMaterialString]],
                columns=self.yearMaterialStackColumns)
            self.yearMaterialStack = pd.concat(
                [self.yearMaterialStack, newDataFrame])

    def showPlots(self):
        # age (x) vs. condition class (y) and probability of collapse (size)
        fig, ax = plt.subplots()
        plt.yticks([1, 2, 3, 4])
        # the circles became quite large,
        # therefore we divide the values by this factor
        resize = 7
        ax.scatter(
            self.ageConditionPocScatter[self.acpScatterColumns[0]],
            self.ageConditionPocScatter[self.acpScatterColumns[1]],
            s=self.ageConditionPocScatter[self.acpScatterColumns[2]] / resize)
        ax.set_xlabel(self.acpScatterColumns[0])
        ax.set_ylabel(self.acpScatterColumns[1])
        ax.set_title(self.acpScatterColumns[2])
        ax.grid(True)
        fig.tight_layout()
        plt.show()

        # age vs. probability of collapse
        fig, ax = plt.subplots()
        ax.scatter(
            self.ageConditionPocScatter[self.acpScatterColumns[0]],
            self.ageConditionPocScatter[self.acpScatterColumns[2]])
        ax.set_xlabel(self.acpScatterColumns[0])
        ax.set_ylabel(self.acpScatterColumns[2])
        ax.grid(True)
        fig.tight_layout()
        plt.show()

        # condition class vs. probability of collapse
        fig, ax = plt.subplots()
        plt.xticks([1, 2, 3, 4])
        ax.scatter(
            self.conditionPocScatter[self.cpScatterColumns[0]],
            self.conditionPocScatter[self.cpScatterColumns[1]])
        ax.set_xlabel(self.cpScatterColumns[0])
        ax.set_ylabel(self.cpScatterColumns[1])
        ax.grid(True)
        fig.tight_layout()
        plt.show()

        # span vs. probability of collapse
        fig, ax = plt.subplots()
        ax.scatter(
            self.spanPocScatter[self.spScatterColumns[0]],
            self.spanPocScatter[self.spScatterColumns[1]])
        ax.set_xlabel(self.spScatterColumns[0])
        ax.set_ylabel(self.spScatterColumns[1])
        ax.grid(True)
        fig.tight_layout()
        plt.show()

        # maintenance acceptance date vs. probability of collapse
        fig, ax = plt.subplots()
        ax.scatter(
            self.maintenancePocScatter[self.maintenancePocScatterColumns[0]],
            self.maintenancePocScatter[self.maintenancePocScatterColumns[1]])
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        ax.set_xlabel(self.maintenancePocScatterColumns[0])
        ax.set_ylabel(self.maintenancePocScatterColumns[1])
        ax.grid(True)
        fig.tight_layout()
        plt.show()

        # box plot of materials vs. probability of collapse
        materials = pd.unique(self.materialPocBox[
            self.materialPocBoxColumns[0]])
        boxplots = []
        for material in materials:
            matches = self.materialPocBox[
                self.materialPocBoxColumns[0]] == material
            pocs = self.materialPocBox[matches][self.materialPocBoxColumns[1]]
            boxplots.append(pocs)
        fig, ax = plt.subplots()
        ax.set_xlabel(self.materialPocBoxColumns[0])
        ax.set_ylabel(self.materialPocBoxColumns[1])
        ax.boxplot(boxplots, labels=materials)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        plt.show()

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
