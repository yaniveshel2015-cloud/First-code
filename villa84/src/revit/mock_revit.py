"""Run villa84_build.py against a small fake of the Revit / Dynamo API, to catch Python errors before it reaches Revit.

  python mock_revit.py villa84_build.py villa84-revit-data.json [--with-families]
Prints the script's report and a count of the fake API calls.
"""
import math
import sys
import types

CALLS = {}
REG = []


def call(name):
    CALLS[name] = CALLS.get(name, 0) + 1


class Anything:
    """Permissive stand-in: any attribute, call, index or number operation works and returns another stand-in."""

    def __init__(self, name="x"):
        self._n = name

    def __getattr__(self, k):
        if k.startswith("__"):
            raise AttributeError(k)
        return Anything(self._n + "." + k)

    def __call__(self, *a, **k):
        call(self._n)
        return Anything(self._n + "()")

    def __iter__(self):
        return iter([])

    def __bool__(self):
        return True

    def __float__(self):
        return 0.0

    def __lt__(self, o):
        return False

    __gt__ = __le__ = __ge__ = __lt__

    def __sub__(self, o):
        return 0.0

    __add__ = __mul__ = __truediv__ = __rsub__ = __radd__ = __rmul__ = __sub__

    def __getitem__(self, k):
        return Anything(self._n + "[]")


class EnumNS:
    def __init__(self, name):
        self._n = name

    def __getattr__(self, k):
        if k.startswith("__"):
            raise AttributeError(k)
        return self._n + "." + k


class EId:
    _next = [1000]

    def __init__(self, v=None):
        if v is None:
            EId._next[0] += 1
            v = EId._next[0]
        self.v = v

    def Equals(self, o):
        return isinstance(o, EId) and o.v == self.v

    def __eq__(self, o):
        return self.Equals(o)

    def __hash__(self):
        return hash(str(self.v))

    def ToString(self):
        return str(self.v)

    InvalidElementId = None


EId.InvalidElementId = EId(-1)


class XYZ:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.X, self.Y, self.Z = float(x), float(y), float(z)

    def DotProduct(self, o):
        return self.X * o.X + self.Y * o.Y + self.Z * o.Z

    def CrossProduct(self, o):
        return XYZ(self.Y * o.Z - self.Z * o.Y, self.Z * o.X - self.X * o.Z, self.X * o.Y - self.Y * o.X)


XYZ.Zero = XYZ()
XYZ.BasisZ = XYZ(0, 0, 1)


class UV:
    def __init__(self, u, v):
        self.U, self.V = u, v


class Param:
    IsReadOnly = False

    def __init__(self, name="p"):
        self.Definition = types.SimpleNamespace(Name=name)

    def Set(self, v):
        call("Parameter.Set")
        return True


class Element:
    def __init__(self, cls, **kw):
        self.Id = EId()
        self.Name = kw.pop("Name", cls + str(self.Id.v))
        self._cls = cls
        self.__dict__.update(kw)
        REG.append(self)

    def get_Parameter(self, bip):
        return Param(str(bip))

    @property
    def Parameters(self):
        return [Param("Width"), Param("Height")]

    def Duplicate(self, name):
        call(self._cls + ".Duplicate")
        e = Element(self._cls, Name=name, **{k: v for k, v in self.__dict__.items() if k not in ("Id", "Name", "_cls")})
        return e

    def SetCompoundStructure(self, cs):
        call(self._cls + ".SetCompoundStructure")

    def GetPlaneReference(self):
        return "ref:" + self.Name

    def Activate(self):
        pass

    def flipFacing(self):
        call("flipFacing")

    def GetReferences(self, t):
        return ["ref:%s:%s" % (self.Name, t)]


class Collector:
    def __init__(self, doc):
        self._items = [e for e in REG if not getattr(e, "_hidden", False)]

    def OfClass(self, cls):
        name = cls if isinstance(cls, str) else getattr(cls, "_cls", cls.__name__)
        self._items = [e for e in self._items if e._cls == name]
        return self

    def OfCategory(self, cat):
        self._items = [e for e in self._items if getattr(e, "Category_", None) == cat]
        return self

    def WhereElementIsNotElementType(self):
        self._items = [e for e in self._items if e._cls not in ("FamilySymbol", "WallType", "FloorType", "ViewFamilyType", "ToposolidType")]
        return self

    def WhereElementIsElementType(self):
        return self

    def FirstElementId(self):
        return self._items[0].Id if self._items else EId.InvalidElementId

    def ToElements(self):
        return list(self._items)

    def __iter__(self):
        return iter(list(self._items))


def cls_factory(name, creator=None):
    """A Revit class stand-in: usable in OfClass(...), with optional static Create."""
    c = type(name, (), {"_cls": name})
    if creator:
        c.Create = staticmethod(creator)
    return c


def mk(cls, **kw):
    def f(*a, **k):
        call(cls + ".Create")
        return Element(cls, **kw)
    return f


