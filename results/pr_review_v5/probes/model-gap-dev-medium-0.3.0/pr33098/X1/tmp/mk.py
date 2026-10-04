import json,sys
path, name, f = sys.argv[1], sys.argv[2], sys.argv[3]
print(json.dumps({"path":path,"declaration_name":name,"new_declaration":open(f).read()}))
