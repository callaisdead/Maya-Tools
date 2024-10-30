import maya.cmds as mc
import maya.mel as mel
import maya.cmds as cmds
from maya.OpenMaya import MVector
import maya.OpenMayaUI as omui #omui = open maya ui
from PySide2.QtWidgets import QVBoxLayout, QWidget, QPushButton, QMainWindow, QHBoxLayout, QGridLayout, QLineEdit, QLabel, QSlider
from PySide2.QtCore import Qt
from shiboken2 import wrapInstance

class TrimSheetBuilderWidget(QWidget):
    def __init__(self):
        mainWindow: QMainWindow = TrimSheetBuilderWidget.GetMayaMainWindow()
        
        for exisiting in mainWindow.findChildren(QWidget, TrimSheetBuilderWidget.GetWindowUniqueId()):
            exisiting.deleteLater()
        
        super().__init__(parent=mainWindow)
        self.setWindowTitle("Trim Sheet Builder")
        self.setWindowFlags(Qt.Window)
        self.setObjectName(TrimSheetBuilderWidget.GetWindowUniqueId())

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.shell = []
        self.CreateInitializationSection()
        self.CreateManipulationSection()

    def CreateManipulationSection(self):
        sectionLayout = QGridLayout()
        self.masterLayout.addLayout(sectionLayout)

        turnBtn = QPushButton("Turn")
        turnBtn.clicked.connect(self.TurnShell)
        sectionLayout.addWidget(turnBtn)

        backtoOrginBtn = QPushButton("Back to Origin")
        backtoOrginBtn.clicked.connect(self.MoveShellToOrigin)
        sectionLayout.addWidget(backtoOrginBtn)

    def GetShellBound(self):
        uvs = mc.polyListComponentConversion(self.shell, toUV=True)
        uvs = mc.ls(uvs, fl=True)
        firstUV = mc.polyEditUV(uvs[0], q=True)
        minU = firstUV[0]
        maxU = firstUV[0]
        minV = firstUV[1]
        maxV = firstUV[1]

        for uv in uvs:
            uvCoord = mc.polyEditUV(uv, q=True)
            if uvCoord[0] < minU :
                minU = uvCoord[0]
            if uvCoord[0] > maxU:
                maxU = uvCoord[0]
            if uvCoord[1] < minV:
                minV = uvCoord[1]
            if uvCoord[1] > maxV:
                maxV = uvCoord[1]

        return[minU, minV], [maxU, maxV]
  
    def MoveShellToOrigin(self):
        minCoord, maxCoord = self.GetShellBound()
        mc.polyEditUV(self.shell, u=-minCoord[0], v=-minCoord[1])

    def TurnShell(self):
        mc.select(self.shell, r=True)
        mel.eval(f"polyRotateUVs 90 0")



    def CreateInitializationSection(self): #UI
        sectionLayout = QHBoxLayout()
        self.masterLayout.addLayout(sectionLayout)

        selectShellBtn = QPushButton("Select Shell")
        selectShellBtn.clicked.connect(self.SelectShell)
        sectionLayout.addWidget(selectShellBtn)

        unfoldBtn = QPushButton("Unfold")
        unfoldBtn.clicked.connect(self.UnfoldShell)
        sectionLayout.addWidget(unfoldBtn)
        
        cutAndUnfoldBtn = QPushButton("Cut and Unfold")
        cutAndUnfoldBtn.clicked.connect(self.CutandUnfoldShell)
        sectionLayout.addWidget(cutAndUnfoldBtn)

        unitizeBtn = QPushButton("Unitize")
        unitizeBtn.clicked.connect(self.UnitizeShell)
        sectionLayout.addWidget(unitizeBtn)

    def UnitizeShell(self):
        edges = mc.polyListComponentConversion(self.shell, toEdge=True)
        edges = mc.ls(edges, fl=True)

        sewedEdges = []
        for edge in edges:
            vertices = mc.polyListComponentConversion(edge, toVertex=True)
            vertices = mc.ls(vertices, fl=True)
            UVs = mc.polyListComponentConversion(edge, toUV=True)
            UVs = mc.ls(UVs, fl=True)

            if len(UVs) == len(vertices):
                sewedEdges.append(edge)

        mc.polyForceUV(self.shell, unitize=True)
        mc.polyMapSewMove(sewedEdges)
        mc.u3dLayout(self.shell)

    def CutandUnfoldShell(self):
        edges = mc.ls(sl=True)
        mc.polyProjection(self.shell, type="Planer", md="c")
        mc.polyMapCut(edges)
        mc.u3dUnfold(self.shell)
        mel.eval("textOrientShells")


    def UnfoldShell(self):
        mc.polyProjection(self.shell, type="Planer", md="c")
        mc.u3dUnfold(self.shell)
        mel.eval("textOrientShells")
        
    def SelectShell(self):
        self.shell = mc.ls(sl=True, fl=True)

    @staticmethod
    def GetMayaMainWindow():
        mainWindow = omui.MQtUtil.mainWindow()
        return wrapInstance(int(mainWindow), QMainWindow)

    @staticmethod
    def GetWindowUniqueId():
        return "f5426cd524306a736fd3c54ff269072b"
    
TrimSheetBuilderWidget().show()