class Transaction:
    def __init__(self, doc, name):
        self.name = name

    def Start(self):
        call("Transaction.Start")

    def Commit(self):
        call("Transaction.Commit")

    def RollBack(self):
        call("Transaction.RollBack")

    def GetFailureHandlingOptions(self):
        return Anything("opts")

    def SetFailureHandlingOptions(self, o):
        pass


class Line:
    @staticmethod
    def CreateBound(a, b):
        call("Line.CreateBound")
        if abs(a.X - b.X) + abs(a.Y - b.Y) + abs(a.Z - b.Z) < 1e-6:
            raise ValueError("curve too short")
        return ("line", a, b)


class ListOf(list):
    def Add(self, x):
        self.append(x)

    @property
    def Count(self):
        return len(self)


class Generic:
    def __getitem__(self, t):
        return ListOf


class CurveLoop(list):
    def Append(self, c):
        self.append(c)


CurveArray = CurveLoop


class ReferenceArray(list):
    def Append(self, r):
        self.append(r)

    @property
    def Size(self):
        return len(self)


class Transform:
    Identity = property(lambda self: Transform())

    def __init__(self):
        self.Origin = XYZ()
        self.BasisX, self.BasisY, self.BasisZ = XYZ(1, 0, 0), XYZ(0, 1, 0), XYZ(0, 0, 1)

    def OfPoint(self, p):
        return XYZ(self.Origin.X + p.X * self.BasisX.X + p.Y * self.BasisY.X, self.Origin.Y + p.X * self.BasisX.Y + p.Y * self.BasisY.Y, p.Z)

    @property
    def Inverse(self):
        return self


Transform.Identity = Transform()


class Creator:
    def __getattr__(self, name):
        def f(*a, **k):
            call("doc.Create." + name)
            if name == "NewRoom":
                return Element("Room", Area=10.0 / 0.0929)
            if name == "NewFamilyInstance":
                return Element("FamilyInstance", Host=a[2], FacingOrientation=XYZ(0, 1, 0), Category_=a[1].Category_)
            return Element(name)
        return f


class ProjectLocation:
    def SetProjectPosition(self, p, pos):
        call("SetProjectPosition")
        self.pos = pos

    def GetTotalTransform(self):
        t = Transform()
        ew, ns, el, ang = self.pos
        t.Origin = XYZ(ew, ns, el)
        t.BasisX = XYZ(math.cos(ang), math.sin(ang), 0)
        t.BasisY = XYZ(-math.sin(ang), math.cos(ang), 0)
        return t


class Doc:
    def __init__(self):
        self.Create = Creator()
        self.ActiveProjectLocation = ProjectLocation()
        self.Application = Anything("app")

    def GetElement(self, eid):
        return next((e for e in REG if e.Id.Equals(eid)), Element("Unknown"))

    def Delete(self, eid):
        call("doc.Delete")

    def Link(self, *a):
        call("doc.Link")

    def LoadFamily(self, p):
        return False


