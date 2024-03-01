import csv
import json
import os
import threading
import time
from tkinter import ttk, filedialog, messagebox

import customtkinter as ctk
import tkinter as tk

import geopy
import pandas as pd
import requests
import simplekml
import tkintermapview
from geopandas.io.file import fiona
from geopy import GoogleV3, Nominatim, ArcGIS, Point
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from shapely.geometry import mapping

allwindow= ctk.CTk()

def on_focus_in(event):
    # set the text of the entry widget to an empty string when the entry widget has focus
    api_key_entry.delete(0, tk.END)

def on_focus_out(event):
    # get the current text of the entry widget
    current_text = api_key_entry.get()
    # check if the text is empty
    if current_text == "":
        # set the text back to the reference text if it is empty
        api_key_entry.insert(0, "Enter API")




# global variable to track whether geocoding should be stopped
stop_geocoding = False
# set the geocoding flag to False
geocoding_flag = False

# global variable to store the CSV data
csv_data = []

# global variable to store the file name
file_name = ""



# initialize the fields list
fields = []

def create_status_label(parent, row, column, **kwargs):
    global status_label
    status_label = ctk.CTkLabel(parent, **kwargs)
    status_label.grid(row=row, column=column, padx=15, pady=5, sticky="w")
    return status_label



def conversion_gui():
    global progress_bar, lat_field_var, file_format_var,lon_field_var
    conversion = ctk.CTkToplevel(allwindow)
    main_frame = ctk.CTkFrame(conversion)
    main_frame.grid(row=0, column=0, sticky="nswe")
    # up_frame = ctk.CTkFrame(main_frame)
    # up_frame.grid(row=0, column=0, sticky="nswe")
    left_frame = ctk.CTkFrame(main_frame)
    left_frame.grid(row=1, column=0, sticky="nswe")

    right_frame = ctk.CTkFrame(main_frame)
    right_frame.grid(row=1, column=1, sticky="nswe")

    # create the "Open CSV for Geocoding" button and place it in the window
    open_csv_button = ctk.CTkButton(left_frame, text="Open CSV", command=lambda: open_csv("reverse_geocoding", lat_option_menu=lat_option_menu, lon_option_menu=lon_option_menu))
    open_csv_button.grid(row=0, column=0, padx=15, pady=5, sticky="nswe")

    select_output_button = ctk.CTkButton(left_frame, text="Select Save Folder", command=select_output_dir)
    select_output_button.grid(row=5, column=0, padx=15, pady=5, sticky="ew")

    # create a StringVar to store the selected file format
    file_format_var = tk.StringVar(right_frame)
    # set the default file format to "shp"
    file_format_var.set("shp")

    # create a dropdown menu for the file formats
    file_format_menu = ttk.OptionMenu(right_frame, file_format_var, "select format", "shp", "kml", "geojson")
    file_format_menu.grid(row=5, column=0, padx=5, pady=5, sticky="nswe")

    # create the dropdown menus for selecting the latitude and longitude fields
    lat_field_label = ctk.CTkLabel(right_frame, text="Latitude field:")
    lat_field_label.grid(row=1, column=0, padx=5, pady=5)
    lat_field_var = tk.StringVar(conversion)
    lat_option_menu = ttk.OptionMenu(right_frame, lat_field_var, "")
    lat_option_menu.grid(row=2, column=0, padx=5, pady=5, sticky="nswe")

    lon_field_label = ctk.CTkLabel(right_frame, text="Longitude field:")
    lon_field_label.grid(row=3, column=0, padx=5, pady=5, sticky="nswe")
    lon_field_var = tk.StringVar(right_frame)
    lon_option_menu = ttk.OptionMenu(right_frame, lon_field_var, "")
    lon_option_menu.grid(row=4, column=0, padx=5, pady=5, sticky="nswe")


    # create the check button
    checkbutton = ctk.CTkCheckBox(left_frame, text="Plot on Map", variable=plot_on_map)
    checkbutton.grid(row=7, column=0, padx=15, pady=5, sticky="nswe")

    # create an export button
    export_button = ctk.CTkButton(right_frame, text="Export", command=export)
    export_button.grid(row=6, column=0, padx=5, pady=5, sticky="nswe")

    # create the progress bar and place it in the window
    progress_bar = ttk.Progressbar(left_frame, orient="horizontal")
    progress_bar.grid(row=10, column=0, padx=15, pady=5, sticky="nswe")

    status_label = create_status_label(left_frame, row=9, column=0, text="")

    HomeButton = ctk.CTkButton(left_frame, text="Home", command=return_home)
    HomeButton.grid(row=11, column=0,padx=15, pady=5, sticky='new')
    conversion.mainloop()




