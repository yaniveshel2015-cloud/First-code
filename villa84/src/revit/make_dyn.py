"""Write villa84.dyn: a Dynamo 4 graph with two File Path inputs (data file, optional survey DWG), the build script in a
PythonNet3 Python Script node, and a Watch node for the report.

  python make_dyn.py villa84_build.py out/villa84.dyn
"""
import json
import sys
import uuid

script, out = sys.argv[1], sys.argv[2]
code = open(script, encoding="utf-8").read()


def gid():
    return uuid.uuid4().hex


def port(name, desc):
    return {"Id": gid(), "Name": name, "Description": desc, "UsingDefaultValue": False, "Level": 2, "UseLevels": False, "KeepListStructure": False}


def filename_node(value, desc):
    return {"ConcreteType": "CoreNodeModels.Input.Filename, CoreNodeModels", "Id": gid(), "NodeType": "ExtensionNode", "Inputs": [],
            "Outputs": [port("", "File Path")], "Replication": "Disabled", "Description": desc, "HintPath": value, "InputValue": value}


f_data = filename_node("C:\\villa84\\03-revit\\villa84-revit-data.json", "קובץ הנתונים של הווילה: villa84-revit-data.json")
f_dwg = filename_node("", "קובץ המדידה (DWG) לקישור. אפשר להשאיר ריק")
py = {"ConcreteType": "PythonNodeModels.PythonNode, PythonNodeModels", "Code": code, "Engine": "PythonNet3", "EngineName": "PythonNet3",
      "VariableInputPorts": True, "Id": gid(), "NodeType": "PythonScriptNode",
      "Inputs": [port("IN[0]", "Input #0"), port("IN[1]", "Input #1")], "Outputs": [port("OUT", "Result of the python script")],
      "Replication": "Disabled", "Description": "Builds the editable Revit model of villa 84"}
watch = {"ConcreteType": "CoreNodeModels.Watch, CoreNodeModels", "WatchWidth": 600.0, "WatchHeight": 600.0, "Id": gid(),
         "NodeType": "ExtensionNode", "Inputs": [port("", "Node to show output from")], "Outputs": [port("", "Node output")],
         "Replication": "Disabled", "Description": "Visualizes a node's output"}
connectors = [
    {"Start": f_data["Outputs"][0]["Id"], "End": py["Inputs"][0]["Id"], "Id": gid(), "IsHidden": "False"},
    {"Start": f_dwg["Outputs"][0]["Id"], "End": py["Inputs"][1]["Id"], "Id": gid(), "IsHidden": "False"},
    {"Start": py["Outputs"][0]["Id"], "End": watch["Inputs"][0]["Id"], "Id": gid(), "IsHidden": "False"},
]
dyn = {
    "Uuid": str(uuid.uuid4()), "IsCustomNode": False, "Description": "Villa 84: build an editable Revit 2027 model from villa84-revit-data.json",
    "Name": "villa84", "ElementResolver": {"ResolutionMap": {}}, "Inputs": [], "Outputs": [],
    "Nodes": [f_data, f_dwg, py, watch], "Connectors": connectors, "Dependencies": [], "NodeLibraryDependencies": [],
    "EnableLegacyPolyCurveBehavior": False, "Thumbnail": "", "GraphDocumentationURL": None, "ExtensionWorkspaceData": [], "Author": "",
    "Linting": {"activeLinter": "None", "activeLinterId": "7b75fb44-43fd-4631-a878-29f4d5d8399a", "warningCount": 0, "errorCount": 0},
    "Bindings": [],
    "View": {
        "Dynamo": {"ScaleFactor": 1.0, "HasRunWithoutCrash": False, "IsVisibleInDynamoLibrary": True, "Version": "4.0.2.3852",
                   "RunType": "Manual", "RunPeriod": "1000"},
        "Camera": {"Name": "_Background Preview", "EyeX": -17.0, "EyeY": 24.0, "EyeZ": 50.0, "LookX": 12.0, "LookY": -13.0, "LookZ": -58.0,
                   "UpX": 0.0, "UpY": 1.0, "UpZ": 0.0},
        "ConnectorPins": [],
        "NodeViews": [
            {"Id": f_data["Id"], "Name": "קובץ נתונים", "IsSetAsInput": True, "IsSetAsOutput": False, "Excluded": False, "ShowGeometry": True,
             "X": 0.0, "Y": 0.0},
            {"Id": f_dwg["Id"], "Name": "קובץ מדידה (לא חובה)", "IsSetAsInput": True, "IsSetAsOutput": False, "Excluded": False,
             "ShowGeometry": True, "X": 0.0, "Y": 180.0},
            {"Id": py["Id"], "Name": "בניית מודל וילה 84", "IsSetAsInput": False, "IsSetAsOutput": False, "Excluded": False,
             "ShowGeometry": True, "X": 420.0, "Y": 60.0},
            {"Id": watch["Id"], "Name": "דוח", "IsSetAsInput": False, "IsSetAsOutput": True, "Excluded": False, "ShowGeometry": True,
             "X": 760.0, "Y": 0.0},
        ],
        "Annotations": [], "X": 0.0, "Y": 0.0, "Zoom": 1.0,
    },
}
json.dump(dyn, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("wrote", out)