def install(with_families):
    db = types.ModuleType("Autodesk.Revit.DB")
    enums = ["BuiltInCategory", "BuiltInParameter", "FailureProcessingResult", "FailureSeverity", "FamilyInstanceReferenceType",
             "ImportPlacement", "MaterialFunctionAssignment", "ShellLayerType", "ViewFamily", "WallFunction", "WallKind"]
    for e in enums:
        setattr(db, e, EnumNS(e))
    db.XYZ, db.UV, db.ElementId, db.Transaction, db.Line, db.CurveLoop, db.CurveArray = XYZ, UV, EId, Transaction, Line, CurveLoop, CurveArray
    db.ReferenceArray, db.Transform, db.FilteredElementCollector = ReferenceArray, Transform, Collector
    db.IFailuresPreprocessor = type("IFailuresPreprocessor", (), {})
    db.BoundingBoxXYZ = lambda: types.SimpleNamespace()
    db.CompoundStructure = types.SimpleNamespace(CreateSingleLayerCompoundStructure=lambda *a: "cs")
    db.ProjectPosition = lambda *a: a
    db.DWGImportOptions = lambda: types.SimpleNamespace()
    db.ImportUnit = types.SimpleNamespace(Meter="Meter", Default="Default")
    db.LinkElementId = lambda i: i
    db.ScheduleSortGroupField = lambda i: i
    db.HostObjectUtils = types.SimpleNamespace(GetSideFaces=lambda w, s: ListOf(["face:%s:%s" % (w.Name, s)]))
    db.Curve = db.Reference = db.View = object
    for name in ("FamilySymbol", "FloorType", "Material", "ViewFamilyType", "WallType", "ToposolidType", "GraphicsStyle"):
        setattr(db, name, cls_factory(name))
    db.Level = cls_factory("Level", lambda doc, z: Element("Level", Elevation=z))
    db.Wall = cls_factory("Wall", mk("Wall"))
    db.Floor = cls_factory("Floor", mk("Floor"))
    db.SketchPlane = cls_factory("SketchPlane", mk("SketchPlane"))
    db.ViewPlan = cls_factory("ViewPlan", mk("ViewPlan", IsTemplate=False, GenLevel=None, Scale=100))
    db.ViewSection = types.SimpleNamespace(CreateSection=mk("ViewSection", Scale=100))
    db.ViewSchedule = types.SimpleNamespace(CreateSchedule=lambda doc, cat: Element("ViewSchedule", Definition=Definition()))
    db.ViewSheet = cls_factory("ViewSheet", mk("ViewSheet", SheetNumber="", ))
    db.Viewport = types.SimpleNamespace(Create=mk("Viewport"), CanAddViewToSheet=lambda *a: True)
    db.ScheduleSheetInstance = types.SimpleNamespace(Create=mk("ScheduleSheetInstance"))
    db.Toposolid = cls_factory("Toposolid", mk("Toposolid"))
    arch = types.ModuleType("Autodesk.Revit.DB.Architecture")
    arch.StairsEditScope = lambda doc, n: types.SimpleNamespace(Start=lambda a, b: Element("Stairs").Id, Commit=lambda q: call("stairs.Commit"),
                                                                 Cancel=lambda: None)
    arch.StairsRun = types.SimpleNamespace(CreateStraightRun=lambda *a: Element("StairsRun", ActualRunWidth=0))
    arch.StairsLanding = types.SimpleNamespace(CreateAutomaticLanding=mk("StairsLanding"))
    arch.StairsRunJustification = EnumNS("StairsRunJustification")
    arch.TopographySurface = cls_factory("TopographySurface", mk("TopographySurface"))
    struct = types.ModuleType("Autodesk.Revit.DB.Structure")
    struct.StructuralType = EnumNS("StructuralType")
    doc = Doc()
    persistence = types.ModuleType("RevitServices.Persistence")
    persistence.DocumentManager = types.SimpleNamespace(Instance=types.SimpleNamespace(CurrentDBDocument=doc))
    trans = types.ModuleType("RevitServices.Transactions")
    trans.TransactionManager = types.SimpleNamespace(Instance=types.SimpleNamespace(ForceCloseTransaction=lambda: None))
    generic = types.ModuleType("System.Collections.Generic")
    generic.List = Generic()
    clr = types.ModuleType("clr")
    clr.AddReference = lambda n: None
    for name, mod in (("clr", clr), ("Autodesk", types.ModuleType("Autodesk")), ("Autodesk.Revit", types.ModuleType("Autodesk.Revit")),
                      ("Autodesk.Revit.DB", db), ("Autodesk.Revit.DB.Architecture", arch), ("Autodesk.Revit.DB.Structure", struct),
                      ("RevitServices", types.ModuleType("RevitServices")), ("RevitServices.Persistence", persistence),
                      ("RevitServices.Transactions", trans), ("System", types.ModuleType("System")),
                      ("System.Collections", types.ModuleType("System.Collections")), ("System.Collections.Generic", generic)):
        sys.modules[name] = mod
    # what a new project from the architectural template contains
    Element("Level", Name="Level 1", Elevation=0.0)
    Element("Level", Name="Level 2", Elevation=4.0 / 0.3048)
    Element("WallType", Name="Generic - 200mm", Kind="WallKind.Basic", Function=None)
    Element("FloorType", Name="Generic 150mm")
    Element("ViewFamilyType", Name="Floor Plan", ViewFamily="ViewFamily.FloorPlan")
    Element("ViewFamilyType", Name="Building Section", ViewFamily="ViewFamily.Section")
    Element("ToposolidType", Name="Toposolid")
    if with_families:
        for cat, fam, nm in (("BuiltInCategory.OST_Doors", "M_Single-Flush", "0915 x 2134mm"), ("BuiltInCategory.OST_Doors", "M_Double-Flush", "1830 x 2134mm"),
                             ("BuiltInCategory.OST_Windows", "M_Fixed", "0915 x 1220mm")):
            Element("FamilySymbol", Name=nm, FamilyName=fam, Category_=cat, IsActive=True)
    return doc


class Definition:
    def GetSchedulableFields(self):
        return [types.SimpleNamespace(ParameterId=EId(None)) for _ in range(3)]

    def AddField(self, f):
        return types.SimpleNamespace(FieldId=EId())

    def AddSortGroupField(self, f):
        pass


if __name__ == "__main__":
    script, data = sys.argv[1], sys.argv[2]
    install("--with-families" in sys.argv)
    dwg = sys.argv[sys.argv.index("--dwg") + 1] if "--dwg" in sys.argv else None
    g = {"IN": [data, dwg], "__name__": "__dynamo__"}
    exec(compile(open(script, encoding="utf-8").read(), script, "exec"), g)
    print("\n".join(g["OUT"]))
    print("\nfake API calls:", sum(CALLS.values()))
    for k in sorted(CALLS, key=lambda k: -CALLS[k])[:25]:
        print("  %-40s %d" % (k, CALLS[k]))
