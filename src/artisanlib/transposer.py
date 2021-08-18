#!/usr/bin/env python3

# ABOUT
# Artisan Profile Transposer

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2020

import time as libtime
import warnings
import copy
import numpy

from artisanlib.dialogs import ArtisanDialog
from artisanlib.util import stringfromseconds, stringtoseconds

from help import transposer_help

from PyQt5.QtCore import Qt, pyqtSlot, QSettings, QRegExp, QDateTime
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import (QApplication, QHeaderView, QAbstractItemView, QWidget, QLabel, QLineEdit, QComboBox, QDialogButtonBox,
            QTableWidget, QTableWidgetItem, QGroupBox, QLayout, QHBoxLayout, QVBoxLayout)

class profileTransformatorDlg(ArtisanDialog):
    def __init__(self, parent = None, aw = None):
        super(profileTransformatorDlg,self).__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption","Profile Transposer",None))
        
        self.helpdialog = None
        
        self.regexpercent = QRegExp(r"^$|^?[0-9]?[0-9]?(\.[0-9])?$")
        self.regextime = QRegExp(r"^$|^?[0-9]?[0-9]?[0-9]:[0-5][0-9]$")
        self.regextemp = QRegExp(r"^$|^?[0-9]?[0-9]?[0-9]?(\.[0-9])?$")
        
        # original data
        self.org_transMappingMode = self.aw.qmc.transMappingMode
        self.org_timex = self.aw.qmc.timex[:]
        self.org_temp2 = self.aw.qmc.temp2[:]
        self.org_extratimex = copy.deepcopy(self.aw.qmc.extratimex)
        self.org_curFile = self.aw.curFile
        self.org_UUID = self.aw.qmc.roastUUID
        self.org_roastdate = self.aw.qmc.roastdate
        self.org_roastepoch = self.aw.qmc.roastepoch
        self.org_roasttzoffset = self.aw.qmc.roasttzoffset
        self.org_roastbatchnr = self.aw.qmc.roastbatchnr
        self.org_safesaveflag = self.aw.qmc.safesaveflag
        self.org_l_event_flags_dict = self.aw.qmc.l_event_flags_dict
        self.org_l_annotations_dict = self.aw.qmc.l_annotations_dict
        
        self.phasestable = QTableWidget()
        self.timetable = QTableWidget()
        self.temptable = QTableWidget()
        
        # time table widgets initialized by createTimeTable() to a list (target/result) with 4 widgets each
        #   DRY, FCs, SCs, DROP
        # if an event is not set in the profile, None is set instead of a widget
        #
        self.phases_target_widgets_time = None
        self.phases_target_widgets_percent = None
        self.phases_result_widgets = None
        #
        self.time_target_widgets = None
        self.time_result_widgets = None
        
        # profileTimes: list of DRY, FCs, SCs and DROP times in seconds if event is set, otherwise None
        self.profileTimes = self.getProfileTimes()
        # list of DRY, FCs, SCs, and DROP target times in seconds as specified by the user, or None if not set
        self.targetTimes = self.getTargetTimes()
        
        # temp table widgets initialized by createTempTable() to a list (target/result) with 5 widgets each
        #   CHARGE, DRY, FCs, SCs, DROP
        # if an event is not set in the profile, None is set instead of a widget
        self.temp_target_widgets = None
        self.temp_result_widgets = None
        
        # list of CHARGE, DRY, FCs, SCs and DROP BT temperatures
        self.profileTemps = self.getProfileTemps()
        # list of DRY, FCs, SCs, and DROP target temperatures as specified by the user, or None if not set
        self.targetTemps = self.getTargetTemps()
        
        self.createPhasesTable()
        self.createTimeTable()
        self.createTempTable()
        
        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.applyTransformations)
        self.dialogbuttons.rejected.connect(self.restoreState)
        self.applyButton = self.dialogbuttons.addButton(QDialogButtonBox.Apply)
        self.resetButton = self.dialogbuttons.addButton(QDialogButtonBox.Reset)
        self.helpButton = self.dialogbuttons.addButton(QDialogButtonBox.Help)
        self.dialogbuttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        self.dialogbuttons.button(QDialogButtonBox.Reset).clicked.connect(self.restore)
        self.dialogbuttons.button(QDialogButtonBox.Help).clicked.connect(self.openHelp)
        
        #buttons
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.dialogbuttons)
        
        mappingLabel = QLabel(QApplication.translate("Label","Mapping",None))
        self.mappingModeComboBox = QComboBox()
        self.mappingModeComboBox.addItems([QApplication.translate("ComboBox","discrete",None),
                                              QApplication.translate("ComboBox","linear",None),
                                              QApplication.translate("ComboBox","quadratic",None)])
        self.mappingModeComboBox.setCurrentIndex(self.aw.qmc.transMappingMode)
        self.mappingModeComboBox.currentIndexChanged.connect(self.changeMappingMode)
        
        self.temp_formula = QLabel()
        self.temp_formula.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        settingsHLayout = QHBoxLayout()
        settingsHLayout.addStretch()
        settingsHLayout.addWidget(mappingLabel)
        settingsHLayout.addWidget(self.mappingModeComboBox)
        settingsHLayout.addStretch()
        
        phasesHLayout = QHBoxLayout()
        phasesHLayout.addStretch()
        phasesHLayout.addWidget(self.phasestable)
        phasesHLayout.addStretch()
        phasesLayout = QVBoxLayout()
        phasesLayout.addLayout(phasesHLayout)
        
        timeHLayout = QHBoxLayout()
        timeHLayout.addStretch()
        timeHLayout.addWidget(self.timetable)
        timeHLayout.addStretch()
        timeLayout = QVBoxLayout()
        timeLayout.addLayout(timeHLayout)
        timeLayout.addStretch()

        tempHLayout = QHBoxLayout()
        tempHLayout.addWidget(self.temptable)
        tempHLayout.addStretch()
        formulaHLayout = QHBoxLayout()
        formulaHLayout.addStretch()
        formulaHLayout.addWidget(self.temp_formula)
        formulaHLayout.addStretch()
        tempLayout = QVBoxLayout()
        tempLayout.addLayout(tempHLayout)
        tempLayout.addLayout(formulaHLayout)
        tempLayout.addStretch()
        
        phasesGroupLayout = QGroupBox(QApplication.translate("Table","Phases",None))
        phasesGroupLayout.setLayout(phasesLayout)
        timeGroupLayout = QGroupBox(QApplication.translate("Table","Time",None))
        timeGroupLayout.setLayout(timeLayout)
        tempGroupLayout = QGroupBox(QApplication.translate("Table","BT",None))
        tempGroupLayout.setLayout(tempLayout)
        
        #main
        mainlayout = QVBoxLayout()
        mainlayout.addLayout(settingsHLayout)
        mainlayout.addWidget(phasesGroupLayout)
        mainlayout.addWidget(timeGroupLayout)
        mainlayout.addWidget(tempGroupLayout)
        mainlayout.addStretch()
        mainlayout.addLayout(buttonsLayout)
        
        self.setLayout(mainlayout)
        self.dialogbuttons.button(QDialogButtonBox.Ok).setFocus()

        settings = QSettings()
        if settings.contains("TransformatorPosition"):
            self.move(settings.value("TransformatorPosition"))
        
        mainlayout.setSizeConstraint(QLayout.SetFixedSize)


    # utility functions
    
    def forgroundOffset(self):
        if self.aw.qmc.timeindex[0] == -1:
            return 0
        else:
            return self.org_timex[self.aw.qmc.timeindex[0]]
    
    def backgroundOffset(self):
        if self.aw.qmc.timeindexB[0] != -1 and len(self.aw.qmc.timeB) > self.aw.qmc.timeindexB[0]:
            return self.aw.qmc.timeB[self.aw.qmc.timeindexB[0]]
        else:
            return 0
    
    def clearPhasesTargetTimes(self):
        for i in range(3):
            if self.phases_target_widgets_time[i] is not None:
                self.phases_target_widgets_time[i].setText("")
    
    def clearPhasesTargetPercent(self):
        for i in range(3):
            if self.phases_target_widgets_percent[i] is not None:
                self.phases_target_widgets_percent[i].setText("")
    
    def clearPhasesResults(self):
        for i in range(3):
            if self.phases_result_widgets[i] is not None:
                self.phases_result_widgets[i].setText("")
    
    def clearTimeTargets(self):
        for i in range(4):
            if self.time_target_widgets[i] is not None:
                self.time_target_widgets[i].setText("")
    
    def clearTimeResults(self):
        for i in range(4):
            if self.time_result_widgets[i] is not None:
                self.time_result_widgets[i].setText("")
    
    def clearTempTargets(self):
        for i in range(5):
            if self.temp_target_widgets[i] is not None:
                self.temp_target_widgets[i].setText("")
    
    def clearTempResults(self):
        for i in range(5):
            if self.temp_result_widgets[i] is not None:
                self.temp_result_widgets[i].setText("")

    # returns list of DRY, FCs, SCs and DROP profile times in seconds if event is set, otherwise None
    def getProfileTimes(self):
        offset = self.forgroundOffset()
        res = []
        for i in [1,2,4,6]:
            idx = self.aw.qmc.timeindex[i]
            if idx == 0 or len(self.aw.qmc.timex) < idx:
                res.append(None)
            else:
                res.append(self.aw.qmc.timex[idx] - offset)
        return res
        
    # returns list of CHARGE, DRY, FCs, SCs and DROP BT temperatures if event is set, otherwise None
    def getProfileTemps(self):
        res = []
        for i in [0,1,2,4,6]:
            idx = self.aw.qmc.timeindex[i]
            if idx in [-1,0] or len(self.aw.qmc.timex) < idx:
                res.append(None)
            elif len(self.aw.qmc.temp2) > idx:
                res.append(self.aw.qmc.temp2[idx])
            else:
                res.append(None)
        return res
    
    # returns list of DRYING, MAILARD, FINISHING target phases times in seconds as first result and phases percentages (float) as second result
    # if a phase is set not set None is returned instead of a value
    def getTargetPhases(self):
        res_times = []
        res_phases = []
        if self.phases_target_widgets_time is not None:
            for w in self.phases_target_widgets_time:
                r = None
                if w is not None:
                    txt = w.text()
                    if txt is not None and txt != "":
                        r = stringtoseconds(txt)
                res_times.append(r)
        if self.phases_target_widgets_percent is not None:
            for w in self.phases_target_widgets_percent:
                r = None
                if w is not None:
                    txt = w.text()
                    if txt is not None and txt != "":
                        r = float(txt)
                res_phases.append(r)
        return res_times, res_phases

    # returns list of DRY, FCs, SCs and DROP target times in seconds if event is set, otherwise None
    def getTargetTimes(self):
        res = []
        if self.time_target_widgets is not None:
            for w in self.time_target_widgets:
                r = None
                if w is not None:
                    txt = w.text()
                    if txt is not None and txt != "":
                        r = stringtoseconds(txt)
                res.append(r)
        return res

    # returns list of CHARGE, DRY, FCs, SCs and DROP BT temperatures if event is set, otherwise None
    def getTargetTemps(self):
        res = []
        if self.temp_target_widgets is not None:
            for w in self.temp_target_widgets:
                r = None
                if w is not None:
                    txt = w.text()
                    if txt is not None and txt != "":
                        r = float(txt)
                res.append(r)
        return res


    # message slots
    
    @pyqtSlot(int)
    def changeMappingMode(self,i):
        self.aw.qmc.transMappingMode = i
        self.updateTimeResults()
        self.updateTempResults()

    @pyqtSlot(int)
    def phasesTableColumnHeaderClicked(self,i):
        if self.phases_target_widgets_time[i] is not None and self.phases_target_widgets_percent[i] is not None:
            # clear target value i
            if self.phases_target_widgets_time[i].text() != "" or self.phases_target_widgets_percent[i].text() != "":
                self.phases_target_widgets_time[i].setText("")
                self.phases_target_widgets_percent[i].setText("")
            elif self.aw.qmc.background and self.aw.qmc.timeindexB[1]>0 and self.aw.qmc.timeindexB[2]>0 and self.aw.qmc.timeindexB[6]>0 and \
                    self.aw.qmc.timeindex[1]>0 and self.aw.qmc.timeindex[2]>0 and self.aw.qmc.timeindex[6]>0:
                back_offset = self.backgroundOffset()
                back_dry = self.aw.qmc.timeB[self.aw.qmc.timeindexB[1]]
                back_fcs = self.aw.qmc.timeB[self.aw.qmc.timeindexB[2]]
                back_drop = self.aw.qmc.timeB[self.aw.qmc.timeindexB[6]]
                s = 0
                if i == 0:
                    # DRYING
                    s = stringfromseconds(back_dry - back_offset)
                elif i == 1:
                    # MAILARD
                    s = stringfromseconds(back_fcs - back_dry)
                elif i == 2:
                    s = stringfromseconds(back_drop - back_fcs)
                self.phases_target_widgets_time[i].setText(s)
            self.updateTimeResults()
    
    @pyqtSlot(int)
    def phasesTableRowHeaderClicked(self,i):
        if i == 1: # row targets
            # clear all targets and results
            # clear all targets
            self.clearPhasesTargetTimes()
            self.clearPhasesTargetPercent()
            self.clearPhasesResults()

    @pyqtSlot(int)
    def timeTableColumnHeaderClicked(self,i):
        if self.time_target_widgets[i] is not None:
            # clear target value i
            if self.time_target_widgets[i].text() != "":
                self.time_target_widgets[i].setText("")
                self.updateTimeResults()
            elif self.aw.qmc.background:
                timeidx = [1,2,4,6][i]
                if self.aw.qmc.timeindex[timeidx] and self.aw.qmc.timeindexB[timeidx]:
                    s = stringfromseconds(self.aw.qmc.timeB[self.aw.qmc.timeindexB[timeidx]]-self.backgroundOffset(),False)
                    self.time_target_widgets[i].setText(s)
                    self.updateTimeResults()

    @pyqtSlot(int)
    def timeTableRowHeaderClicked(self,i):
        if i == 1: # row targets
            self.clearTimeTargets()
            self.clearTimeResults()

    @pyqtSlot(int)
    def tempTableColumnHeaderClicked(self,i):
        if self.temp_target_widgets[i] is not None:
            # clear target value i
            if self.temp_target_widgets[i].text() != "":
                self.temp_target_widgets[i].setText("")
                self.updateTempResults()
            elif self.aw.qmc.background:
                timeidx = [0,1,2,4,6][i]
                if self.aw.qmc.timeindexB[timeidx] > 0:
                    self.temp_target_widgets[i].setText(str(self.aw.float2float(self.aw.qmc.temp2B[self.aw.qmc.timeindexB[timeidx]])))
                    self.updateTempResults()
    
    @pyqtSlot(int)
    def tempTableRowHeaderClicked(self,i):
        if i == 1: # row targets
            self.clearTempTargets()
            self.clearTempResults()
    
    @pyqtSlot()
    def updatePhasesWidget(self):
        self.clearTimeTargets()
        sender = self.sender()
        # clear corresponding time target if percentage target is set, or the otherway around
        if sender.text() != "":
            try:
                time_idx = self.phases_target_widgets_time.index(sender)
                self.phases_target_widgets_percent[time_idx].setText("")
            except:
                pass
            try:
                percent_idx = self.phases_target_widgets_percent.index(sender)
                self.phases_target_widgets_time[percent_idx].setText("")
            except:
                pass
        self.updateTimeResults()
    
    @pyqtSlot()
    def updateTimesWidget(self):
        self.clearPhasesTargetTimes()
        self.clearPhasesTargetPercent()
        self.updateTimeResults()

    # updates time and phases result widgets
    def updateTimeResults(self):
        self.targetTimes = self.getTargetTimes()
        time_targets_clear = all(v is None for v in self.targetTimes)
        target_times, target_phases = self.getTargetPhases()
        phases_targets_clear = all(v is None for v in target_times + target_phases)
        self.clearPhasesResults()
        self.clearTimeResults()
        if not (phases_targets_clear and time_targets_clear):
            self.clearTimeResults()
            # phases targets are set, first clear the time targets
            if not phases_targets_clear:
                self.targetTimes = self.getTargetPhasesTimes()
            else:
                self.targetTimes = self.getTargetTimes()
            # set new time results
            result_times = self.calcTimeResults()
            for i in range(4):
                if self.time_result_widgets[i] is not None:
                    if result_times[i] is None:
                        s = ""
                    else:
                        s = stringfromseconds(result_times[i],leadingzero=False)
                    self.time_result_widgets[i].setText(s)
            # set new phases results
            result_times = self.calcTimeResults()
            if all(result_times[r] is not None for r in [0,1,3]):
                # DRYING
                drying_period = result_times[0]
                drying_percentage = 100 * drying_period / result_times[3]
                drying_str = \
                        "{}    {}%".format(stringfromseconds(drying_period,leadingzero=False),self.aw.float2float(drying_percentage))
                self.phases_result_widgets[0].setText(drying_str)
                # MAILARD
                mailard_period = result_times[1] - result_times[0]
                mailard_percentage = 100 * mailard_period / result_times[3]
                mailard_str = \
                        "{}    {}%".format(stringfromseconds(mailard_period,leadingzero=False),self.aw.float2float(mailard_percentage))
                self.phases_result_widgets[1].setText(mailard_str)
                # FINISHING
                finishing_period = result_times[3] - result_times[1]
                finishing_percentage = 100 * finishing_period / result_times[3]
                finishing_str = \
                        "{}    {}%".format(stringfromseconds(finishing_period,leadingzero=False),self.aw.float2float(finishing_percentage))
                self.phases_result_widgets[2].setText(finishing_str)
            else:
                for w in self.phases_result_widgets:
                    if w is not None:
                        w.setText("")

    @pyqtSlot()
    def updateTempResults(self):
        self.targetTemps = self.getTargetTemps()
        if all(v is None for v in self.targetTemps):
            # clear all results if no targets are set
            self.clearTempResults()
        else:
            # set new results
            result_temps,fit = self.calcTempResults()
            for i in range(5):
                if self.temp_result_widgets[i] is not None and result_temps[i] is not None:
                    self.temp_result_widgets[i].setText(str(self.aw.float2float(result_temps[i])) + self.aw.qmc.mode)
            if fit is None:
                s = ""
            elif isinstance(fit,str):
                s = fit
            else:
                s = self.aw.fit2str(fit)
            self.temp_formula.setText(s)
            self.temp_formula.repaint()

    #called from Apply button
    @pyqtSlot(bool)
    def apply(self,_=False):
        applied_time = self.applyTimeTransformation()
        applied_temp = self.applyTempTransformation()
        if applied_time or applied_temp:
            self.aw.qmc.roastUUID = None
            self.aw.qmc.roastdate = QDateTime.currentDateTime()
            self.aw.qmc.roastepoch = self.aw.qmc.roastdate.toTime_t()
            self.aw.qmc.roasttzoffset = libtime.timezone
            self.aw.qmc.roastbatchnr = 0
            self.aw.setCurrentFile(None,addToRecent=False)
            self.aw.qmc.l_event_flags_dict = {}
            self.aw.qmc.l_annotations_dict = {}
            self.aw.qmc.fileDirty()
            self.aw.qmc.timealign()
            self.aw.autoAdjustAxis()
            self.aw.qmc.redraw()
        else:
            self.restore()
    
    #called from Restore button
    @pyqtSlot(bool)
    def restore(self,_=False):
        self.aw.setCurrentFile(self.org_curFile,addToRecent=False)
        self.aw.qmc.roastUUID = self.org_UUID
        self.aw.qmc.roastdate = self.org_roastdate
        self.aw.qmc.roastepoch = self.org_roastepoch
        self.aw.qmc.roasttzoffset = self.org_roasttzoffset
        self.aw.qmc.roastbatchnr = self.org_roastbatchnr
        if self.org_safesaveflag:
            self.aw.qmc.fileDirty()
        else:
            self.aw.qmc.fileClean()
        self.aw.qmc.l_event_flags_dict = self.org_l_event_flags_dict
        self.aw.qmc.l_annotations_dict = self.org_l_annotations_dict
        self.aw.qmc.timex = self.org_timex[:]
        self.aw.qmc.extratimex = copy.deepcopy(self.org_extratimex)
        self.aw.qmc.temp2 = self.org_temp2[:]
        self.aw.autoAdjustAxis()
        self.aw.qmc.redraw()
    
    #called from OK button
    @pyqtSlot()
    def applyTransformations(self):
        self.apply()
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue("TransformatorPosition",self.frameGeometry().topLeft())
        self.accept()

    #called from Cancel button
    @pyqtSlot()
    def restoreState(self):
        self.restore()
        self.aw.qmc.transMappingMode = self.org_transMappingMode
        #save window position (only; not size!)
        settings = QSettings()
        settings.setValue("TransformatorPosition",self.geometry().topLeft())
        self.closeHelp()
        self.reject()

    @pyqtSlot(bool)
    def openHelp(self,_=False):
        self.helpdialog = self.aw.showHelpDialog(
                self,            # this dialog as parent
                self.helpdialog, # the existing help dialog
                QApplication.translate("Form Caption","Profile Transposer Help",None),
                transposer_help.content())

    def closeHelp(self):
        self.aw.closeHelpDialog(self.helpdialog)

    def closeEvent(self, _):
        self.restoreState()


    # Calculations

    # returns the list of results times in seconds
    def calcTimeResults(self):
        res = []
        if self.aw.qmc.transMappingMode == 0:
            # discrete mapping
            # adding CHARGE
            fits = self.calcDiscretefits([0] + self.profileTimes,[0] + self.targetTimes)
            for i in range(4):
                if self.profileTimes[i] is not None and fits[i+1] is not None:
                    res.append(numpy.poly1d(fits[i+1])(self.profileTimes[i]))
                else:
                    res.append(None)
        else:
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                try:
                    fit = self.calcTimePolyfit() # that that this fit is already applied to numpy.polyfit !!
                    for i in range(4):
                        if fit is not None and self.profileTimes[i] is not None:
                            res.append(fit(self.profileTimes[i]))
                        else:
                            res.append(None)
                except numpy.RankWarning:
                    pass
                except:
                    pass
        return res

    # returns the list of results temperatures and the polyfit or None as second result
    def calcTempResults(self):
        res = []
        fit = None
        if self.aw.qmc.transMappingMode == 0:
            # discrete mapping
            fits = self.calcDiscretefits(self.profileTemps,self.targetTemps)
            for i in range(5):
                if self.profileTemps[i] is not None and fits[i] is not None:
                    res.append(numpy.poly1d(fits[i])(self.profileTemps[i]))
                else:
                    res.append(None)
            active_fits = list(filter(lambda x: x[1][1] is not None,zip(fits,zip(self.profileTemps,self.targetTemps))))
            if len(active_fits) > 0 and len(active_fits) < 3:
                fit = self.aw.fit2str(fits[0])
            else:
                formula = ""
                last_target = None
                for f,tpl in reversed(active_fits[:-1]):
                    if last_target is None:
                        formula = self.aw.fit2str(f)
                    else:
                        formula = "({} if x<{} else {})".format(self.aw.fit2str(f), last_target, formula)
                    last_target = tpl[1]
                fit = formula
        else:
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                try:
                    fit = self.calcTempPolyfit() # numpy.poly1d not yet applied to this fit
                    p = numpy.poly1d(fit)
                    for i in range(5):
                        if fit is not None and self.profileTemps[i] is not None:
                            res.append(p(self.profileTemps[i]))
                        else:
                            res.append(None)
                except numpy.RankWarning:
                    pass
                except:
                    pass
        return res,fit
    
    # returns target times based on the phases target
    def getTargetPhasesTimes(self):
        # get the offset
        offset = self.forgroundOffset()
        # get profile phases events time
        dry = self.aw.qmc.timex[self.aw.qmc.timeindex[1]] - offset
        fcs = self.aw.qmc.timex[self.aw.qmc.timeindex[2]] - offset
        drop = self.aw.qmc.timex[self.aw.qmc.timeindex[6]] - offset
        # flags for targets set
        dry_set = False
        drop_set = False
        fcs_set = False
        
        # first determine the target DROP time (relative to the profile drop) if any
        if self.phases_target_widgets_time[2] is not None and self.phases_target_widgets_time[2].text() != "":
            drop = fcs + stringtoseconds(self.phases_target_widgets_time[2].text())
            drop_set = True
        elif self.phases_target_widgets_percent[2] is not None and self.phases_target_widgets_percent[2].text() != "":
            drop = fcs + (float(self.phases_target_widgets_percent[2].text()) * drop / 100)
            drop_set = True
        
        # determine the target DRY time (relative to the target drop of above) if any
        if self.phases_target_widgets_time[0] is not None and self.phases_target_widgets_time[0].text() != "":
            dry = stringtoseconds(self.phases_target_widgets_time[0].text())
            dry_set = True
        elif self.phases_target_widgets_percent[0] is not None and self.phases_target_widgets_percent[0].text() != "":
            dry = float(self.phases_target_widgets_percent[0].text()) * drop / 100
            dry_set = True
        
        # determine the target FCs time (relative to the target drop of above) if any
        if self.phases_target_widgets_time[1] is not None and self.phases_target_widgets_time[1].text() != "":
            fcs = dry + stringtoseconds(self.phases_target_widgets_time[1].text())
            fcs_set = True
        elif self.phases_target_widgets_percent[1] is not None and self.phases_target_widgets_percent[1].text() != "":
            fcs = dry + (float(self.phases_target_widgets_percent[1].text()) * drop / 100)
            fcs_set = True
            
