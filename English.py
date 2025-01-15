import os
import json
import logging
import shutil
import re
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import exifread
from opencage.geocoder import OpenCageGeocode

# ------------------------ CONFIGURATION --------------------------
OPENCAGE_API_KEY = "Your_API_Key"  # Replace with your key
BASE_FOLDER = r"Takeout\Photos from" # Replace with your takeout folder
OUTPUT_FOLDER = r"\photos" # Replace with your final folder

# Supported extensions
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.mkv', '.avi')

# Log and cache files
LOG_FILE = os.path.join(OUTPUT_FOLDER, "organization.log")
CACHE_FILE = os.path.join(OUTPUT_FOLDER, "location_cache.json")

# ------------------------ LOGGING --------------------------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s','%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

logger = logging.getLogger(__name__)

# ------------------------ GEOCODING --------------------------
geocoder = OpenCageGeocode(OPENCAGE_API_KEY)

# Load or initialize location cache
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        location_cache = json.load(f)
else:
    location_cache = {}

def save_location_cache():
    """Save the location cache to disk."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(location_cache, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving location cache: {e}")

def dms2dd(degrees, minutes, seconds, direction):
    """Convert DMS (degrees, minutes, seconds) coordinates to decimal (DD)."""
    dd = float(degrees) + float(minutes)/60 + float(seconds)/3600
    if direction in ['S', 'W']:
        dd *= -1
    return dd

def parse_gps_info(gps_info):
    """Convert GPS information into a (lat, lon) tuple."""
    def extract_dms(rational_list):
        d = float(rational_list[0].num) / float(rational_list[0].den)
        m = float(rational_list[1].num) / float(rational_list[1].den)
        s = float(rational_list[2].num) / float(rational_list[2].den)
        return d, m, s

    try:
        lat = None
        lon = None
        lat_ref = gps_info.get("GPSLatitudeRef")
        lon_ref = gps_info.get("GPSLongitudeRef")

        if "GPSLatitude" in gps_info:
            d, m, s = extract_dms(gps_info["GPSLatitude"].values)
            lat_dir = lat_ref.printable if lat_ref else 'N'
            lat = dms2dd(d, m, s, lat_dir)

        if "GPSLongitude" in gps_info:
            d, m, s = extract_dms(gps_info["GPSLongitude"].values)
            lon_dir = lon_ref.printable if lon_ref else 'E'
            lon = dms2dd(d, m, s, lon_dir)

        if lat is not None and lon is not None:
            return (lat, lon)
    except Exception as e:
        logger.error(f"Error processing GPS coordinates: {e}")
    return None

def get_city_state_name(lat, lon):
    """
    Given coordinates (lat, lon), returns the location as "City - State".
    If it cannot be determined, returns "No_Location".
    """
    latlon_key = f"{lat:.6f},{lon:.6f}"
    if latlon_key in location_cache:
        return location_cache[latlon_key]

    try:
        results = geocoder.reverse_geocode(lat, lon)
        if results and 'components' in results[0]:
            components = results[0]['components']
            city = components.get('city') or components.get('town') or components.get('village') or components.get('municipality')
            state = components.get('state')
            if city and state:
                location_name = f"{city} - {state}"
                location_cache[latlon_key] = location_name
                save_location_cache()
                return location_name
    except Exception as e:
        logger.error(f"Error converting coordinates to location: {e}")

    location_cache[latlon_key] = "No_Location"
    save_location_cache()
    return "No_Location"

def get_metadata_from_exif(image_path):
    """Extract date and location from the EXIF data of an image."""
    date = None
    location = None
    try:
        with open(image_path, 'rb') as img_file:
            tags = exifread.process_file(img_file)
            # Date
            if "EXIF DateTimeOriginal" in tags:
                date_str = tags["EXIF DateTimeOriginal"].values
                date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")

            # GPS
            gps_info = {}
            for tag, value in tags.items():
                if tag.startswith("GPS"):
                    gps_key = TAGS.get(tag, tag)
                    if gps_key.startswith("GPS "):
                        gps_key = gps_key[4:]
                    gps_info[gps_key] = value

            if gps_info:
                coords = parse_gps_info(gps_info)
                if coords:
                    location = coords
    except Exception as e:
        logger.error(f"Error reading EXIF from {image_path}: {e}")
    return date, location

def get_metadata_from_json(json_path):
    """Read metadata (location and date) from a JSON file."""
    date = None
    coords = None
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Date
        if "photoTakenTime" in data and "timestamp" in data["photoTakenTime"]:
            ts = int(data["photoTakenTime"]["timestamp"])
            date = datetime.fromtimestamp(ts)

        # Location
        lat = 0.0
        lon = 0.0
        if "geoData" in data:
            lat = data["geoData"].get("latitude", 0.0)
            lon = data["geoData"].get("longitude", 0.0)

        if (lat == 0.0 and lon == 0.0) and "geoDataExif" in data:
            lat = data["geoDataExif"].get("latitude", 0.0)
            lon = data["geoDataExif"].get("longitude", 0.0)

        if not (lat == 0.0 and lon == 0.0):
            coords = (lat, lon)

    except Exception as e:
        logger.error(f"Error reading {json_path}: {e}")

    return date, coords

def get_final_metadata(file_path):
    """
    Attempt to extract metadata (date, location) from the associated JSON.
    If not available, try EXIF for images.
    """
    base_name, ext = os.path.splitext(file_path)
    json_path = file_path + ".json"
    date, location = None, None

    # Try from JSON
    if os.path.exists(json_path):
        date_json, coords_json = get_metadata_from_json(json_path)
        if date_json is not None:
            date = date_json
        if coords_json is not None:
            location = coords_json

    # If it's an image and data is missing, try EXIF
    if ext.lower() in IMAGE_EXTENSIONS:
        if date is None or location is None:
            date_exif, coords_exif = get_metadata_from_exif(file_path)
            if date is None:
                date = date_exif
            if location is None:
                location = coords_exif

    return date, location

def organize_files(base_folder, output_folder):
    """Organize images and videos into folders by location and date."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for root, _, files in os.walk(base_folder):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            if ext in IMAGE_EXTENSIONS or ext in VIDEO_EXTENSIONS:
                date, coordinates = get_final_metadata(file_path)

                # Location
                location_folder = "No_Location"
                if coordinates:
                    location_folder = get_city_state_name(*coordinates)

                # Date
                date_folder = "No_Date"
                if date:
                    date_folder = date.strftime('%d-%m-%y')

                target_folder = os.path.join(output_folder, location_folder, date_folder)
                os.makedirs(target_folder, exist_ok=True)

                dest_path = os.path.join(target_folder, file)
                if not os.path.exists(dest_path):
                    shutil.copy(file_path, dest_path)
                    logger.info(f"Moved: {file_path} -> {target_folder}")
                else:
                    logger.warning(f"The file {file} already exists in {target_folder}. Skipping...")

