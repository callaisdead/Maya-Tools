import maya.cmds as mc
import maya.mel as mel
import maya.cmds as cmds
from maya.OpenMaya import MVector
import maya.OpenMayaUI as omui #omui = open maya ui
from PySide2.QtWidgets import QVBoxLayout, QWidget, QPushButton, QMainWindow, QHBoxLayout, QGridLayout, QLineEdit, QLabel, QSlider
from PySide2.QtCore import Qt
from shiboken2 import wrapInstance

#commandPort -n "localhost:7001" -stp "mel";

class LimbRiggingWidget(QWidget):
    def __init__(self):
        mainWindow: QMainWindow = LimbRiggingWidget.GetMayaMainWindow()
        
        for exisiting in mainWindow.findChildren(QWidget, LimbRiggingWidget.GetWindowUniqueId()):
            exisiting.deleteLater()
        
        super().__init__(parent=mainWindow)
        self.controllerSize = 10
        self.setWindowTitle("Limb Rigging Tool")
        self.setWindowFlags(Qt.Window)
        self.setObjectName(LimbRiggingWidget.GetWindowUniqueId())

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        hintLabel = QLabel("Please Select the Root, Middle, and End joint of your limb:")
        self.masterLayout.addWidget(hintLabel)

        controllerSizeCtrlLayout = QHBoxLayout()
        self.masterLayout.addLayout(controllerSizeCtrlLayout)

        controllerSizeCtrlLayout.addWidget(QLabel("Controller Size:"))
        controllerSizeSlider =QSlider()
        controllerSizeSlider.setValue(1)
        controllerSizeSlider.setMinimum(1)
        controllerSizeSlider.setMaximum(30)
        controllerSizeSlider.setOrientation(Qt.Horizontal)
        controllerSizeCtrlLayout.addWidget(controllerSizeSlider)
        self.sizeDisplayLabel = QLabel(str(self.controllerSize))
        controllerSizeSlider.valueChanged.connect(self.ControllerSizeChanged)
        controllerSizeCtrlLayout.addWidget(self.sizeDisplayLabel)

        rigLimbBtn = QPushButton("Rig the limb")
        rigLimbBtn.clicked.connect(self.RigTheLimb)
        self.masterLayout.addWidget(rigLimbBtn)

    def RigTheLimb(self):
        print("start to rig the limb")
        selection = mc.ls(sl=True)

        rootJnt = selection[0]
        midJnt = selection[1]
        endJnt = selection[2]

        rootFkCtrl, rootFKCtrlGrp = self.CreateFKForJnt(rootJnt)
        midFKCtrl, midFKCtrlGrp = self.CreateFKForJnt(midJnt)
        endFKCtrl, endFKCtrlGrp = self.CreateFKForJnt(endJnt)

        mc.parent(midFKCtrlGrp, rootFkCtrl)
        mc.parent(endFKCtrlGrp, midFKCtrl)

        ikEndCtrlName, ikEndCtrlGrpName, midIkCtrlName, midIkCtrlGrpName, ikHandleName = self.CreateIkControl(rootJnt, midJnt, endJnt)

        ikfkBlendCtrlName = "ac_ikfk_blend_" + rootJnt
        mel.eval(f"curve -d 1 -n {ikfkBlendCtrlName} -p -10 0 -4 -p -10 0 -2 -p -8 0 -2 -p -8 0 -4 -p -6 0 -4 -p -6 0 -6 -p -8 0 -6 -p -8 0 -8 -p -10 0 -8 -p -10 0 -6 -p -12 0 -6 -p -12 0 -4 -p -10 0 -4 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12")
        ikfkBlendCtrlGrpName = ikfkBlendCtrlName + "_grp"
        mc.group(ikfkBlendCtrlName, n = ikfkBlendCtrlGrpName)

        rootJntPosVals = mc.xform(rootJnt, t = True, q = True, ws = True)
        rootJntPos = MVector(rootJntPosVals[0], rootJntPosVals[1], rootJntPosVals[2])
        ikfkBlendCtrlPos = rootJntPos + MVector(rootJntPos.x, 0, 0)
        mc.move(ikfkBlendCtrlPos[0], ikfkBlendCtrlPos[1], ikfkBlendCtrlPos[2], ikfkBlendCtrlGrpName)

        ikfkBlendAttrName = "ikfk_blend"
        mc.addAttr(ikfkBlendCtrlName, ln=ikfkBlendAttrName, k=True, min=0, max=1)

        mc.expression(s= f"{rootFKCtrlGrp}.v=1-{ikfkBlendCtrlName}.{ikfkBlendAttrName};")
        mc.expression(s=f"{ikEndCtrlGrpName}.v={ikfkBlendCtrlName}.{ikfkBlendAttrName};")
        mc.expression(s=f"{midIkCtrlGrpName}.v={ikfkBlendCtrlName}.{ikfkBlendAttrName};")
        mc.expression(s=f"{ikHandleName}.v={ikfkBlendCtrlName}.{ikfkBlendAttrName};")

        endJntOrientConstraint = mc.listConnections(endJnt, s=True, t="orientConstraint")[0]
        mc.expression(s=f"{endJntOrientConstraint}.{endFKCtrl}W0=1-{ikfkBlendCtrlName}.{ikfkBlendAttrName};")
        mc.expression(s=f"{endJntOrientConstraint}.{ikEndCtrlName}W1={ikfkBlendCtrlName}.{ikfkBlendAttrName};")

        topGrpName = f"{rootJnt}_rig_grp"

        mc.group([rootFKCtrlGrp, ikEndCtrlGrpName, midIkCtrlGrpName, ikfkBlendCtrlGrpName], n = topGrpName)



     
    def CreateFKForJnt(self,jnt):
        fkCtrlName = "ac_fk_" + jnt
        fkCtrlGrpName = fkCtrlName + "_grp"
        mc.circle(n=fkCtrlName, r=self.controllerSize, nr=(1,0,0))
        mc.group(fkCtrlName, n = fkCtrlGrpName)
        mc.matchTransform(fkCtrlGrpName, jnt)
        mc.orientConstraint(fkCtrlName, jnt)
        return fkCtrlName, fkCtrlGrpName
    
    def CreateIkControl(self, rootJnt, midJnt, endJnt):
        # wrist controller
        ikEndCtrlName = "ac_ik_" + endJnt
        mel.eval(f"curve -d 1 -n {ikEndCtrlName} -p  -0.5 0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 -0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 -0.5 0.5 -p -0.5 0.5 0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 ;")
        mc.scale(self.controllerSize, self.controllerSize, self.controllerSize, ikEndCtrlName, r=True)
        mc.makeIdentity(ikEndCtrlName, apply=True) #freeze transformation
        ikEndCtrlGrpName = ikEndCtrlName + "_grp"
        mc.group(ikEndCtrlName, n = ikEndCtrlGrpName)
        mc.matchTransform(ikEndCtrlGrpName, endJnt)
        mc.orientConstraint(ikEndCtrlName, endJnt)

        # ik handle
        ikHandleName = "ikHandle_" + endJnt
        mc.ikHandle(n = ikHandleName, sj=rootJnt, ee=endJnt, sol="ikRPsolver")

        rootJntPosVals = mc.xform(rootJnt, q=True, t=True, ws=True) # getting the world space (ws = True) translate (t = True) of the root joint, as a list of 3 values
        rootJntPos = MVector(rootJntPosVals[0], rootJntPosVals[1], rootJntPosVals[2])

        endJntPosVals = mc.xform(endJnt, q=True, t=True, ws=True)
        endJntPos = MVector(endJntPosVals[0], endJntPosVals[1], endJntPosVals[2])

        poleVectorVals = mc.getAttr(ikHandleName + ".poleVector")[0]
        poleVector = MVector(poleVectorVals[0], poleVectorVals[1], poleVectorVals[2])
        poleVector.normalize()

        vectorToEnd = endJntPos - rootJntPos
        limbDirOffset: MVector = vectorToEnd/2

        poleVectorDirOffset = poleVector * limbDirOffset.length()
        midIkCtrlPos = rootJntPos + limbDirOffset + poleVectorDirOffset

        midIkCtrlName = "ac_ik_" + midJnt
        mc.spaceLocator(n = midIkCtrlName)

        midIkCtrlGrpName = midIkCtrlName + "_grp"
        mc.group(midIkCtrlName, n=midIkCtrlGrpName)
        mc.move(midIkCtrlPos.x, midIkCtrlPos.y , midIkCtrlPos.z, midIkCtrlGrpName)

        mc.parent(ikHandleName, ikEndCtrlName)
        mc.poleVectorConstraint(midIkCtrlName, ikHandleName)
        mc.setAttr(ikHandleName+".v",0)
        
        return ikEndCtrlName, ikEndCtrlGrpName, midIkCtrlName, midIkCtrlGrpName, ikHandleName

        
    def ControllerSizeChanged(self, sliderVal):
        self.sizeDisplayLabel.setText(str(sliderVal))
        self.controllerSize = sliderVal

    @staticmethod
    def GetMayaMainWindow():
        mainWindow = omui.MQtUtil.mainWindow()
        return wrapInstance(int(mainWindow), QMainWindow)

    @staticmethod
    def GetWindowUniqueId():
        return "f5427cd524306a736fd3c14ff269072b"
def Run():
    LimbRiggingWidget().show()
