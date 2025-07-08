import cadquery as cq
from cadquery.occ_impl.assembly import toCAF

from typing import List, Union
from importlib import reload
from types import SimpleNamespace
import OCC
from OCC.Core.XCAFPrs import XCAFPrs_AISObject
from OCC.Core.TopoDS import topods, TopoDS_Shape, TopoDS_Compound
from OCC.Core.AIS import AIS_InteractiveObject, AIS_Shape
from OCC.Core.Quantity import Quantity_Color, Quantity_NOC_GOLD, Quantity_TOC_RGB
from OCC.Core.Graphic3d import Graphic3d_NOM_JADE, Graphic3d_MaterialAspect

from PySide6.QtGui import QColor

DEFAULT_FACE_COLOR = Quantity_Color(Quantity_NOC_GOLD)
DEFAULT_MATERIAL = Graphic3d_MaterialAspect(Graphic3d_NOM_JADE)


def is_cq_obj(obj):

    from cadquery import Workplane, Shape, Assembly, Sketch

    return isinstance(obj, (Workplane, Shape, Assembly, Sketch))


def find_cq_objects(results: dict):

    return {
        k: SimpleNamespace(shape=v, options={})
        for k, v in results.items()
        if is_cq_obj(v)
    }


def to_compound(obj):
    vals = []

    if isinstance(obj, cq.Workplane):
        vals.extend(obj.vals())
    elif isinstance(obj, cq.Shape):
        vals.append(obj)
    elif isinstance(obj, list) and isinstance(obj[0], cq.Workplane):
        for o in obj:
            vals.extend(o.vals())
    elif isinstance(obj, list) and isinstance(obj[0], cq.Shape):
        vals.extend(obj)
    elif isinstance(obj, OCC.Core.TopoDS.TopoDS_Shape):  # 这里改成OCC
        # 如果直接是TopoDS_Shape，转换成cadquery.Shape
        vals.append(cq.Shape.cast(obj))
    elif isinstance(obj, list) and isinstance(obj[0], OCC.Core.TopoDS.TopoDS_Shape):
        vals.extend(cq.Shape.cast(o) for o in obj)
    elif isinstance(obj, cq.Sketch):
        if obj._faces:
            vals.append(obj._faces)
        else:
            vals.extend(obj._edges)
    else:
        raise ValueError(f"Invalid type {type(obj)}")

    compound = cq.Compound.makeCompound(vals)
    # 返回cadquery.Shape
    if compound is None or compound.wrapped is None:
        raise ValueError("Invalid compound shape")
    return compound


def to_workplane(obj: cq.Shape):

    rv = cq.Workplane("XY")
    rv.objects = [
        obj,
    ]

    return rv


from OCC.Core.TopoDS import topods, TopoDS_Shape, TopoDS_Compound

def make_AIS(
    obj: Union[
        cq.Workplane,
        List[cq.Workplane],
        cq.Shape,
        List[cq.Shape],
        cq.Assembly,
        AIS_InteractiveObject,
    ],
    options={},
):
    shape = None

    if isinstance(obj, cq.Assembly):
        obj = obj.val()
        label, shape = toCAF(obj)
        ais = XCAFPrs_AISObject(label)

    elif isinstance(obj, AIS_InteractiveObject):
        ais = obj

    else:
        try:
            shape = to_compound(obj)
        except Exception as e:
            raise ValueError(f"[make_AIS] Failed to convert to compound: {e}")

        if shape is None or shape.wrapped is None:
            raise ValueError(f"Invalid shape or empty shape: {shape}")

        # 强制类型转换：从 cadquery.Shape 转换为 OCC.Core.TopoDS_Shape
        base_shape = shape.wrapped

        # 确保 wrapped 是 TopoDS_Shape 类型（处理 OCP 类型兼容性）
        try:
            base_shape = cq.Shape.cast(base_shape).wrapped
        except Exception as e:
            raise TypeError(f"[make_AIS] Invalid wrapped type after cast: {type(base_shape)}\nError: {e}")

        try:
            ais = AIS_Shape(base_shape)
        except Exception as e:
            raise RuntimeError(f"[make_AIS] Failed to create AIS_Shape: {e}")

    # 设置属性
    try:
        set_material(ais, DEFAULT_MATERIAL)
        set_color(ais, DEFAULT_FACE_COLOR)
    except Exception as e:
        print("[make_AIS] Warning: Failed to set material or color:", e)

    # 附加选项
    if "alpha" in options:
        set_transparency(ais, options["alpha"])
    if "color" in options:
        set_color(ais, to_occ_color(options["color"]))
    if "rgba" in options:
        r, g, b, a = options["rgba"]
        set_color(ais, to_occ_color((r, g, b)))
        set_transparency(ais, a)

    return ais, shape