# define a function to export the data to a shapefile or KML file
def export_to_shapefile(filepath, header, lat_field, lon_field, file_format):
    # check if the file format is valid
    if file_format not in ("shp", "kml", "geojson"):
        status_label.configure(text="Error: Invalid file format.")
        return
    # get the field names from the dropdown menus
    lat_field = lat_field_var.get()
    lon_field = lon_field_var.get()

    # define the projection for the shapefile
    projection = '+proj=longlat +datum=WGS84 +no_defs'  # WGS 84
    schema = {
        'geometry': 'Point',
        'properties': {},
    }
    # create a list to store the shapefile features
    records = []
    # open the CSV file and read the rows
    try:
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]
    except Exception as e:
        print(e)  # debug
        status_label.configure(text="Error: Could not open CSV file.")
        return
    # get the header row and data rows
    header = rows[0]
    data = rows[1:]
    # get the total number of rows
    total_rows = len(data)
    # initialize the progress bar
    progress_bar["maximum"] = total_rows
    progress_bar["value"] = 0
    # iterate through the data rows
    for i, row in enumerate(data):
        # skip rows with missing or extra fields
        if len(row) != len(header):
            continue
        # get the latitude and longitude
        lat = row[header.index(lat_field)]
        lon = row[header.index(lon_field)]
        # skip rows with missing coordinates
        if lat is None or lon is None:
            continue
        # create a Point object
        try:
            point = Point(float(lon), float(lat))
        except ValueError:
            # handle the error here
            pass
        print(i, lat, lon)  # print the values of i, lat, and lon
        # create a dictionary with the field names and values
        properties = {header[i]: value for i, value in enumerate(row)}
        # create a feature dictionary
        feature = {
            'geometry': mapping(point),
            'properties': properties
        }
        # add the feature to the records list
        records.append(feature)
        # update the progress bar
        progress_bar["value"] = i
        progress_bar.update()

    print(len(records))  # debug
    # update the shapefile schema with the field names
    schema['properties'] = {name: 'str' for name in header}
    # create the shapefile driver
    driver = 'ESRI Shapefile' if file_format == "shp" else 'libkml'
    env = fiona.Env(driver=driver)
    # create a file dialog to choose the directory where to save the file
    directory = filedialog.askdirectory()
    # create the file name based on the selected file format
    filename = "geocoded_data." + file_format
    # create the full file path
    filepath = os.path.join(directory, filename)
    # create the shapefile or KML file based on the selected file format
    if file_format == "shp":
        # create the shapefile driver
        driver = 'ESRI Shapefile'
        env = fiona.Env(driver=driver)
        # create the shapefile collection
        collection = fiona.collection(filepath, "w", driver=driver, schema=schema, crs=projection, encoding="utf-8")
        # iterate through the features
        for feature in records:
            # add the feature to the collection
            collection.write(feature)
        # close the shapefile collection
        collection.close()
    elif file_format == "kml":
        # create a KML document
        kml = simplekml.Kml()
        # create a KML folder
        folder = kml.newfolder(name='Geocoded data')
        # iterate through the features
        for feature in records:
            # get the feature properties
            properties = feature['properties']
            # create a KML placemark
            placemark = folder.newpoint(
                name=properties.get('Name', ''),
                description=properties.get('Description', ''),
                coords=[(feature['geometry']['coordinates'][0], feature['geometry']['coordinates'][1])]
            )
            # add the extended data to the placemark
            for key, value in properties.items():
                placemark.extendeddata.newdata(name=key, value=value)
        # save the KML document to the file
        kml.save(filepath)
    elif file_format == "geojson":

        # create the file name based on the selected file format
        filename = "geocoded_data.geojson"
        # create a dictionary to store the GeoJSON feature collection
        geojson = {
            "type": "FeatureCollection",
            "features": records
        }
        # write the GeoJSON feature collection to the file
        with open(filepath, "w") as f:
            json.dump(geojson, f)
    else:
        status_label.configure(text="Error: Invalid file format.")
        return
    # update the status label
    completed_window("Export")