#        return [(dry if dry_set else None),(fcs if fcs_set else None), None, (drop if drop_set else None)]
        # set all unset target times to the profile times
        return [
            (dry if dry_set else (self.aw.qmc.timex[self.aw.qmc.timeindex[1]] - offset)),
            (fcs if fcs_set else (self.aw.qmc.timex[self.aw.qmc.timeindex[2]] - offset)),
            None,
            (drop if drop_set else (self.aw.qmc.timex[self.aw.qmc.timeindex[6]] - offset))]

    # calculates the linear (self.aw.qmc.transMappingMode = 1) or quadratic (self.aw.qmc.transMappingMode = 2) mapping
    # between the profileTimes and the targetTimes
    def calcTimePolyfit(self):
        # initialized by CHARGE time 00:00
        xa = [0]
        ya = [0]
        for i in range(4):
            if self.targetTimes[i] is not None:
                xa.append(self.profileTimes[i])
                ya.append(self.targetTimes[i])
        deg = self.aw.qmc.transMappingMode
        if len(xa) > 1:
            try:
                deg = min(len(xa) - 1,deg)
                z = numpy.polyfit(xa, ya, deg)
                return numpy.poly1d(z)
            except:
                return None
        else:
            return None

    # calculates the linear (self.aw.qmc.transMappingMode = 1) or quadratic (self.aw.qmc.transMappingMode = 2) mapping
    # between the profileTemps and the targetTemps
    def calcTempPolyfit(self):
        xa = []
        ya = []
        for i in range(5):
            if self.targetTemps[i] is not None:
                xa.append(self.profileTemps[i])
                ya.append(self.targetTemps[i])
        deg = self.aw.qmc.transMappingMode
        if len(xa) > 0:
            try:
                deg = min(len(xa) - 1,deg)
                if deg == 0:
                    z = numpy.array([1, ya[0] - xa[0]])
                else:
                    z = numpy.polyfit(xa, ya, deg)
                return z
            except:
                return None
        else:
            return None
    
    # returns a list of segment-wise fits between sources and targets
    # each fit is a numpy.array as returned by numpy.polyfit
    # a source element of None generates None as fit
    # a target element of None is skipped and pervious and next segements are joined
    # the lists of sources and targets are expected to be of the same length
    # the length of the result list is the same as that of the sources and targets
    def calcDiscretefits(self,sources,targets):
        if len(sources) != len(targets):
            return [None]*len(sources)
        fits = [None]*len(sources)
        last_fit = None
        for i in range(len(sources)):
            if sources[i] is not None:
                if targets[i] is None:
                    # we take the last fit
                    fits[i] = last_fit
                else:
                    next_idx = None # the index of the next non-empty source/target pair
                    for j in range(i+1,len(sources)):
                        if sources[j] is not None and targets[j] is not None:
                            next_idx = j
                            break
                    if next_idx is None:
                        if last_fit is not None:
                            fits[i] = last_fit # copy previous fit
                        else:
                            # set a simple offset only as there is no previous nor next fit
                            fits[i] = numpy.array([1,targets[i]-sources[i]])
                    else:
                        fits[i] = numpy.polyfit([sources[i],sources[j]],[targets[i],targets[j]],1)
                    # if this is the first fit, we copy it to all previous positions
                    if last_fit is None:
                        for k in range(0,i):
                            if sources[k] is not None:
                                fits[k] = fits[i]
                    # register this fit
                    last_fit = fits[i]
        return fits

    # fits of length 5
    def applyDiscreteTimeMapping(self,timex,fits):
        offset = self.forgroundOffset()
        res_timex = []
        if offset == 0:
            new_offset = 0
        else:
            new_offset = numpy.poly1d(fits[0])(offset)
        for i in range(len(timex)):
            # first fit is to be applied for all readings before DRY
            j = 0
            if self.aw.qmc.timeindex[6] > 0 and i >= self.aw.qmc.timeindex[6]:
                # last fit counts after DROP
                j = 4
            elif self.aw.qmc.timeindex[4] > 0 and i >= self.aw.qmc.timeindex[4]:
                j = 3 # after SCs
            elif self.aw.qmc.timeindex[2] > 0 and i >= self.aw.qmc.timeindex[2]:
                j = 2 # after FCs
            elif self.aw.qmc.timeindex[1] > 0 and i >= self.aw.qmc.timeindex[1]:
                j = 1 # after DRY
            fit = numpy.poly1d(fits[j]) # fit to be applied
            res_timex.append(fit(timex[i] - offset)+new_offset)
        return res_timex
    
    # returns False if no transformation was applied
    def applyTimeTransformation(self):
        # first update the targets
        self.targetTimes = self.getTargetTimes()
        if all(v is None for v in self.targetTimes):
            target_times, target_phases = self.getTargetPhases()
            if all(v is None for v in target_times + target_phases):
                self.aw.qmc.timex = self.org_timex[:]
                self.aw.qmc.extratimex = copy.deepcopy(self.org_extratimex)
                return False
            else:
                self.targetTimes = self.getTargetPhasesTimes()
        # calculate the offset of 00:00
        offset = self.forgroundOffset()
        # apply either the discrete or the polyfit mappings
        if self.aw.qmc.transMappingMode == 0:
            # discrete mapping
            fits = self.calcDiscretefits([0] + self.profileTimes,[0] + self.targetTimes)
            self.aw.qmc.timex = self.applyDiscreteTimeMapping(self.org_timex,fits)
            # apply to the extra timex
            self.aw.qmc.extratimex = []
            for timex in self.org_extratimex:
                try:
                    timex_trans = self.applyDiscreteTimeMapping(timex,fits)
                except:
                    timex_trans = timex
                self.aw.qmc.extratimex.append(timex_trans)
        else:
            # polyfit mappings
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                try:
                    fit = self.calcTimePolyfit() # the fit returned here is already applied to numpy.poly1d
                    if fit is not None:
                        self.aw.qmc.timex = [fit(tx-offset) for tx in self.org_timex]
                        if len(self.aw.qmc.timex) > 0 and self.aw.qmc.timeindex[0] != -1:
                            foffset = self.aw.qmc.timex[0]
                            self.aw.qmc.timex = [tx+foffset for tx in self.aw.qmc.timex]
                        extratimex = []
                        for timex in self.org_extratimex:
                            offset = 0
                            if self.aw.qmc.timeindex[0] != -1:
                                offset = timex[self.aw.qmc.timeindex[0]]
                            new_timex = [fit(tx-offset) for tx in timex]
                            if len(new_timex) > 0 and self.aw.qmc.timeindex[0] != -1:
                                foffset = new_timex[0]
                                new_timex = [tx+foffset for tx in new_timex]
                            extratimex.append(new_timex)
                        self.aw.qmc.extratimex = extratimex
                except numpy.RankWarning:
                    pass
        return True
    
    # returns False if no transformation was applied
    def applyTempTransformation(self):
        # first update the targets
        self.targetTemps = self.getTargetTemps()
        if all(v is None for v in self.targetTemps):
            self.aw.qmc.temp2 = self.org_temp2[:]
            return False
        # apply either the discrete or the polyfit mappings
        if self.aw.qmc.transMappingMode == 0:
            # discrete mappings, length 5
            fits = self.calcDiscretefits(self.profileTemps,self.targetTemps)
            self.aw.qmc.temp2 = []
            for i in range(len(self.org_temp2)):
                # first fit is to be applied for all readings before DRY
                j = 0
                if self.aw.qmc.timeindex[6] > 0 and i >= self.aw.qmc.timeindex[6]:
                    # last fit counts after DROP
                    j = 4
                elif self.aw.qmc.timeindex[4] > 0 and i >= self.aw.qmc.timeindex[4]:
                    j = 3 # after SCs
                elif self.aw.qmc.timeindex[2] > 0 and i >= self.aw.qmc.timeindex[2]:
                    j = 2 # after FCs
                elif self.aw.qmc.timeindex[1] > 0 and i >= self.aw.qmc.timeindex[1]:
                    j = 1 # after DRY
                fit = numpy.poly1d(fits[j]) # fit to be applied
                
                tp = self.org_temp2[i]
                if tp is None or tp == -1:
                    self.aw.qmc.temp2.append(tp)
                else:
                    self.aw.qmc.temp2.append(fit(tp))
            return True
        else:
            # polyfit mappings
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                try:
                    fit = numpy.poly1d(self.calcTempPolyfit())
                    if fit is not None:
                        self.aw.qmc.temp2 = [(-1 if (temp is None) or (temp == -1) else fit(temp)) for temp in self.org_temp2]
                except numpy.RankWarning:
                    pass
        return True
    
    # tables
    
    def createPhasesTable(self):
    
        self.phasestable.setStyleSheet("QTableView { background-color: red); }")

        self.phasestable.setRowCount(3)
        self.phasestable.setColumnCount(3)
        self.phasestable.horizontalHeader().setStretchLastSection(False)
        self.timetable.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.timetable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.timetable.horizontalHeader().setHighlightSections(False)
        self.phasestable.setHorizontalHeaderLabels([QApplication.translate("Label","Drying",None),
                                                         QApplication.translate("Label","Maillard",None),
                                                         QApplication.translate("Label","Finishing",None)])
        self.phasestable.setVerticalHeaderLabels([QApplication.translate("Table","Profile",None),
                                                         QApplication.translate("Table","Target",None),
                                                         QApplication.translate("Table","Result",None)])
        self.phasestable.setShowGrid(True)
        self.phasestable.setAlternatingRowColors(True)
        self.phasestable.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.phasestable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#        self.phasestable.setFrameStyle(QTableWidget.NoFrame)
        self.phasestable.setFixedSize(
            self.phasestable.horizontalHeader().length() + 
#                self.phasestable.verticalHeader().width(), # only the width of the default labels (numbers)
                self.phasestable.verticalHeader().sizeHint().width(),
            self.phasestable.verticalHeader().length() + 
                self.phasestable.horizontalHeader().height())
        self.phasestable.setEditTriggers(QAbstractItemView.NoEditTriggers);
        self.phasestable.setFocusPolicy(Qt.NoFocus);
        self.phasestable.setSelectionMode(QAbstractItemView.NoSelection)
        self.phasestable.setAutoScroll(False)
        self.phasestable.verticalHeader().sectionClicked.connect(self.phasesTableRowHeaderClicked)
        self.phasestable.horizontalHeader().sectionClicked.connect(self.phasesTableColumnHeaderClicked)

        self.phases_target_widgets_time = []
        self.phases_target_widgets_percent = []
        self.phases_result_widgets = []
        
        profilePhasesTimes = [None]*3 # DRYING, MAILARD, FINISHING
        profilePhasesPercentages = [None] * 3
        #
        # the phases transformation are only enabled if at least DRY, FCs and DROP events are set
        phases_enabled = self.aw.qmc.timeindex[1] and self.aw.qmc.timeindex[2] and self.aw.qmc.timeindex[6]
        #
        if phases_enabled:
            profilePhasesTimes[0] = self.profileTimes[0] # DRYING == DRY
            if self.profileTimes[0] is not None and self.profileTimes[1] is not None:
                profilePhasesTimes[1] = self.profileTimes[1] - self.profileTimes[0]
            if self.profileTimes[1] is not None and self.profileTimes[3] is not None:
                profilePhasesTimes[2] = self.profileTimes[3] - self.profileTimes[1]
            if self.profileTimes[3] is not None:
                profilePhasesPercentages = [(ppt/self.profileTimes[3])*100 for ppt in profilePhasesTimes if ppt is not None]

        for i in range(3):
            if len(profilePhasesTimes) > i and profilePhasesTimes[i] is not None:
                profile_phases_time_str = \
                    "{}    {}%".format(stringfromseconds(profilePhasesTimes[i],leadingzero=False),self.aw.float2float(profilePhasesPercentages[i]))
                profile_phases_widget = QTableWidgetItem(profile_phases_time_str)
                profile_phases_widget.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                self.phasestable.setItem(0,i,profile_phases_widget)
                #
                target_widget_time = QLineEdit("")
                target_widget_time.setValidator(QRegExpValidator(self.regextime))
                target_widget_time.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                if phases_enabled:
                    target_widget_time.editingFinished.connect(self.updatePhasesWidget)
                else:
                    target_widget_time.setEnabled(False)
                target_widget_percent = QLineEdit("")
                target_widget_percent.setValidator(QRegExpValidator(self.regexpercent))
                target_widget_percent.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                if phases_enabled:
                    target_widget_percent.editingFinished.connect(self.updatePhasesWidget)
                else:
                    target_widget_percent.setEnabled(False)
                target_cell_widget = QWidget()
                target_cell_layout = QHBoxLayout(target_cell_widget)
                target_cell_layout.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                target_cell_layout.setContentsMargins(4,4,4,4)
                target_cell_layout.addWidget(target_widget_time)
                target_cell_layout.addWidget(target_widget_percent)
                target_cell_widget.setLayout(target_cell_layout)
                self.phasestable.setCellWidget(1,i,target_cell_widget)
                #
                result_widget = QTableWidgetItem("")
                result_widget.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                self.phasestable.setItem(2,i,result_widget)
            else:
                target_widget_time = None
                target_widget_percent = None
                result_widget = None
            self.phases_target_widgets_time.append(target_widget_time)
            self.phases_target_widgets_percent.append(target_widget_percent)
            self.phases_result_widgets.append(result_widget)

    def createTimeTable(self):
        self.timetable.clear()
        self.timetable.setRowCount(3)
        self.timetable.setColumnCount(4)
        self.timetable.horizontalHeader().setStretchLastSection(False)
        self.timetable.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.timetable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.timetable.horizontalHeader().setHighlightSections(False)
        self.timetable.setHorizontalHeaderLabels([QApplication.translate("Label","DRY END",None),
                                                         QApplication.translate("Label","FC START",None),
                                                         QApplication.translate("Label","SC START",None),
                                                         QApplication.translate("Label","DROP",None)])
        self.timetable.setVerticalHeaderLabels([QApplication.translate("Table","Profile",None),
                                                         QApplication.translate("Table","Target",None),
                                                         QApplication.translate("Table","Result",None)])
        self.timetable.setShowGrid(True)
        self.timetable.setAlternatingRowColors(False)
        self.timetable.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.timetable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.timetable.setFrameStyle(QTableWidget.NoFrame)
        self.timetable.setFixedSize(
            self.timetable.horizontalHeader().length() + 
#                self.timetable.verticalHeader().width(), # only the width of the default labels (numbers)
                self.timetable.verticalHeader().sizeHint().width(),
            self.timetable.verticalHeader().length() + 
                self.timetable.horizontalHeader().height())
        self.timetable.setEditTriggers(QAbstractItemView.NoEditTriggers);
        self.timetable.setFocusPolicy(Qt.NoFocus);
        self.timetable.setSelectionMode(QAbstractItemView.NoSelection)
        self.timetable.setAutoScroll(False)
