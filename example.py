import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
import NemAll_Python_Utility as AllplanUtil
import GeometryValidate as GeometryValidate

from StdReinfShapeBuilder.RotationAngles import RotationAngles
from HandleDirection import HandleDirection
from HandleProperties import HandleProperties
from HandleService import HandleService

def check_allplan_version(build_ele, version):
    del build_ele
    del version
    return True

def create_element(build_ele, doc):
    element = CreateBridgeBeam(doc)
    return element.create(build_ele)

def move_handle(build_ele, handle_prop, input_pnt, doc):
    build_ele.change_property(handle_prop, input_pnt)
    return create_element(build_ele, doc)

def modify_element_property(build_ele, name, value):
    if (name == "beam_height"):
        build_ele.edge_height.value = value - build_ele.top_shelf_height.value - build_ele.bottom_shelf_up_height.value - build_ele.bottom_shelf_low_height.value
    elif (name == "top_shelf_height"):
        build_ele.beam_height.value = value + build_ele.edge_height.value + build_ele.bottom_shelf_up_height.value + build_ele.bottom_shelf_low_height.value
    elif (name == "edge_height"):
        build_ele.beam_height.value = value + build_ele.top_shelf_height.value + build_ele.bottom_shelf_up_height.value + build_ele.bottom_shelf_low_height.value
    elif (name == "bottom_shelf_up_height"):
        build_ele.beam_height.value = value + build_ele.top_shelf_height.value + build_ele.edge_height.value + build_ele.bottom_shelf_low_height.value
    elif (name == "bottom_shelf_low_height"):
        build_ele.beam_height.value = value + build_ele.top_shelf_height.value + build_ele.edge_height.value + build_ele.bottom_shelf_up_height.value
    elif (name == "hole_height"):
        if (value > build_ele.beam_height.value - build_ele.top_shelf_height.value):
            build_ele.hole_height.value = build_ele.beam_height.value - build_ele.top_shelf_height.value - 45.5
        elif (value < build_ele.bottom_shelf_low_height.value + build_ele.bottom_shelf_up_height.value):
            build_ele.hole_height.value = build_ele.bottom_shelf_low_height.value + build_ele.bottom_shelf_up_height.value + 45.5
    elif (name == "hole_depth"):
        if (value >= build_ele.beam_length.value / 2.):
            build_ele.hole_depth.value = build_ele.beam_length.value / 2. - 45.5

    return True


