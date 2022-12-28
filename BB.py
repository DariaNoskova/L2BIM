
# Script for the usage of the CreateBridgeBeam function

import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
import NemAll_Python_Utility as AllplanUtil
import GeometryValidate as GeometryValidate

from StdReinfShapeBuilder.RotationAngles import RotationAngles
from HandleDirection import HandleDirection
from HandleProperties import HandleProperties
from HandleService import HandleService

print('Load BridgeBeam.py')


def check_allplan_version(build_ele, version):
    
    # Delete unused arguments
    del build_ele
    del version

    # Support all versions
    return True


def create_element(build_ele, doc):
    # Create Element
    element = CreateBridgeBeam(doc)

    # Return a tuple with elements list and handles list
    return element.create(build_ele)

def move_handle(build_ele, handle_prop, input_pnt, doc):
    # Change the handle properties
    build_ele.change_property(handle_prop, input_pnt)
    build_ele.RibHeight.value = build_ele.BeamHeight.value - build_ele.TopShHeight.value - build_ele.BotShLowHeight.value - build_ele.BotShUpHeight.value

    # Recreate element with new properties
    return create_element(build_ele, doc)

def modify_element_property(build_ele, name, value):
    # Handle dependencies for changed property
    # Return true/false for palette refresh
    print(name)
    if (name == "BeamHeight"):
        build_ele.RibHeight.value = value - build_ele.TopShHeight.value - build_ele.BotShUpHeight.value - build_ele.BotShLowHeight.value
    elif (name == "TopShHeight"):
        build_ele.BeamHeight.value = value + build_ele.RibHeight.value + build_ele.BotShUpHeight.value + build_ele.BotShLowHeight.value
    elif (name == "RibHeight"):
        build_ele.BeamHeight.value = value + build_ele.TopShHeight.value + build_ele.BotShUpHeight.value + build_ele.BotShLowHeight.value
    elif (name == "BotShUpHeight"):
        build_ele.BeamHeight.value = value + build_ele.TopShHeight.value + build_ele.RibHeight.value + build_ele.BotShLowHeight.value
    elif (name == "BotShLowHeight"):
        build_ele.BeamHeight.value = value + build_ele.TopShHeight.value + build_ele.RibHeight.value + build_ele.BotShUpHeight.value
    elif (name == "HoleHeight"):
        if (value > build_ele.BeamHeight.value - build_ele.TopShHeight.value):
            build_ele.HoleHeight.value = build_ele.BeamHeight.value - build_ele.TopShHeight.value - 45.5
        elif (value < build_ele.BotShLowHeight.value + build_ele.BotShUpHeight.value):
            build_ele.HoleHeight.value = build_ele.BotShLowHeight.value + build_ele.BotShUpHeight.value + 45.5
    elif (name == "HoleDepth"):
        if (value >= build_ele.BeamLength.value / 2.):
            build_ele.HoleDepth.value = build_ele.BeamLength.value / 2. - 45.5

    return True

