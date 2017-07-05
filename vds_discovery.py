import sys
import math # To calculate distance
import xml.etree.ElementTree as ET  # For reading XML file

def main(argv):
    # Get latitude, longitude, and radius float values from user
    try:
        loc = [float(input("Latitude of location: "))]
        loc.append(float(input("Longitude of location: ")))
        radius = float(input("Radius extending from location: "))
    except:
        print("Please enter a numerical value\n")
    
    # Parse XML file in order to get information for VDSs.
    tree = ET.parse("vds_config.xml")
    root = tree.getroot()
    stations = root[11][1]  # Gets detector_stations child tag in XML file for District 11

    # Loops thru all of the VDSs to find if they are within the radius
    first_id = True
    for vds in stations.findall("vds"):
        # Get latitude, longitude, and ID for VDS
        vds_id = vds.get("id")
        try:
            vds_loc = [float(vds.get("latitude"))]
            vds_loc.append(float(vds.get("longitude")))
        except:
            print("Could not get latitude and longitude for {}".format(vds_id))
        # Compare distance from VDS to location to radius. If within boundaries, writes to file.
        if distance(loc, vds_loc) <= radius:
            if first_id == True:  # If first ID to be written (overwrite file as precaution)
                with open("IDs.txt", "w") as output_file:
                    output_file.write("{}\n".format(vds_id))
                first_id = False
            else:
                with open("IDs.txt", "a") as output_file: # All other IDs should be appended
                    output_file.write("{}\n".format(vds_id))


def distance(loc1, loc2):
    """Calculate distance between the entered coordinates and the coordinates of the VDS."""
    return math.sqrt((loc2[0]-loc1[0])**2 + (loc2[0]-loc1[0])**2) # sqrt((x2-x1)^2+(y2-y1)^2)


# Executes from here
if __name__ == "__main__":
    main(sys.argv[1:])