class CreateBridgeBeam():

    def __init__(self, doc):
        self.model_ele_list = []
        self.handle_list = []
        self.document = doc
        

    def create(self, build_ele):
        # Верхня полиця
        self._top_shelf_width = build_ele.top_shelf_width.value
        self._top_shelf_height = build_ele.top_shelf_height.value

        # Нижня полиця
        self._bottom_shelf_width = build_ele.bottom_shelf_width.value
        self._bottom_shelf_up_height = build_ele.bottom_shelf_up_height.value
        self._bottom_shelf_low_height = build_ele.bottom_shelf_low_height.value
        self._bottom_shelf_height = self._bottom_shelf_up_height + self._bottom_shelf_low_height

        # Ребро
        if (build_ele.edge_thickness.value > min(self._top_shelf_width, self._bottom_shelf_width)):
            build_ele.edge_thickness.value = min(self._top_shelf_width, self._bottom_shelf_width)        
        self._edge_thickness = build_ele.edge_thickness.value
        self._edge_height = build_ele.edge_height.value

        # Балка
        self._beam_length = build_ele.beam_length.value
        self._beam_width = max(self._top_shelf_width, self._bottom_shelf_width)
        self._beam_height = build_ele.beam_height.value

        # Отвір
        self._hole_depth = build_ele.hole_depth.value
        self._hole_height = build_ele.hole_height.value

        # Кути для повороту
        self._angle_x = build_ele.rotation_angle_x.value
        self._angle_y = build_ele.rotation_angle_y.value
        self._angle_z = build_ele.rotation_angle_z.value

        self.create_beam(build_ele)
        self.create_handles(build_ele)
        
        AllplanBaseElements.ElementTransform(AllplanGeo.Vector3D(), self._angle_x, self._angle_y, self._angle_z, self.model_ele_list)

        rot_angles = RotationAngles(self._angle_x, self._angle_y, self._angle_z)
        HandleService.transform_handles(self.handle_list, rot_angles.get_rotation_matrix())
        
        return (self.model_ele_list, self.handle_list)


    def create_beam(self, build_ele):
        common_properties = AllplanBaseElements.CommonProperties()
        common_properties.GetGlobalProperties()
        common_properties.Pen = 1
        common_properties.Stroke = 1


        # Створення верхньої полиці
        top_shelf = AllplanGeo.BRep3D.CreateCuboid(AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D((self._beam_width - self._top_shelf_width) / 2., 0., self._beam_height - self._top_shelf_height), AllplanGeo.Vector3D(1, 0, 0), AllplanGeo.Vector3D(0, 0, 1)), self._top_shelf_width, self._beam_length, self._top_shelf_height)

        top_shelf_notch = AllplanGeo.BRep3D.CreateCuboid(AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D((self._beam_width - self._top_shelf_width) / 2., 0., self._beam_height - 45.), AllplanGeo.Vector3D(1, 0, 0), AllplanGeo.Vector3D(0, 0, 1)), 60., self._beam_length, 45.)
        err, top_shelf = AllplanGeo.MakeSubtraction(top_shelf, top_shelf_notch)
        if not GeometryValidate.polyhedron(err):
            return

        top_shelf_notch = AllplanGeo.Move(top_shelf_notch, AllplanGeo.Vector3D(self._top_shelf_width - 60., 0, 0))
        err, top_shelf = AllplanGeo.MakeSubtraction(top_shelf, top_shelf_notch)
        if not GeometryValidate.polyhedron(err):
            return
        

        # Створення нижньої полиці
        bottom_shelf = AllplanGeo.BRep3D.CreateCuboid(AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D((self._beam_width - self._bottom_shelf_width) / 2., 0., 0.), AllplanGeo.Vector3D(1, 0, 0), AllplanGeo.Vector3D(0, 0, 1)), self._bottom_shelf_width, self._beam_length, self._bottom_shelf_height)

        edges = AllplanUtil.VecSizeTList()
        edges.append(10)
        edges.append(8)
        err, bottom_shelf = AllplanGeo.ChamferCalculus.Calculate(bottom_shelf, edges, 20., False)
        

        # Обєднання верхньої та нижньої полиці
        err, beam = AllplanGeo.MakeUnion(bottom_shelf, top_shelf)
        if not GeometryValidate.polyhedron(err):
            return

        # Створення ребра
        rib = AllplanGeo.BRep3D.CreateCuboid(AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D(0., 0., self._bottom_shelf_height), AllplanGeo.Vector3D(1, 0, 0), AllplanGeo.Vector3D(0, 0, 1)), self._beam_width, self._beam_length, self._edge_height)
        

        # Обєднання ребра з полицями
        err, beam = AllplanGeo.MakeUnion(beam, rib)
        if not GeometryValidate.polyhedron(err):
            return
        
        # Створення лівих заокруглень
        left_notch_pol = AllplanGeo.Polygon2D()
        left_notch_pol += AllplanGeo.Point2D((self._beam_width - self._edge_thickness) / 2., self._beam_height - self._top_shelf_height)
        left_notch_pol += AllplanGeo.Point2D((self._beam_width - self._edge_thickness) / 2., self._bottom_shelf_height)
        left_notch_pol += AllplanGeo.Point2D((self._beam_width - self._bottom_shelf_width) / 2., self._bottom_shelf_low_height)
        left_notch_pol += AllplanGeo.Point2D(0., self._bottom_shelf_low_height)     
        left_notch_pol += AllplanGeo.Point2D(0., self._beam_height - 100.)
        left_notch_pol += AllplanGeo.Point2D(0., self._beam_height - 100.)
        left_notch_pol += AllplanGeo.Point2D((self._beam_width - self._top_shelf_width) / 2., self._beam_height - 100.)
        left_notch_pol += AllplanGeo.Point2D((self._beam_width - self._edge_thickness) / 2., self._beam_height - self._top_shelf_height)
        if not GeometryValidate.is_valid(left_notch_pol):
            return
        
        # Cтворення лінії довжини
        beam_length_pol = AllplanGeo.Polyline3D()
        beam_length_pol += AllplanGeo.Point3D(0, 0, 0)
        beam_length_pol += AllplanGeo.Point3D(0, build_ele.beam_length.value, 0)

        # Об'єднання довжини з заокругленнями
        
        err, notches = AllplanGeo.CreatePolyhedron(left_notch_pol, AllplanGeo.Point2D(0., 0.), beam_length_pol)
        
        if GeometryValidate.polyhedron(err):
            edges = AllplanUtil.VecSizeTList()
            if (self._edge_thickness == self._bottom_shelf_width):
                edges.append(0)
            elif (self._edge_thickness == self._top_shelf_width):
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
        
        
        # Створення отвору
        sling_hole = AllplanGeo.BRep3D.CreateCylinder(AllplanGeo.AxisPlacement3D(AllplanGeo.Point3D(0,build_ele.hole_depth.value, build_ele.hole_height.value), AllplanGeo.Vector3D(0, 0, 1), AllplanGeo.Vector3D(1, 0, 0)), 45.5, self._beam_width)
        
        # Створення отвору на протилежній стороні
        sling_hole_mirror = AllplanGeo.Move(sling_hole, AllplanGeo.Vector3D(0., self._beam_length - self._hole_depth * 2, 0))
            
        # Додавання отворів до балки
        err, beam = AllplanGeo.MakeSubtraction(beam, sling_hole)
        if not GeometryValidate.polyhedron(err):
            return 
        
        err, beam = AllplanGeo.MakeSubtraction(beam, sling_hole_mirror)
        if not GeometryValidate.polyhedron(err):
            return 


        self.model_ele_list.append(AllplanBasisElements.ModelElement3D(common_properties, beam))
        

    def create_handles(self, build_ele):
        # Створення ручок
        origin = AllplanGeo.Point3D(0, 0, 0)

        # Нажаль я не зміг налаштувати декілька ручок(
        point1 = AllplanGeo.Point3D(0, self._beam_length, 0)
        handle1 = HandleProperties("beam_length", point1, origin,
                                   [("beam_length", HandleDirection.y_dir)],
                                   HandleDirection.y_dir, True)
        self.handle_list.append(handle1)
        

        point2 = AllplanGeo.Point3D(0., 0., self._beam_height)
        handle2 = HandleProperties("beam_height", point2, origin,
                                  [("beam_height", HandleDirection.z_dir)],
                                  HandleDirection.z_dir, True)
        self.handle_list.append(handle2)
        
        point3 = AllplanGeo.Point3D(self._beam_width - (self._beam_width - self._top_shelf_width) / 2., 0., self._beam_height - 45.)
        origin3 = AllplanGeo.Point3D((self._beam_width - self._top_shelf_width) / 2., 0, 0)
        handle3 = HandleProperties("top_shelf_width", point3, origin3,
                                   [("top_shelf_width", HandleDirection.x_dir)],
                                   HandleDirection.x_dir, True)
        self.handle_list.append(handle3)

        point4 = AllplanGeo.Point3D(self._beam_width - (self._beam_width - self._bottom_shelf_width) / 2., 0., self._bottom_shelf_low_height)
        origin4 = AllplanGeo.Point3D((self._beam_width - self._bottom_shelf_width) / 2., 0, 0)
        handle4 = HandleProperties("bottom_shelf_width", point4, origin4,
                                   [("bottom_shelf_width", HandleDirection.x_dir)],
                                   HandleDirection.x_dir, True)
        self.handle_list.append(handle4)
        
        point5 = AllplanGeo.Point3D(self._beam_width - (self._beam_width - self._edge_thickness) / 2., 0., self._beam_height / 2.)
        origin5 = AllplanGeo.Point3D((self._beam_width - self._edge_thickness) / 2., 0, 0)
        handle5 = HandleProperties("edge_thickness", point5, origin5,
                                   [("edge_thickness", HandleDirection.x_dir)],
                                   HandleDirection.x_dir, True)
        self.handle_list.append(handle5)

        