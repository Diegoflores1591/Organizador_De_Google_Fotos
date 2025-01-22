import os
import logging
import shutil
import re
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import exifread
from opencage.geocoder import OpenCageGeocode
import sqlite3

# -------------------------- CONSTANTES --------------------------
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.mkv', '.avi')
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(PROJECT_ROOT, "organizacion.log")
DATABASE_FILE = os.path.join(PROJECT_ROOT, "location_cache.db")
FECHA_REGEX_PATTERN = re.compile(r'^\d{2}-\d{2}-\d{2}$')

OPENCAGE_API_KEY = ""
BASE_FOLDER = ""
OUTPUT_FOLDER = ""

class PhotoVideoOrganizer:
    def __init__(self, api_key, base_folder, output_folder, progress_callback=None):
        self.api_key = api_key
        self.base_folder = base_folder
        self.output_folder = output_folder
        self.progress_callback = progress_callback

        self._init_logging()
        self._init_database()

        self.geocoder = OpenCageGeocode(self.api_key)

        logging.info("PhotoVideoOrganizer inicializado.")
        logging.debug(f"Carpeta base: {self.base_folder}")
        logging.debug(f"Carpeta destino: {self.output_folder}")

    def organize(self):
        logging.info("Iniciando organización de archivos...")
        self._organize_files()
        logging.info("Organización inicial completada. Unificando 'Sin_Ubicacion'...")
        self._unir_sin_ubicacion()
        logging.info("Proceso completado.")

    def _init_logging(self):
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%d-%m-%Y %H:%M:%S'
        )
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s', '%d-%m-%Y %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logging.getLogger().addHandler(console_handler)

    def _init_database(self):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS location_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lat REAL,
                lon REAL,
                city TEXT,
                state TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    @staticmethod
    def _save_location_to_cache(lat, lon, city, state):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO location_cache (lat, lon, city, state) VALUES (?, ?, ?, ?)",
            (lat, lon, city, state)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def _get_location_from_cache(lat, lon):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT city, state FROM location_cache WHERE lat = ? AND lon = ?",
            (lat, lon)
        )
        result = cursor.fetchone()
        conn.close()
        return result

    @staticmethod
    def _dms2dd(degrees, minutes, seconds, direction):
        dd = float(degrees) + float(minutes)/60 + float(seconds)/3600
        if direction in ['S', 'W']:
            dd *= -1
        return dd

    def _parse_gps_info(self, gps_info):
        def _extract_dms(rational_list):
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
                d, m, s = _extract_dms(gps_info["GPSLatitude"].values)
                lat_dir = lat_ref.printable if lat_ref else 'N'
                lat = self._dms2dd(d, m, s, lat_dir)

            if "GPSLongitude" in gps_info:
                d, m, s = _extract_dms(gps_info["GPSLongitude"].values)
                lon_dir = lon_ref.printable if lon_ref else 'E'
                lon = self._dms2dd(d, m, s, lon_dir)

            if lat is not None and lon is not None:
                return (lat, lon)
        except Exception as e:
            logging.error(f"Error al procesar coordenadas GPS: {e}")
        return None

    def _get_city_state_name(self, lat, lon):
        cached_location = self._get_location_from_cache(lat, lon)
        if cached_location:
            city, state = cached_location
            return f"{city} - {state}"

        try:
            results = self.geocoder.reverse_geocode(lat, lon)
            if results and 'components' in results[0]:
                components = results[0]['components']
                city = (
                    components.get('city') or
                    components.get('town') or
                    components.get('village') or
                    components.get('municipality')
                )
                state = components.get('state')
                if city and state:
                    self._save_location_to_cache(lat, lon, city, state)
                    return f"{city} - {state}"
        except Exception as e:
            logging.error(f"Error al convertir coordenadas: {e}")

        return "Sin_Ubicacion"

    def _get_metadata_from_exif(self, image_path):
        date = None
        location = None
        try:
            with open(image_path, 'rb') as img_file:
                tags = exifread.process_file(img_file)
                if "EXIF DateTimeOriginal" in tags:
                    date_str = tags["EXIF DateTimeOriginal"].values
                    date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")

                gps_info = {}
                for tag, value in tags.items():
                    if tag.startswith("GPS"):
                        gps_info[tag] = value
                if gps_info:
                    coords = self._parse_gps_info(gps_info)
                    if coords:
                        location = coords
        except Exception as e:
            logging.error(f"Error al leer EXIF de {image_path}: {e}")
        return date, location

    def _get_final_metadata(self, file_path):
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        date, location = None, None
        if ext in IMAGE_EXTENSIONS:
            date_exif, coords_exif = self._get_metadata_from_exif(file_path)
            if date_exif is not None:
                date = date_exif
            if coords_exif is not None:
                location = coords_exif

        return date, location

    def _organize_files(self):
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        for root, _, files in os.walk(self.base_folder):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                ext = os.path.splitext(file_name)[1].lower()

                if ext in IMAGE_EXTENSIONS or ext in VIDEO_EXTENSIONS:
                    date, coordinates = self._get_final_metadata(file_path)

                    location_folder = "Sin_Ubicacion"
                    if coordinates:
                        location_folder = self._get_city_state_name(*coordinates)

                    date_folder = "Sin_Fecha"
                    if date:
                        date_folder = date.strftime('%d-%m-%y')

                    target_folder = os.path.join(self.output_folder, location_folder, date_folder)
                    os.makedirs(target_folder, exist_ok=True)

                    dest_path = os.path.join(target_folder, file_name)
                    if not os.path.exists(dest_path):
                        shutil.copy(file_path, dest_path)
                        logging.info(f"Copiado: {file_path} -> {target_folder}")

                        if self.progress_callback:
                            self.progress_callback()
                    else:
                        logging.warning(
                            f"Archivo duplicado {file_name} en {target_folder}. Ignorando..."
                        )

    def _unir_sin_ubicacion(self):
        sin_ubicacion_dir = os.path.join(self.output_folder, "Sin_Ubicacion")
        if not os.path.exists(sin_ubicacion_dir):
            logging.info("No existe carpeta 'Sin_Ubicacion'; no se realiza la unificación.")
            return

        fechas_destinos = {}
        for carpeta in os.listdir(self.output_folder):
            if carpeta == "Sin_Ubicacion":
                continue
            ruta_carpeta = os.path.join(self.output_folder, carpeta)
            if os.path.isdir(ruta_carpeta):
                for subcarpeta in os.listdir(ruta_carpeta):
                    ruta_subcarpeta = os.path.join(ruta_carpeta, subcarpeta)
                    if os.path.isdir(ruta_subcarpeta) and FECHA_REGEX_PATTERN.match(subcarpeta):
                        fechas_destinos[subcarpeta] = ruta_subcarpeta

        for fecha_carpeta in os.listdir(sin_ubicacion_dir):
            ruta_fecha_carpeta = os.path.join(sin_ubicacion_dir, fecha_carpeta)
            if os.path.isdir(ruta_fecha_carpeta) and FECHA_REGEX_PATTERN.match(fecha_carpeta):
                if fecha_carpeta in fechas_destinos:
                    ruta_destino = fechas_destinos[fecha_carpeta]
                    for archivo in os.listdir(ruta_fecha_carpeta):
                        ruta_archivo = os.path.join(ruta_fecha_carpeta, archivo)
                        if os.path.isfile(ruta_archivo):
                            shutil.move(ruta_archivo, os.path.join(ruta_destino, archivo))
                            logging.info(f"Movido {archivo} de {ruta_fecha_carpeta} a {ruta_destino}")

                    if not os.listdir(ruta_fecha_carpeta):
                        os.rmdir(ruta_fecha_carpeta)
                        logging.info(f"Carpeta vacía eliminada: {ruta_fecha_carpeta}")

def main(api_key, base_folder, output_folder, progress_callback=None):
    organizer = PhotoVideoOrganizer(
        api_key,
        base_folder,
        output_folder,
        progress_callback
    )
    organizer.organize()

if __name__ == "__main__":
    main("", "", "")