def export(
    obj: Union[cq.Workplane, List[cq.Workplane]], type: str, file, precision=1e-1
):

    comp = to_compound(obj)

    if type == "stl":
        comp.exportStl(file, tolerance=precision)
    elif type == "step":
        comp.exportStep(file)
    elif type == "brep":
        comp.exportBrep(file)


def to_occ_color(color) -> Quantity_Color:

    if not isinstance(color, QColor):
        if isinstance(color, tuple):
            if isinstance(color[0], int):
                color = QColor(*color)
            elif isinstance(color[0], float):
                color = QColor.fromRgbF(*color)
            else:
                raise ValueError("Unknown color format")
        else:
            color = QColor(color)

    return Quantity_Color(color.redF(), color.greenF(), color.blueF(), Quantity_TOC_RGB)


def get_occ_color(obj: Union[AIS_InteractiveObject, Quantity_Color]) -> QColor:

    if isinstance(obj, AIS_InteractiveObject):
        color = Quantity_Color()
        obj.Color(color)
    else:
        color = obj

    return QColor.fromRgbF(color.Red(), color.Green(), color.Blue())


def set_color(ais: AIS_Shape, color: Quantity_Color) -> AIS_Shape:

    drawer = ais.Attributes()
    drawer.SetupOwnShadingAspect()
    drawer.ShadingAspect().SetColor(color)

    return ais


def set_material(ais: AIS_Shape, material: Graphic3d_MaterialAspect) -> AIS_Shape:

    drawer = ais.Attributes()
    drawer.SetupOwnShadingAspect()
    drawer.ShadingAspect().SetMaterial(material)

    return ais


def set_transparency(ais: AIS_Shape, alpha: float) -> AIS_Shape:

    drawer = ais.Attributes()
    drawer.SetupOwnShadingAspect()
    drawer.ShadingAspect().SetTransparency(1.0 - alpha)

    return ais


def reload_cq():

    # NB: order of reloads is important
    reload(cq.types)
    reload(cq.occ_impl.geom)
    reload(cq.occ_impl.shapes)
    reload(cq.occ_impl.shapes)
    reload(cq.occ_impl.importers.dxf)
    reload(cq.occ_impl.importers)
    reload(cq.occ_impl.solver)
    reload(cq.occ_impl.assembly)
    reload(cq.occ_impl.sketch_solver)
    reload(cq.hull)
    reload(cq.selectors)
    reload(cq.sketch)
    reload(cq.occ_impl.exporters.svg)
    reload(cq.cq)
    reload(cq.occ_impl.exporters.dxf)
    reload(cq.occ_impl.exporters.amf)
    reload(cq.occ_impl.exporters.json)
    # reload(cq.occ_impl.exporters.assembly)
    reload(cq.occ_impl.exporters)
    reload(cq.assembly)
    reload(cq)


def is_obj_empty(obj: Union[cq.Workplane, cq.Shape]) -> bool:

    rv = False

    if isinstance(obj, cq.Workplane):
        rv = True if isinstance(obj.val(), cq.Vector) else False

    return rv
