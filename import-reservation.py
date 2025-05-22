import json
import requests
import argparse

msg = "Import reservation objects into Kea DHCP from a JSON file"

parser = argparse.ArgumentParser(description = msg)
parser.add_argument("file", help="Path or filename to JSON file to import")
parser.add_argument("URL", help="URL of Kea DHCP API endpoint", default="http://[::1]:9099")
parser.add_argument("--ignore_duplicate", dest="ignore", action="store_true", help="Ignore duplicate database entry errors.")
args = parser.parse_args()

api_url = args.URL
total_reservations = 0
import_success = 0
import_fail    = 0
import_ignore  = 0

print(f"Importing JSON reservations from {args.file}")
print(f"Sending to API endpoint {args.URL}")

# Opening JSON file
f = open(args.file)

# returns JSON object as a dictionary
data = json.load(f)

# Iterating through the json list of reservations
for i in data["reservations"]:
    total_reservations += 1
    reservationadd = "{ \"command\": \"reservation-add\", \"service\": [ \"dhcp4\" ], \"arguments\": { \"reservation\": " + str(i).replace("'", '"') + " }}"
    resjson = json.loads(reservationadd)
    response = requests.post(api_url, json=resjson)
    respjson = response.json()
    resptext = str(respjson)
    if respjson[0]["result"] > 0:
        if "Mandatory 'subnet-id' parameter missing" in resptext:
            idnum = resptext[resptext.index("' id")+4:resptext.index("}]")-2]
            i["subnet-id"] = int(idnum)
            reservationadd = "{ \"command\": \"reservation-add\", \"service\": [ \"dhcp4\" ], \"arguments\": { \"reservation\": " + str(i).replace("'", '"') + " }}"
            resjson = json.loads(reservationadd)
            response = requests.post(api_url, json=resjson)
            respjson = response.json()
            if respjson[0]["result"] > 0:
                if args.ignore and "Database duplicate entry error" in respjson[0]["text"]:
                    import_ignore +=1
                else:
                    import_fail += 1
                    print("Error: " + respjson[0]["text"] + " " + str(i))
            else:
                import_success += 1
        else:
            if args.ignore and "Database duplicate entry error" in respjson[0]["text"]:
                import_ignore +=1
            else:
                import_fail += 1
                print("Error: " + respjson[0]["text"] + " " + str(i))
    else:
        import_success += 1

# Closing file
f.close()
print("Finished importing reservations")
print(f"Reservations processed: {total_reservations}")
print(f"Successfully imported : {import_success}")
print(f"Import failed         : {import_fail}")
print(f"Duplicates ignored    : {import_ignore}")