## create a function to handle the export button press
def export():
    file_format = file_format_var.get()
    # get the field names from the dropdown menus
    lat_field = lat_field_var.get()
    lon_field = lon_field_var.get()
    # define the filepath variable
    # export the data to the selected file format
    export_to_shapefile( lat_field, lon_field, file_format)


def reversegeocoding_gui():
    global lat_option_menu, lon_option_menu, lat_field, lon_field, api_key_entry, progress_bar, api_key

    reverse = ctk.CTkToplevel(allwindow)
    main_frame = ctk.CTkFrame(reverse)
    main_frame.grid(row=0, column=0, sticky="nswe")
    # up_frame = ctk.CTkFrame(main_frame)
    # up_frame.grid(row=0, column=0, sticky="nswe")
    left_frame = ctk.CTkFrame(main_frame)
    left_frame.grid(row=1, column=0, sticky="nswe")

    right_frame = ctk.CTkFrame(main_frame)
    right_frame.grid(row=1, column=1, sticky="nswe")

    # left_frame = ctk.CTkFrame(main_frame)
    # left_frame.grid(row=2, column=0, sticky="nswe")

    # create the map widget and place it in the window
    map_widget = tkintermapview.TkinterMapView(right_frame, width=500, height=500, corner_radius=0)
    map_widget.grid(row=0, column=0, rowspan=4, padx=15, pady=5, sticky="nswe")

    # create the "Open CSV for Geocoding" button and place it in the window
    open_csv_button = ctk.CTkButton(left_frame, text="Open CSV", command=lambda: open_csv("reverse_geocoding", lat_option_menu=lat_option_menu, lon_option_menu=lon_option_menu))
    open_csv_button.grid(row=0, column=0, padx=15, pady=5, sticky="nswe")

    # xyframe = ctk.CTkFrame(left_frame)
    # xyframe.grid(row=1, column=0, sticky="nswe")

    lat_field = tk.StringVar(reverse)
    lon_field = tk.StringVar(reverse)
    # set the default values to the first two fields
    lat_field.set('select X')
    lon_field.set('Select Y')
    lat_option_menu = ttk.OptionMenu(left_frame, lat_field, *fields)
    lon_option_menu = ttk.OptionMenu(left_frame, lon_field, *fields)
    lat_option_menu.configure(takefocus=False)
    lon_option_menu.configure(takefocus=False)
    lat_option_menu.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
    lon_option_menu.grid(row=2, column=0, padx=15, pady=5, sticky="ew")

    # create a list of geocoding services
    geocoding_services = ['ArcGIS', 'Nominatim', 'Google']
    # create a variable to store the selected geocoding service
    selected_service = ctk.CTkComboBox(left_frame, values=geocoding_services, state="readonly")
    # create the OptionMenu widget
    # add the OptionMenu widget to the main window
    selected_service.grid(row=3, column=0, padx=15, pady=5, sticky="nswe")
    # create a label and an input field for the API key
    api_key_entry = ctk.CTkEntry(left_frame)
    api_key_entry.grid(row=4, column=0, padx=15, pady=5, sticky="nswe")
    # bind the focusin and focusout events to the entry widget
    api_key_entry.bind("<FocusIn>", on_focus_in)
    api_key_entry.bind("<FocusOut>", on_focus_out)

    # insert the text "Enter API key" into the Entry widget
    api_key_entry.insert(0, "Enter API key")
    api_key = api_key_entry.get()

    select_output_button = ctk.CTkButton(left_frame, text="Select Save Folder", command=select_output_dir)
    reverse_geocode_button = ctk.CTkButton(left_frame, text="Reverse Geocode",
                                           command=lambda: reverse_geocode_csv(selected_service, api_key))
    select_output_button.grid(row=5, column=0, padx=15, pady=5, sticky="ew")
    reverse_geocode_button.grid(row=6, column=0, padx=15, pady=5, sticky="ew")

    # create the check button
    checkbutton = ctk.CTkCheckBox(left_frame, text="Plot on Map", variable=plot_on_map)
    checkbutton.grid(row=7, column=0, padx=15, pady=5, sticky="nswe")

    # create the progress bar and place it in the window
    progress_bar = ttk.Progressbar(left_frame, orient="horizontal")
    progress_bar.grid(row=8, column=0, padx=15, pady=5, sticky="nswe")

    status_label = create_status_label(left_frame, row=9, column=0, text="")

    HomeButton = ctk.CTkButton(left_frame, text="Home", command=return_home)
    HomeButton.grid(row=10, column=0,padx=15, pady=5, sticky='new')
    reverse.mainloop()