def unify_no_location(base_dir):
    """
    Unify the images from the 'No_Location' folder with existing location folders
    if the dates match.
    """
    no_location_dir = os.path.join(base_dir, "No_Location")
    if not os.path.exists(no_location_dir):
        logger.info("No 'No_Location' folder found, skipping unification.")
        return

    date_pattern = re.compile(r'^\d{2}-\d{2}-\d{2}$')
    date_destinations = {}

    # Index existing date folders by date
    for folder in os.listdir(base_dir):
        if folder == "No_Location":
            continue
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            for subfolder in os.listdir(folder_path):
                subfolder_path = os.path.join(folder_path, subfolder)
                if os.path.isdir(subfolder_path) and date_pattern.match(subfolder):
                    date = subfolder
                    date_destinations[date] = subfolder_path

    # Unify no_location files
    for date_folder in os.listdir(no_location_dir):
        date_folder_path = os.path.join(no_location_dir, date_folder)
        if os.path.isdir(date_folder_path) and date_pattern.match(date_folder):
            date = date_folder
            if date in date_destinations:
                destination_path = date_destinations[date]
                for file in os.listdir(date_folder_path):
                    file_path = os.path.join(date_folder_path, file)
                    if os.path.isfile(file_path):
                        shutil.move(file_path, os.path.join(destination_path, file))
                        logger.info(f"File {file} moved from {date_folder_path} to {destination_path}")
                # Remove empty folder
                if not os.listdir(date_folder_path):
                    os.rmdir(date_folder_path)
                    logger.info(f"Empty folder {date_folder_path} removed")

def main():
    logger.info("Starting file organization...")
    organize_files(BASE_FOLDER, OUTPUT_FOLDER)
    logger.info("Initial organization completed. Starting No_Location unification...")
    unify_no_location(OUTPUT_FOLDER)
    logger.info("Process completed.")

if __name__ == "__main__":
    main()