class CreateBridgeBeam():

    def __init__(self, doc):

        self.model_ele_list = []
        self.handle_list = []
        self.document = doc
        
    def create(self, build_ele):
        
        self._top_sh_width = build_ele.TopShWidth.value
        self._top_sh_height = build_ele.TopShHeight.value

        self._bot_sh_width = build_ele.BotShWidth.value
        self._bot_sh_up_height = build_ele.BotShUpHeight.value
        self._bot_sh_low_height = build_ele.BotShLowHeight.value
        self._bot_sh_height = self._bot_sh_up_height + self._bot_sh_low_height

        if (build_ele.RibThick.value > min(self._top_sh_width, self._bot_sh_width)):
            build_ele.RibThick.value = min(self._top_sh_width, self._bot_sh_width)        
        self._rib_thickness = build_ele.RibThick.value
        self._rib_height = build_ele.RibHeight.value

        self._beam_length = build_ele.BeamLength.value
        self._beam_width = max(self._top_sh_width, self._bot_sh_width)
        self._beam_height = build_ele.BeamHeight.value

        self._hole_depth = build_ele.HoleDepth.value
        self._hole_height = build_ele.HoleHeight.value

        self._angleX = build_ele.RotationAngleX.value
        self._angleY = build_ele.RotationAngleY.value
        self._angleZ = build_ele.RotationAngleZ.value

        self.create_beam(build_ele)
        self.create_handles(build_ele)
        
        AllplanBaseElements.ElementTransform(AllplanGeo.Vector3D(), self._angleX, self._angleY, self._angleZ, self.model_ele_list)

        rot_angles = RotationAngles(self._angleX, self._angleY, self._angleZ)
        HandleService.transform_handles(self.handle_list, rot_angles.get_rotation_matrix())
        
        return (self.model_ele_list, self.handle_list)


    def create_beam(self, build_ele):
        com_prop = AllplanBaseElements.CommonProperties()
        com_prop.GetGlobalProperties()
        com_prop.Pen = 1
        com_prop.Color = build_ele.Color3.value
        com_prop.Stroke = 1

        # bottom shelf
        bottom_shelf = AllplanGeo.BRep3D.CreateCuboid(AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D((self._beam_width - self._bot_sh_width) / 2., 0., 0.), AllplanGeo.Vector3D(1, 0, 0), AllplanGeo.Vector3D(0, 0, 1)), self._bot_sh_width, self._beam_length, self._bot_sh_height)

        edges = AllplanUtil.VecSizeTList()
        edges.append(10)
        edges.append(8)
        err, bottom_shelf = AllplanGeo.ChamferCalculus.Calculate(bottom_shelf, edges, 20., False)
        
        # top shelf
        top_shelf = AllplanGeo.BRep3D.CreateCuboid(AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D((self._beam_width - self._top_sh_width) / 2., 0., self._beam_height - self._top_sh_height), AllplanGeo.Vector3D(1, 0, 0), AllplanGeo.Vector3D(0, 0, 1)), self._top_sh_width, self._beam_length, self._top_sh_height)

        top_shelf_notch = AllplanGeo.BRep3D.CreateCuboid(AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D((self._beam_width - self._top_sh_width) / 2., 0., self._beam_height - 45.), AllplanGeo.Vector3D(1, 0, 0), AllplanGeo.Vector3D(0, 0, 1)), 60., self._beam_length, 45.)
        err, top_shelf = AllplanGeo.MakeSubtraction(top_shelf, top_shelf_notch)
        if not GeometryValidate.polyhedron(err):
            return
        top_shelf_notch = AllplanGeo.Move(top_shelf_notch, AllplanGeo.Vector3D(self._top_sh_width - 60., 0, 0))
        err, top_shelf = AllplanGeo.MakeSubtraction(top_shelf, top_shelf_notch)
        if not GeometryValidate.polyhedron(err):
            return
        
        err, beam = AllplanGeo.MakeUnion(bottom_shelf, top_shelf)
        if not GeometryValidate.polyhedron(err):
            return

        # rib
        rib = AllplanGeo.BRep3D.CreateCuboid(AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D(0., 0., self._bot_sh_height), AllplanGeo.Vector3D(1, 0, 0), AllplanGeo.Vector3D(0, 0, 1)), self._beam_width, self._beam_length, self._rib_height)
        
        err, beam = AllplanGeo.MakeUnion(beam, rib)
        if not GeometryValidate.polyhedron(err):
            return
        
        # left and right notches
        left_notch_pol = AllplanGeo.Polygon2D()
        left_notch_pol += AllplanGeo.Point2D((self._beam_width - self._rib_thickness) / 2., self._beam_height - self._top_sh_height)
        left_notch_pol += AllplanGeo.Point2D((self._beam_width - self._rib_thickness) / 2., self._bot_sh_height)
        left_notch_pol += AllplanGeo.Point2D((self._beam_width - self._bot_sh_width) / 2., self._bot_sh_low_height)
        left_notch_pol += AllplanGeo.Point2D(0., self._bot_sh_low_height)     
        left_notch_pol += AllplanGeo.Point2D(0., self._beam_height - 100.)
        left_notch_pol += AllplanGeo.Point2D(0., self._beam_height - 100.)
        left_notch_pol += AllplanGeo.Point2D((self._beam_width - self._top_sh_width) / 2., self._beam_height - 100.)
        left_notch_pol += AllplanGeo.Point2D((self._beam_width - self._rib_thickness) / 2., self._beam_height - self._top_sh_height)
        if not GeometryValidate.is_valid(left_notch_pol):
            return
        
        path = AllplanGeo.Polyline3D()
        path += AllplanGeo.Point3D(0, 0, 0)
        path += AllplanGeo.Point3D(0, build_ele.BeamLength.value, 0)

        err, notches = AllplanGeo.CreatePolyhedron(left_notch_pol, AllplanGeo.Point2D(0., 0.), path)
        if GeometryValidate.polyhedron(err):
            edges = AllplanUtil.VecSizeTList()
            if (self._rib_thickness == self._bot_sh_width):
                edges.append(0)
            elif (self._rib_thickness == self._top_sh_width):
                edges.append(1)
            else:
                edges.append(0)
                edges.append(2)
            err, notches = AllplanGeo.FilletCalculus3D.Calculate(notches, edges, 100., False)

            plane = AllplanGeo.Plane3D(AllplanGeo.Point3D(self._beam_width / 2., 0, 0), AllplanGeo.Vector3D(1, 0, 0))
            right_notch = AllplanGeo.Mirror(notches, plane)

            err, notches = AllplanGeo.MakeUnion(notches, right_notch)
            if not GeometryValidate.polyhedron(err):
                return
            
            err, beam = AllplanGeo.MakeSubtraction(beam, notches)
            if not GeometryValidate.polyhedron(err):
                return

        # sling_holes
        sling_holes = AllplanGeo.BRep3D.CreateCylinder(AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D(0,build_ele.HoleDepth.value, build_ele.HoleHeight.value), AllplanGeo.Vector3D(0, 0, 1), AllplanGeo.Vector3D(1, 0, 0)), 45.5, self._beam_width)
        
        sling_hole_moved = AllplanGeo.Move(sling_holes, AllplanGeo.Vector3D(0., self._beam_length - self._hole_depth * 2, 0))

        err, sling_holes = AllplanGeo.MakeUnion(sling_holes, sling_hole_moved)
        if not GeometryValidate.polyhedron(err):
            return
            
        err, beam = AllplanGeo.MakeSubtraction(beam, sling_holes)
        if not GeometryValidate.polyhedron(err):
            return 

        # result beam
        
        self.model_ele_list.append(AllplanBasisElements.ModelElement3D(com_prop, beam))
        

    def create_handles(self, build_ele):
        
        #------------------ Define handles
        origin = AllplanGeo.Point3D(0, 0, 0)

        point1 = AllplanGeo.Point3D(0., self._beam_length, 0.)
        handle1 = HandleProperties("BeamLength", point1, origin,
                                   [("BeamLength", HandleDirection.y_dir)],
                                   HandleDirection.y_dir, True)
        self.handle_list.append(handle1)

        point2 = AllplanGeo.Point3D(0., 0., self._beam_height)
        handle2 = HandleProperties("BeamHeight", point2, origin,
                                   [("BeamHeight", HandleDirection.z_dir)],
                                   HandleDirection.z_dir, True)
        self.handle_list.append(handle2)
        
        point3 = AllplanGeo.Point3D(self._beam_width - (self._beam_width - self._top_sh_width) / 2., 0., self._beam_height - 45.)
        origin3 = AllplanGeo.Point3D((self._beam_width - self._top_sh_width) / 2., 0, 0)
        handle3 = HandleProperties("TopShWidth", point3, origin3,
                                   [("TopShWidth", HandleDirection.x_dir)],
                                   HandleDirection.x_dir, True)
        self.handle_list.append(handle3)

        point4 = AllplanGeo.Point3D(self._beam_width - (self._beam_width - self._bot_sh_width) / 2., 0., self._bot_sh_low_height)
        origin4 = AllplanGeo.Point3D((self._beam_width - self._bot_sh_width) / 2., 0, 0)
        handle4 = HandleProperties("BotShWidth", point4, origin4,
                                   [("BotShWidth", HandleDirection.x_dir)],
                                   HandleDirection.x_dir, True)
        self.handle_list.append(handle4)
        
        point5 = AllplanGeo.Point3D(self._beam_width - (self._beam_width - self._rib_thickness) / 2., 0., self._beam_height / 2.)
        origin5 = AllplanGeo.Point3D((self._beam_width - self._rib_thickness) / 2., 0, 0)
        handle5 = HandleProperties("RibThick", point5, origin5,
                                   [("RibThick", HandleDirection.x_dir)],
                                   HandleDirection.x_dir, True)
        self.handle_list.append(handle5)

        