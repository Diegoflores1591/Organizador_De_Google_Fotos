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

# ------------------------ CONFIGURACIÓN --------------------------
OPENCAGE_API_KEY = "Tu clave"  # Reemplazar con la propia clave
BASE_FOLDER = r"ruta\de\la\carpeta\de\Google\Takeout\Photos from" # Reemplazar con la ruta de takeout
OUTPUT_FOLDER = r"ruta\de\la\carpeta\de\destino" # Reemplazar con la ruta de destino

# Extensiones soportadas
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.mkv', '.avi')

# Archivos de registro y caché
LOG_FILE = os.path.join(OUTPUT_FOLDER, "organizacion.log")
CACHE_FILE = os.path.join(OUTPUT_FOLDER, "location_cache.json")

# ------------------------ LOGGING --------------------------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S'
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s','%d-%m-%Y %H:%M:%S')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

logger = logging.getLogger(__name__)

# ------------------------ GEOLOCALIZACIÓN --------------------------
geocoder = OpenCageGeocode(OPENCAGE_API_KEY)

# Cargar o inicializar caché de ubicaciones
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        location_cache = json.load(f)
else:
    location_cache = {}

def save_location_cache():
    """Guarda el caché de ubicaciones en disco."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(location_cache, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error guardando caché de ubicaciones: {e}")

def dms2dd(degrees, minutes, seconds, direction):
    """Convierte coordenadas en DMS (grados, minutos, segundos) a decimal (DD)."""
    dd = float(degrees) + float(minutes)/60 + float(seconds)/3600
    if direction in ['S', 'W']:
        dd *= -1
    return dd

def parse_gps_info(gps_info):
    """Convierte la información GPS en un tuple (lat, lon)."""
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
        logger.error(f"Error al procesar coordenadas GPS: {e}")
    return None

def get_city_state_name(lat, lon):
    """
    Dadas coordenadas (lat, lon), obtiene la ubicación en forma "Ciudad - Estado".
    Si no se puede obtener, retorna "Sin_Ubicacion".
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
        logger.error(f"Error al convertir coordenadas: {e}")

    location_cache[latlon_key] = "Sin_Ubicacion"
    save_location_cache()
    return "Sin_Ubicacion"

def get_metadata_from_exif(image_path):
    """Extrae la fecha y ubicación desde EXIF de una imagen."""
    date = None
    location = None
    try:
        with open(image_path, 'rb') as img_file:
            tags = exifread.process_file(img_file)
            # Fecha
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
        logger.error(f"Error al leer EXIF de {image_path}: {e}")
    return date, location

def get_metadata_from_json(json_path):
    """Lee metadatos (ubicación y fecha) desde un archivo JSON."""
    date = None
    coords = None
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Fecha
        if "photoTakenTime" in data and "timestamp" in data["photoTakenTime"]:
            ts = int(data["photoTakenTime"]["timestamp"])
            date = datetime.fromtimestamp(ts)

        # Ubicación
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
        logger.error(f"Error leyendo {json_path}: {e}")

    return date, coords

def get_final_metadata(file_path):
    """
    Intenta extraer metadatos (fecha, ubicación) del JSON asociado.
    Si no existen o faltan datos, para imágenes intenta EXIF.
    """
    base_name, ext = os.path.splitext(file_path)
    json_path = file_path + ".json"
    date, location = None, None

    # Intentar desde JSON
    if os.path.exists(json_path):
        date_json, coords_json = get_metadata_from_json(json_path)
        if date_json is not None:
            date = date_json
        if coords_json is not None:
            location = coords_json

    # Si es imagen y faltan datos, intentar EXIF
    if ext.lower() in IMAGE_EXTENSIONS:
        if date is None or location is None:
            date_exif, coords_exif = get_metadata_from_exif(file_path)
            if date is None:
                date = date_exif
            if location is None:
                location = coords_exif

    return date, location

def organize_files(base_folder, output_folder):
    """Organiza imágenes y videos en carpetas según ubicación y fecha."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for root, _, files in os.walk(base_folder):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            if ext in IMAGE_EXTENSIONS or ext in VIDEO_EXTENSIONS:
                date, coordinates = get_final_metadata(file_path)

                # Ubicación
                location_folder = "Sin_Ubicacion"
                if coordinates:
                    location_folder = get_city_state_name(*coordinates)

                # Fecha
                date_folder = "Sin_Fecha"
                if date:
                    date_folder = date.strftime('%d-%m-%y')

                target_folder = os.path.join(output_folder, location_folder, date_folder)
                os.makedirs(target_folder, exist_ok=True)

                dest_path = os.path.join(target_folder, file)
                if not os.path.exists(dest_path):
                    shutil.copy(file_path, dest_path)
                    logger.info(f"Movido: {file_path} -> {target_folder}")
                else:
                    logger.warning(f"El archivo {file} ya existe en {target_folder}. Ignorando...")

def unir_sin_ubicacion(base_dir):
    """
    Unifica las imágenes sin ubicación con las carpetas de misma fecha
    en las ubicaciones ya existentes.
    """
    sin_ubicacion_dir = os.path.join(base_dir, "Sin_Ubicacion")
    if not os.path.exists(sin_ubicacion_dir):
        logger.info("No existe carpeta Sin_Ubicacion, no se realiza la unificación.")
        return

    fecha_pattern = re.compile(r'^\d{2}-\d{2}-\d{2}$')
    fechas_destinos = {}

    # Indexar rutas por fecha en carpetas con ubicación
    for carpeta in os.listdir(base_dir):
        if carpeta == "Sin_Ubicacion":
            continue
        ruta_carpeta = os.path.join(base_dir, carpeta)
        if os.path.isdir(ruta_carpeta):
            for subcarpeta in os.listdir(ruta_carpeta):
                ruta_subcarpeta = os.path.join(ruta_carpeta, subcarpeta)
                if os.path.isdir(ruta_subcarpeta) and fecha_pattern.match(subcarpeta):
                    fecha = subcarpeta
                    fechas_destinos[fecha] = ruta_subcarpeta

    # Unificar sin ubicación
    for fecha_carpeta in os.listdir(sin_ubicacion_dir):
        ruta_fecha_carpeta = os.path.join(sin_ubicacion_dir, fecha_carpeta)
        if os.path.isdir(ruta_fecha_carpeta) and fecha_pattern.match(fecha_carpeta):
            fecha = fecha_carpeta
            if fecha in fechas_destinos:
                ruta_destino = fechas_destinos[fecha]
                for archivo in os.listdir(ruta_fecha_carpeta):
                    ruta_archivo = os.path.join(ruta_fecha_carpeta, archivo)
                    if os.path.isfile(ruta_archivo):
                        shutil.move(ruta_archivo, os.path.join(ruta_destino, archivo))
                        logger.info(f"Archivo {archivo} movido de {ruta_fecha_carpeta} a {ruta_destino}")
                if not os.listdir(ruta_fecha_carpeta):
                    os.rmdir(ruta_fecha_carpeta)
                    logger.info(f"Carpeta vacía {ruta_fecha_carpeta} eliminada")

def main():
    logger.info("Iniciando organización de archivos...")
    organize_files(BASE_FOLDER, OUTPUT_FOLDER)
    logger.info("Organización inicial completada. Iniciando unificación de Sin_Ubicacion...")
    unir_sin_ubicacion(OUTPUT_FOLDER)
    logger.info("Proceso completado.")

if __name__ == "__main__":
    main()