def geocode_gui():
    global map_widget, geocode_button, address_field, geocode, address_option_menu,api_key_entry, progress_bar
    geocode = ctk.CTkToplevel(allwindow)
    main_frame = ctk.CTkFrame(geocode)
    main_frame.grid(row=0, column=0, sticky="nswe")
    # up_frame = ctk.CTkFrame(main_frame)
    # up_frame.grid(row=0, column=0, sticky="nswe")
    left_frame = ctk.CTkFrame(main_frame)
    left_frame.grid(row=1, column=0, sticky="nswe")

    right_frame = ctk.CTkFrame(main_frame)
    right_frame.grid(row=1, column=1, sticky="nswe")

    address_field = tk.StringVar(geocode)
    address_field.set('Select Address')
    address_option_menu = ttk.OptionMenu(left_frame, address_field, *fields)

    address_option_menu.config(takefocus=False)
    address_option_menu.grid(row=1, column=0, padx=15, pady=2, sticky="ew")
    # create the map widget and place it in the window
    map_widget = tkintermapview.TkinterMapView(right_frame, width=500, height=500, corner_radius=0)
    map_widget.grid(row=0, column=0, rowspan=4, padx=15, pady=5, sticky="nswe")

    # create the "Open CSV for Geocoding" button and place it in the window
    open_geocoding_csv_button = ctk.CTkButton(left_frame, text="Open CSV for Geocoding",
                                              command=lambda: open_csv("geocoding",
                                                                       address_option_menu=address_option_menu))
    open_geocoding_csv_button.grid(row=0, column=0, padx=15, pady=5, sticky="nswe")

    # xyframe = ctk.CTkFrame(left_frame)
    # xyframe.grid(row=1, column=0, sticky="nswe")

    # create a variable to store the selected geocoding service
    selected_service = ctk.CTkComboBox(left_frame, values=geocoding_services)
    selected_service.configure(border_width=0.5, corner_radius=3)
    # add the OptionMenu widget to the main window
    selected_service.grid(row=3, column=0, padx=15, pady=5, sticky="nswe")
    # create a label and an input field for the API key
    api_key_entry = ctk.CTkEntry(left_frame)
    api_key_entry.grid(row=4, column=0, padx=15, pady=5, sticky="nswe")
    # bind the focusin and focusout events to the entry widget
    api_key_entry.bind("<FocusIn>", on_focus_in)
    api_key_entry.bind("<FocusOut>", on_focus_out)

    # insert the text "Enter API key" into the Entry widget
    api_key_entry.insert(0, "Enter API key")
    api_key = api_key_entry.get()

    select_output_button = ctk.CTkButton(left_frame, text="Select Save Folder", command=select_output_dir)
    select_output_button.grid(row=5, column=0, padx=15, pady=5, sticky="ew")

    # create the check button
    checkbutton = ctk.CTkCheckBox(left_frame, text="Plot on Map", variable=plot_on_map)
    checkbutton.grid(row=7, column=0, padx=15, pady=5, sticky="nswe")

    # create a button to start the geocoding process
    geocode_button = ctk.CTkButton(left_frame, text="Geocode",
                                   command=lambda: start_geocoding(selected_service, api_key))
    # disable the "Geocode" button until the user selects an output folder
    geocode_button.grid(row=8, column=0, padx=15, pady=2, sticky="nswe")

    # create the progress bar and place it in the window
    progress_bar = ttk.Progressbar(left_frame, orient="horizontal")
    progress_bar.grid(row=10, column=0, padx=15, pady=5, sticky="nswe")

    status_label = create_status_label(left_frame, row=9, column=0, text="")

    HomeButton = ctk.CTkButton(left_frame, text="Home", command=return_home)
    HomeButton.grid(row=11, column=0,padx=15, pady=5, sticky='new')
    geocode.mainloop()



