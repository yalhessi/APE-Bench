import json,sys
name, path = sys.argv[1], sys.argv[2]
print(json.dumps({"path":"Mathlib/Topology/Order/IsLUB.lean","declaration_name":name,"new_declaration":open(path).read()}))
