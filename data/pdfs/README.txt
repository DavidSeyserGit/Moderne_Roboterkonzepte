========================================
Robot Navigation Locations
========================================

To add locations for the robot to navigate to, create a PDF file in this directory
with location data in one of the following formats:

FORMAT 1: Simple key-value format
---------------------------------
Küche: x=2.5, y=3.0, theta=1.57
Werkstatt: x=-1.0, y=4.5, theta=0.0
Ladestation: x=0.0, y=0.0, theta=3.14
Besprechungsraum: x=5.2, y=-2.3, theta=0.785

FORMAT 2: YAML format
---------------------
locations:
  kitchen:
    x: 2.5
    y: 3.0
    theta: 1.57
  workshop:
    x: -1.0
    y: 4.5
    theta: 0.0
  charging_station:
    x: 0.0
    y: 0.0
    theta: 3.14

FORMAT 3: Descriptive format
----------------------------
The kitchen is located at x=2.5, y=3.0, theta=1.57 in the map frame.
The workshop can be found at x=-1.0, y=4.5, theta=0.0.

========================================
EXAMPLE LOCATIONS (for testing)
========================================

Home: x=0.0, y=0.0, theta=0.0
Kitchen: x=2.5, y=3.0, theta=1.57
Workshop: x=-1.0, y=4.5, theta=0.0
Charging_Station: x=0.5, y=-0.5, theta=3.14
Meeting_Room: x=5.2, y=-2.3, theta=0.785

========================================

Once you add PDF files with location data to this directory,
the system will automatically index them on startup.

You can also manually trigger re-indexing by saying:
"Index the PDFs" or "Rebuild the index"