def check_api_key(api_key, selected_service):
    # get the selected geocoding service
    selected_service = selected_service.get()

    if selected_service == 'Google':
        try:
            response = requests.get(
                f'https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA&key={api_key}')
            if response.status_code == 200:
                json_response = response.json()
                if 'error_message' in json_response:
                    status_label.configure(text=json_response['error_message'])
                    return None
                else:
                    geolocator = GoogleV3(api_key=api_key)
                    return geolocator
            else:
                status_label.configure(text="Invalid Google API key, please check your key")
                return None

        except requests.exceptions.RequestException as e:
            status_label.configure(text=str(e))
            return None
    elif selected_service == 'Nominatim':
        try:
            geolocator = Nominatim(user_agent="ayoubla3@gmail.com")
            return geolocator
        except geopy.exc.GeocoderTimedOut as e:
            status_label.configure(text=str(e))
            return None
    elif selected_service == 'ArcGIS':
        try:
            geolocator = ArcGIS()
            return geolocator
        except geopy.exc.GeocoderTimedOut as e:
            status_label.configure(text=str(e))
            return None
    else:
        geolocator = Nominatim(user_agent="ayoubla3@gmail.com")
        return geolocator
def open_csv(window_type, lat_option_menu=None, lon_option_menu=None, address_option_menu=None):
    # open a file dialog to select the CSV file
    file_path = filedialog.askopenfilename()

    # store the file path in a global variable
    global csv_file_path
    csv_file_path = file_path
    # print the value of the csv_file_path variable to the console
    print(csv_file_path)

    # read the CSV file and store the field names in the fields list
    global fields
    fields = []
    with open(csv_file_path, 'r') as f:
        reader = csv.reader(f)
        fields = next(reader)

    # update the options in the OptionMenu widgets
    if fields:
        if window_type == "geocoding":
            address_option_menu['menu'].delete(0, 'end')
            for field in fields:
                address_option_menu['menu'].add_command(label=field, command=tk._setit(address_field, field))
        elif window_type == "reverse_geocoding":
            lat_option_menu['menu'].delete(0, 'end')
            lon_option_menu['menu'].delete(0, 'end')
            for field in fields:
                lat_option_menu['menu'].add_command(label=field, command=tk._setit(lat_field, field))
                lon_option_menu['menu'].add_command(label=field, command=tk._setit(lon_field, field))

    # create a function to set the selected fields as the latitude, longitude, and address fields
    def set_fields(name, index, mode):
        global lat_field_name, lon_field_name, address_field_name
        lat_field_name = lat_field.get()
        lon_field_name = lon_field.get()
        address_field_name = address_field.get()

    lat_field.trace("w", set_fields)
    lon_field.trace("w", set_fields)
    address_field.trace("w", set_fields)