#        self.timetable.setStyleSheet("QTableWidget { background-color: #fafafa; }")
        self.timetable.verticalHeader().sectionClicked.connect(self.timeTableRowHeaderClicked)
        self.timetable.horizontalHeader().sectionClicked.connect(self.timeTableColumnHeaderClicked)
        
        self.time_target_widgets = []
        self.time_result_widgets = []
        
        for i in range(4):
            if len(self.profileTimes) > i and not self.profileTimes[i] is None:
                profile_time_str = stringfromseconds(self.profileTimes[i],leadingzero=False)
                profile_widget = QTableWidgetItem(profile_time_str)
                profile_widget.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                self.timetable.setItem(0,i,profile_widget)
                #
                target_widget = QLineEdit("")
                target_widget.setValidator(QRegExpValidator(self.regextime))
                target_widget.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                target_widget.editingFinished.connect(self.updateTimesWidget)
                target_cell_widget = QWidget()
                target_cell_layout = QHBoxLayout(target_cell_widget)
                target_cell_layout.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                target_cell_layout.setContentsMargins(4,4,4,4)
                target_cell_layout.addWidget(target_widget)
                target_cell_widget.setLayout(target_cell_layout)
                self.timetable.setCellWidget(1,i,target_cell_widget)
                #
                result_widget = QTableWidgetItem("") #profile_time_str)
                result_widget.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                self.timetable.setItem(2,i,result_widget)
            else:
                target_widget = None
                result_widget = None
            self.time_target_widgets.append(target_widget)
            self.time_result_widgets.append(result_widget)

    def createTempTable(self):
        self.temptable.clear()
        self.temptable.setRowCount(3)
        self.temptable.setColumnCount(5)
        self.temptable.horizontalHeader().setStretchLastSection(False)
        self.temptable.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.temptable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.temptable.setHorizontalHeaderLabels([QApplication.translate("Label","CHARGE",None),
                                                         QApplication.translate("Label","DRY END",None),
                                                         QApplication.translate("Label","FC START",None),
                                                         QApplication.translate("Label","SC START",None),
                                                         QApplication.translate("Label","DROP",None)])
        self.temptable.setVerticalHeaderLabels([QApplication.translate("Table","Profile",None),
                                                         QApplication.translate("Table","Target",None),
                                                         QApplication.translate("Table","Result",None)])
        self.temptable.setShowGrid(True)
        self.temptable.setAlternatingRowColors(False)
        self.temptable.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.temptable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#        self.temptable.setFrameStyle(QTableWidget.NoFrame)
        self.temptable.setFixedSize(
            self.temptable.horizontalHeader().length() + 
#                self.temptable.verticalHeader().width(), # only the width of the default labels (numbers)
                self.temptable.verticalHeader().sizeHint().width(),
            self.temptable.verticalHeader().length() + 
                self.temptable.horizontalHeader().height())
        self.temptable.setEditTriggers(QAbstractItemView.NoEditTriggers);
        self.temptable.setFocusPolicy(Qt.NoFocus);
        self.temptable.setSelectionMode(QAbstractItemView.NoSelection)
        self.temptable.setAutoScroll(False)
        self.temptable.verticalHeader().sectionClicked.connect(self.tempTableRowHeaderClicked)
        self.temptable.horizontalHeader().sectionClicked.connect(self.tempTableColumnHeaderClicked)
        
        self.temp_target_widgets = []
        self.temp_result_widgets = []
        
        for i in range(5):
            if len(self.profileTemps) > i and self.profileTemps[i] is not None:
                profile_temp_str = str(self.aw.float2float(self.profileTemps[i])) + self.aw.qmc.mode
                profile_widget = QTableWidgetItem(profile_temp_str)
                profile_widget.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                self.temptable.setItem(0,i,profile_widget)
                #
                target_widget = QLineEdit("")
                target_widget.setValidator(QRegExpValidator(self.regextemp))
                target_widget.editingFinished.connect(self.updateTempResults)
                target_widget.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                
                target_cell_widget = QWidget()
                target_cell_layout = QHBoxLayout(target_cell_widget)
                target_cell_layout.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                target_cell_layout.setContentsMargins(4,4,4,4)
                target_cell_layout.addWidget(target_widget)
#                target_cell_layout.addWidget(QLabel(self.aw.qmc.mode))
                target_cell_widget.setLayout(target_cell_layout)
                self.temptable.setCellWidget(1,i,target_cell_widget)
                #
                result_widget = QTableWidgetItem("")
                result_widget.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                self.temptable.setItem(2,i,result_widget)
            else:
                target_widget = None
                result_widget = None
            self.temp_target_widgets.append(target_widget)
            self.temp_result_widgets.append(result_widget)