#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 23 22:02:30 2018
@author: adam
"""

from functools import reduce
from operator import add
from logbook import Logger

from PySide6.QtCore import Slot, QSettings


class MainMixin(object):

    name = "Main"
    org = "Unknown"

    components = {}
    docks = {}
    preferences = None

    def __init__(self):

        self.settings = QSettings(self.org, self.name)

    def registerComponent(self, name, component, dock=None):

        self.components[name] = component

        if dock:
            self.docks[name] = dock(component)

    def saveWindow(self):

        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

    def restoreWindow(self):

        if self.settings.value("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.value("windowState"):
            self.restoreState(self.settings.value("windowState"))

    def savePreferences(self):

        settings = self.settings

        if self.preferences:
            settings.setValue("General", self.preferences.saveState())

        for comp in (c for c in self.components.values() if c.preferences):
            settings.setValue(comp.name, comp.preferences.saveState())

    def restorePreferences(self):

        settings = self.settings

        if self.preferences and settings.value("General"):
            self.preferences.restoreState(
                settings.value("General"), removeChildren=False
            )
        general_state = settings.value("General")
        # if self.preferences and general_state is not None:
        
        # if self.preferences and isinstance(general_state, (bytes, bytearray)):
        #     self.preferences.restoreState(general_state, removeChildren=False)

        for comp in (c for c in self.components.values() if c.preferences):
            comp_state = settings.value(comp.name)
            #if comp_state is not None:
            if isinstance(comp_state, (bytes, bytearray)):
                comp.preferences.restoreState(comp_state, removeChildren=False)

    def saveComponentState(self):

        settings = self.settings

        for comp in self.components.values():
            comp.saveComponentState(settings)

    def restoreComponentState(self):

        settings = self.settings

        for comp in self.components.values():
            #comp.restoreComponentState(settings)
            if hasattr(comp, "restoreComponentState"):
                comp.restoreComponentState(settings)


class ComponentMixin(object):

    name = "Component"
    preferences = None

    _actions = {}

    def __init__(self):

        if self.preferences:
            self.preferences.sigTreeStateChanged.connect(self.updatePreferences)

        self._logger = Logger(self.name)

    def menuActions(self):

        return self._actions

    def toolbarActions(self):

        if len(self._actions) > 0:
            return reduce(add, [a for a in self._actions.values()])
        else:
            return []

    @Slot(object, object)
    def updatePreferences(self, *args):
        pass

    def saveComponentState(self, settings):
        pass

    def restoreComponentState(self, settings):
        pass