# define the function to select the output directory
def select_output_dir():
    # open a file dialog to select the output directory
    dir_path = filedialog.askdirectory()
    # store the directory path in a global variable
    global output_dir
    output_dir = dir_path
    # print the value of the output_folder variable to the console
    print(dir_path)
    # enable the "Geocode" button
    geocode_button["state"] = "normal"
# create a list of geocoding services
geocoding_services = ['ArcGIS', 'Nominatim', 'Google']

# create the OptionMenu widget

# define the function to reverse geocode all the records in the CSV file
#Set task processing to None
is_completed = False
#Set output directory to None
output_dir = None


def reverse_geocode_csv(selected_service, api_key):
    api_key = api_key_entry.get()
    global geolocator
    geolocator = check_api_key(api_key, selected_service)
    # open the CSV file and read the records
    with open(csv_file_path, 'r') as f:
        reader = csv.reader(f)
        # get the field names row
        field_names = next(reader)
        # get the total number of rows
        total_rows = sum(1 for row in reader)
        # reset the file pointer
        f.seek(0)
        next(reader)
        # initialize the progress bar
        progress_bar["maximum"] = total_rows
        progress_bar["value"] = 0
        # check if the output folder has been selected
        if output_dir == None:
            messagebox.showerror("Error", "Select Save folder first")
            return
        # iterate over the records
        while True:
            try:
                for row in reader:
                    # get the latitude and longitude values from the selected fields
                    lat = row[fields.index(lat_field_name)]
                    lon = row[fields.index(lon_field_name)]
                    # reverse geocode the coordinates
                    location = geolocator.reverse((lat, lon))
                    address = location.address
                    # write the results to a CSV file
                    with open(f"{output_dir}/reversed.csv", 'a', encoding='utf-8', newline='') as g:
                        writer = csv.writer(g)
                        writer.writerow(row + [address])
                        # update the progress bar
                        progress_bar["value"] += 1
                        progress_bar.update()
                break # break the loop if successful
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}\nRetrying in 5 seconds...")
                time.sleep(5) # wait 5 seconds before retrying

    completed_window("Reverse Geocoding")



def completed_window(task):
    completed_window = tk.Toplevel()
    completed_window.geometry("200x100")
    label = tk.Label(completed_window, text=f"{task} Completed")
    label.pack()
    button = ctk.CTkButton(completed_window, text="OK", command=completed_window.destroy)
    button.pack()
    status_label["text"] = ""
    stop_geocoding = False


# create the check button variable
plot_on_map = tk.IntVar()


