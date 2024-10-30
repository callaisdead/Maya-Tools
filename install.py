import os
import shutil
import maya.cmds as mc

def Run():
    projDir = os.path.dirname(os.path.abspath(__file__))
    mayaSciptPath = os.path.join(mc.internalVar(uad = True), "scripts")
    pluginName = os.path.split(projDir)[-1]

    pluginDestPath = os.path.join(mayaSciptPath, pluginName)

    if os.path.exists(pluginDestPath):
        shutil.rmtree(pluginDestPath)
    
    os.makedirs(pluginDestPath, exist_ok=True)

    srcDirName = "src"
    assetsDirName = "assets"

    shutil.copytree(os.path.join(projDir, srcDirName), os.path.join(pluginDestPath, srcDirName))
    shutil.copytree(os.path.join(projDir, assetsDirName), os.path.join(pluginDestPath, assetsDirName))

    def CreatesShelfBtnForScript(scriptName):
        currentShelf = mc.tabLayout("ShelfLayout",q=True, selectTab=True)
        mc.setParent(currentShelf)
        iconImage = os.path.join(pluginDestPath, assetsDirName, scriptName + ".png")
        mc.shelfButton(c=f"from {pluginName}.src import {scriptName}; {scriptName}.Run()", image = iconImage)

    CreatesShelfBtnForScript("limbRiggingTool")
    CreatesShelfBtnForScript("trimSheetUVBuilder")
