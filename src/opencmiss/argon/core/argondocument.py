"""
   Copyright 2015 University of Auckland

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import json

from opencmiss.argon.core.argonsceneviewer import ArgonSceneviewer
from opencmiss.argon.core.argonregion import ArgonRegion
from opencmiss.argon.core.argonspectrums import ArgonSpectrums
from opencmiss.argon.core.argonmaterials import ArgonMaterials
from opencmiss.argon.core.argontessellations import ArgonTessellations
from opencmiss.argon.core.argonerror import ArgonError
from opencmiss.argon.core.argonlogger import ArgonLogger
from opencmiss.argon.settings import mainsettings
from opencmiss.zinc.context import Context
from opencmiss.zinc.material import Material


class ArgonDocument(object):

    def __init__(self):
        self._zincContext = None
        self._rootRegion = None
        self._spectrums = None
        self._materials = None
        self._tessellations = None
        self._sceneviewer = None

    def initialiseVisualisationContents(self):
        self._zincContext = Context("Argon")

        sceneviewermodule = self._zincContext.getSceneviewermodule()
        sceneviewermodule.setDefaultBackgroundColourRGB([1.0, 1.0, 1.0])

        # set up standard materials and glyphs
        materialmodule = self._zincContext.getMaterialmodule()
        materialmodule.beginChange()
        materialmodule.defineStandardMaterials()
        # make default material black
        defaultMaterial = materialmodule.getDefaultMaterial()
        defaultMaterial.setAttributeReal3(Material.ATTRIBUTE_AMBIENT, [0.0, 0.0, 0.0])
        defaultMaterial.setAttributeReal3(Material.ATTRIBUTE_DIFFUSE, [0.0, 0.0, 0.0])
        # still want surfaces to default to white material
        white = materialmodule.findMaterialByName("white")
        materialmodule.setDefaultSurfaceMaterial(white)
        materialmodule.endChange()
        glyphmodule = self._zincContext.getGlyphmodule()
        glyphmodule.defineStandardGlyphs()

        zincRootRegion = self._zincContext.getDefaultRegion()
        self._rootRegion = ArgonRegion(name=None, zincRegion=zincRootRegion, parent=None)
        self._rootRegion.connectRegionChange(self._regionChange)

        self._materials = materialmodule
        self._spectrums = ArgonSpectrums(self._zincContext)
        self._materials = ArgonMaterials(self._zincContext)
        self._tessellations = ArgonTessellations(self._zincContext)
        self._sceneviewer = ArgonSceneviewer(self._zincContext)
        ArgonLogger.setZincContext(self._zincContext)

    def freeVisualisationContents(self):
        """
        Deletes subobjects of document to help free memory held by Zinc objects earlier.
        """
        self._rootRegion.freeContents()
        del self._sceneviewer
        del self._tessellations
        del self._spectrums
        del self._materials
        del self._rootRegion
        del self._zincContext

    def _regionChange(self, changedRegion, treeChange):
        """
        If root region has changed, set its new Zinc region as Zinc context's default region.
        :param changedRegion: The top region changed
        :param treeChange: True if structure of tree, or zinc objects reconstructed
        """
        if treeChange and (changedRegion is self._rootRegion):
            zincRootRegion = changedRegion.getZincRegion()
            self._zincContext.setDefaultRegion(zincRootRegion)

    def deserialize(self, state):
        """
        :param  state: string serialisation of Argon JSON document
        """
        d = json.loads(state)
        if not (("OpenCMISS-Argon Version" in d) and ("RootRegion" in d)):
            raise ArgonError("Invalid Argon document")
        argon_version = d["OpenCMISS-Argon Version"]
        if argon_version > mainsettings.VERSION_LIST:
            raise ArgonError("Document version is greater than this version of Argon (" + mainsettings.VERSION_STRING + "). Please update your Argon application.")
        # Ideally would enclose following in:
        # try: zincRegion.beginHierarchicalChange() ... finally: zincRegion.endHierarchicalChange()
        # Can't do this due to Zinc issue 3924 which prevents computed field wrappers being created, so graphics can't find fields
        if "Tessellations" in d:
            self._tessellations.deserialize(d["Tessellations"])
        if "Spectrums" in d:
            self._spectrums.deserialize(d["Spectrums"])
        if "Materials" in d:
            self._materials.deserialize(d["Materials"])
        if "Sceneviewer" in d:
            self._sceneviewer.deserialize(d["Sceneviewer"])
        if "Materials" in d:
            self._materials.deserialize(d["Materials"])
        self._rootRegion.deserialize(d["RootRegion"])

    def serialize(self, basePath=None):
        dictOutput = {
            "OpenCMISS-Argon Version": mainsettings.VERSION_LIST,
            "Spectrums": self._spectrums.serialize(),
            "Materials": self._materials.serialize(),
            "Tessellations": self._tessellations.serialize(),
            "RootRegion": self._rootRegion.serialize(basePath),
            "Sceneviewer": self._sceneviewer.serialize()
        }
        return json.dumps(dictOutput, default=lambda o: o.__dict__, sort_keys=True, indent=2)

    def getZincContext(self):
        return self._zincContext

    def getRootRegion(self):
        return self._rootRegion

    def getSpectrums(self):
        return self._spectrums

    def getMaterials(self):
        return self._materials

    def getTessellations(self):
        return self._tessellations

    def getSceneviewer(self):
        return self._sceneviewer