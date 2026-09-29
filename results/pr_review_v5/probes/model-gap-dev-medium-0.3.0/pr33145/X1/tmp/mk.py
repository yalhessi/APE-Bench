import json,sys
name, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
json.dump({'path':'Mathlib/Topology/Order/IsLUB.lean','declaration_name':name,'new_declaration':open(src).read()}, open(out,'w'))