# define the function to geocode the addresses
def geocode_addresses(csv_data, file_name, address_field, selected_service, api_key):
    global geocoded_data
    api_key = api_key_entry.get()
    global geolocator, geocoding_flag, address_field_index, data

    geolocator = check_api_key(api_key, selected_service)
    if not geolocator:
        return
    # check if the output folder has been selected
    if not csv_data:
        print("Error: empty list")
    else:
        # skip the header row
        header = csv_data[0]
        data = csv_data[1:]
        # get the total number of rows
        total_rows = len(data)
    # skip the header row
    header = csv_data[0]
    data = csv_data[1:]
    # get the total number of rows
    total_rows = len(data)
    # get the index of the address field
    address_field_index = header.index(address_field)
    # initialize the progress bar
    progress_bar["maximum"] = total_rows
    progress_bar["value"] = 0
    # geocode the addresses
    geocoded_data = []
    coordinates = []  # list to store the geocoded coordinates
    for row in data:
        # check the value of stop_geocoding
        if stop_geocoding:
            break
        address = row[address_field_index]
        retries = 0
        while True:
            # check the value of stop_geocoding
            if stop_geocoding:
                break
            try:
                location = geolocator.geocode(query=address, timeout=2)
                break
            except GeocoderTimedOut:
                if retries >= 3:
                    break
                retries += 1
                time.sleep(10)
            except GeocoderServiceError as e:
                handle_connection_error()
                return
        try:
            lat = location.latitude
            lon = location.longitude
            # add the coordinates to the list
            coordinates.append((lat, lon))
        except AttributeError:
            lat = None
            lon = None
        geocoded_row = row + [lat, lon]
        geocoded_data.append(geocoded_row)
        # update the progress bar
        progress_bar["value"] += 1
        progress_bar.update()
        geocoded_data.append(geocoded_row)
        if lat is not None and lon is not None:
         if plot_on_map.get() == 1:
                map_widget.set_marker(lat, lon,
                                  command=lambda marker: marker_click(marker, header, address_field_index),
                                  text=row[address_field_index])
                # Calculate the average latitude and longitude of all the locations
                latitudes = [location[0] for location in coordinates]
                longitudes = [location[1] for location in coordinates]
                try:
                    avg_lat = sum(latitudes) / len(latitudes)
                    avg_lon = sum(longitudes) / len(longitudes)
                except ZeroDivisionError:
                    avg_lat = 0
                    avg_lon = 0
                # Set the center point of the map to the average latitude and longitude
                map_widget.set_position(avg_lat, avg_lon)
                # Set the zoom level so that all the locations are visible on the map
                # You can experiment with different values for the zoom level to see what works best
                map_widget.set_zoom(8)
                # set a position marker with a command
                # update the progress bar
                progress_bar["value"] += 1
                progress_bar.update()
                # set the geocoding flag to True
                geocoding_flag = True

    header += ["lat", "lon"]
    # create a DataFrame from the geocoded data
    df = pd.DataFrame(geocoded_data, columns=header)
    # read the CSV file and store the data in the csv_data variable
    csv_data = []
    with open(csv_file_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            csv_data.append(row)
        # export the DataFrame to the selected file
        df.to_csv(os.path.join(output_dir, "geocoded" + ".csv"), index=False)

is_geocoding = False
def start_geocoding(selected_service, api_key):
    global stop_geocoding, geocoding_flag, is_completed, is_geocoding
    geolocator = check_api_key(api_key, selected_service)
    if geolocator is None:
        handle_api_key_error()
        return
    # check if the output folder has been selected
    if output_dir == None:
        tk.messagebox.showerror("Error", "Select Save folder first")
        return
    if not geocoding_flag and not is_geocoding:
        # get the selected field name
        field_name = address_field.get()
        # get the index of the selected field
        field_index = fields.index(field_name)
        # read the CSV file and store the data in the csv_data list
        with open(csv_file_path, 'r') as f:
            reader = csv.reader(f)
            global csv_data
            csv_data = list(reader)
        # set the stop_geocoding flag to False
        stop_geocoding = False
        # change the text of the "Geocode" button to "Stop"
        geocode_button.configure(text="Stop")
        # disable the "Geocode" button
        geocode_button.configure(state="normal")
        # update the status label
        status_label.configure(text="Geocoding in progress...")
        is_geocoding = True
        # start a new thread to geocode the addresses
        thread = threading.Thread(target=geocode_addresses, args=(csv_data, file_name, field_name, selected_service, api_key))
        thread.start()
        while thread.is_alive():
            status_label.configure(text="Geocoding in progress...")
            geocode.update()
            time.sleep(0.1)
        geocoding_flag = False
        is_completed = True
    # if the geocoding flag is True and the button text is "Resume", resume the geocoding process
    elif geocoding_flag:
        # set the stop_geocoding flag to False
        stop_geocoding = False
        # change the text of the "Resume" button to "Stop"
        geocode_button.configure(text="Stop")
        # disable the "Geocode" button
        geocode_button.configure(state="normal")
        # update the status label
        status_label.configure(text="Geocoding in progress...")
    # if the geocoding flag is True, stop the geocoding process
    else:
        is_geocoding = False
        # set the stop_geocoding flag to True
        stop_geocoding = True
        # change the text of the "Stop" button to "Resume"
        geocode_button.configure(text="Restart")
        # enable the "Geocode" button
        geocode_button.configure(state="normal")
        # update the status label
        status_label.configure(text="Geocoding stopped.")
        # if the geocoding flag is False, start the geocoding process
    if is_completed and not stop_geocoding:
        completed_window("Geocoding")
        status_label.configure(text="Geocoding Completed.")
        geocode_button.configure(text="Geocode")

def handle_api_key_error():
    geocode_button.configure(state="normal")
    geocode_button.configure(text="Invalid API key, please check your key.")
def handle_connection_error():
    tk.messagebox.showerror("Error", "Connection error, please check your internet connection.")
    geocode_button.configure(state="normal")
    geocode_button.configure(text="Geocode")
    geocoding_flag = False
    geocode_button.configure(text="Geocoding failed.")
    is_completed = False

def marker_click(marker, header, address_field_index):
    if header is None:
        print(f"marker clicked - text: {marker.text}  position: {marker.position}")
    else:
        # create a new popup window
        popup_window = tk.Toplevel()

        # get the marker text
        marker_text = marker.text
        # retrieve the desired row from the geocoded_data list
        for row in geocoded_data:
            if row[address_field_index] == marker_text:
                break

        if row is None:
            # if no match was found, display an error message
            tk.messagebox.showerror("Error", "No data found for marker")
            return

        # create the treeview widget to display the information in a table
        tree = ctk.CTkTabview(popup_window)
        tree["columns"] = ("value")
        tree.column("#0", width=100, anchor="w")
        tree.column("value", width=150, anchor="w")
        tree.heading("#0", text="Field")
        tree.heading("value", text="Value")

        # insert the field names and values from the header and row variables into the treeview
        for i, value in enumerate(row):
            tree.insert("", "end", text=header[i], values=(value,))

        # create a close button to close the window
        close_button = ctk.CTkButton(popup_window, text="Close", command=popup_window.destroy)

        # add the treeview and close button to the window
        tree.pack()
        close_button.pack(padx=10, pady=10)



def return_home():
    services()


def services():
    global home
    home = ctk.CTk()
    home.geometry("400x400")

    GeoButton = ctk.CTkButton(home, text="Geocode", width=10, height=2, command=geocode_gui)
    GeoButton.grid(row=0, column=0, padx=5, pady=5, sticky="nswe", columnspan=1)

    RevButton = ctk.CTkButton(home, text="Reverse Geocoding", width=10, height=2, command=reversegeocoding_gui)
    RevButton.grid(row=0, column=1, padx=5, pady=5, sticky="nswe", columnspan=1)

    ExpButton = ctk.CTkButton(home, text="Conversion", width=10, height=2, command=conversion_gui)
    ExpButton.grid(row=1, column=0, padx=5, pady=5, sticky="nswe", columnspan=1)

    AboutButton = ctk.CTkButton(home, text="About", width=10, height=2)
    AboutButton.grid(row=1, column=1, padx=5, pady=5, sticky="nswe", columnspan=1)

    home.grid_columnconfigure(0, weight=1, minsize=10)
    home.grid_columnconfigure(1, weight=1, minsize=10)
    home.grid_rowconfigure(0, weight=1, minsize=10)
    home.grid_rowconfigure(1, weight=1, minsize=10)
    home.mainloop()


services()
