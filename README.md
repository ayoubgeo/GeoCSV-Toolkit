# Geocoding



# GeoCSV Mapper

GeoCSV Mapper is a Python-based desktop application that provides a Tkinter graphical interface for geocoding and reverse-geocoding CSV files. It allows users to visualize data on a map and supports exporting data in various formats such as CSV, KML, Shapefile, and GeoJSON. The tool also facilitates the conversion between these file formats.

![GeoCSV Mapper Geocoding](images\Geocoding.png)

![GeoCSV Mapper Home](D:\CARTOINWGS84\python\Geocoding\images\Home.png)

![GeoCSV Mapper Reverse Geocoding](D:\CARTOINWGS84\python\Geocoding\images\Reverse Geocoding.png)

![GeoCSV Mapper Conversion](D:\CARTOINWGS84\python\Geocoding\images\Conversion.png)

## Installation

No installation file is necessary. The script runs as a standalone application but requires Python to be installed on your system.

### Prerequisites

Make sure you have Python installed on your system. This application has been tested with Python 3.10.

Additionally, the following Python packages must be installed:
- pandas
- geopy
- requests
- simplekml
- tkintermapview
- shapely
- fiona

You can install these packages using `pip`. Run the following command:

```bash
pip install pandas geopy requests simplekml tkintermapview shapely fiona customtkinter
```

## Usage

To run the application, navigate to the directory containing the `Home.py` file and run:

```bash
python Home.py
```

Follow the GUI prompts to load your CSV file, perform geocoding/reverse-geocoding, visualize the data on the map, and export to the desired format.

## Contributing

Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
```

Please make sure to replace `Home.py` with the actual name of the Python file that runs your application if it is different. Adjust the list of required packages and Python version according to your actual project requirements.
