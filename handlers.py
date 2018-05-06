import collections
import json
import math
import struct 
import logging

import jinja2
import webapp2



# Dataset parameters.
N_COLS = 21601
N_ROWS = 10801
RESOLUTION = 1800
CELL_SIZE = 1 / 60
N_BYTES_PER_CELL = 2
N_BYTES_PER_FILE = 30000000
STRUCT_FMT = 'h'
DATASET_PATH = 'data/etopo1_ice_g_i2.bin'

def interp_integer_2d_grid(x, y, z_as_list):
    z = [[z_as_list[0], z_as_list[1]], [z_as_list[2], z_as_list[3]]]
    x = x % 1
    y = y % 1
    return z[0][0] * (1-x) * (1-y) + z[1][0] * x * (1-y) + z[0][1] * (1-x) * y + z[1][1] * x * y


def read_exactly(f, n_bytes):
    data = b""
    remaining = n_bytes
    while remaining > 0:
        newdata = f.read(remaining)
        data += newdata
        remaining -= len(newdata)
    return data


class BaseHandler(webapp2.RequestHandler):
    def add_headers(self):
        '''
        Adds a common set of headers for all responses.
        '''
        self.response.headers.add_header('x-frame-options', 'deny')
        self.response.headers.add_header('x-content-type-options', 'nosniff')
        self.response.headers.add_header('referrer-policy', 'same-origin')
        self.response.headers.add_header('strict-transport-security', 'max-age=31536000; includeSubDomains; preload')


class HomePageHandler(BaseHandler):

    @webapp2.cached_property
    def environment(self):
        '''
        Precomputes the jinja environment.
        '''
        jinja_environmnet = jinja2.Environment(
            autoescape=True,
            loader=jinja2.FileSystemLoader(searchpath='./')
        )
        return jinja_environmnet

    def get(self):
        self.add_headers()
        template = self.environment.get_template('home.html')
        self.response.write(template.render())


class InvalidLatLonError(ValueError):
    pass

class GeoPoint(object):
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        assert -90 <= self.lat <= 90
        assert -180 <= self.lat <= 180

       
    @classmethod
    def from_latlon(cls, latlon):
        parts = latlon.split(',', 1)
        lat = float(parts[0])
        lon = float(parts[1])
        return GeoPoint(lat, lon)
    
    def __repr__(self):
        return '({},{})'.format(self.lat, self.lon)
    
    def __hash__(self):
         return '({},{})'.format(self.lat, self.lon)


class ApiHandler(BaseHandler):
    def render_json(self, data, status_code=200):
        self.add_headers()
        self.response.headers.add_header('content-type', 'application/json')
        self.response.set_status(status_code)
        res = json.dumps(data, sort_keys=True, indent=4)
        self.response.write(res)

    def render_error(self, message, status, status_code=400):
        data = {
            'message': message,
            'results': [],
            'status': status,
        }
        self.render_json(data, status_code=status_code)

    def get(self):
        try:
            # Check input.
            locations = self.request.get('locations')
            locations = locations.split('|')
            if not locations:
                return self.render_error('No locations provided.', 'INVALID_REQUEST')

            # Convert strings to points.
            for i, loc in enumerate(locations):
                try:
                    locations[i] = GeoPoint.from_latlon(loc)
                except:
                    return self.render_error('Invalid location in index {}.'.format(i), 'INVALID_REQUEST')

            # For each point, find the correspoinding grid coord, and the neighbouring ones.
            target_coords = []
            interp_coords = []
            for point in locations:
                grid_x = (point.lon + 180 + CELL_SIZE/2) / (360 + CELL_SIZE) * N_COLS
                grid_y = (90 - point.lat  + CELL_SIZE/2) / (180 + CELL_SIZE) * N_ROWS
                target_coords.append((grid_x, grid_y))

                # Compass positions.
                w = math.floor(grid_x)
                e = math.ceil(grid_x)
                n = math.floor(grid_y)
                s = math.ceil(grid_y)

                # Bounds check.
                w = max(w, 0)
                n = max(n, 0)
                e = min(e, N_COLS-1)
                s = min(s, N_ROWS-1)

                # Sanity check.
                if w == e and w > 0:
                    w = w-1
                elif w == e and w == 0:
                    e = 1
                if n == s and n > 0:
                    n = n-1
                elif n == s and n == 0:
                    s = 1

                interp_coords.append([(n,w), (n,e), (s,w), (s,e)])

            coords = [x for sublist in interp_coords for x in sublist]
            coords.sort()

            # GAE has a restriction on filesize, so I split the binary file
            # up. We can do each file at a time.
            coords_by_file = collections.defaultdict(list)
            for coord in coords:
                    n_skip_cells = coord[0] * N_COLS + coord[1]
                    n_skip_bytes = n_skip_cells * N_BYTES_PER_CELL
                    file_index = int(n_skip_bytes // N_BYTES_PER_FILE)
                    filename = 'data/etopo1_ice_g_i2.bin.{:02}'.format(file_index)
                    coords_by_file[filename].append(coord)
                
            # Read requried data from file.
            interp_z = {}
            for filename, coords in coords_by_file.items():
                with open(filename, 'rb') as f:
                    for coord in coords:
                        n_skip_cells = coord[0] * N_COLS + coord[1]
                        n_skip_bytes = n_skip_cells * N_BYTES_PER_CELL
                        n_skip_bytes = n_skip_bytes % N_BYTES_PER_FILE
                        f.seek(n_skip_bytes, 0)
                        interp_z[coord] = read_exactly(f, N_BYTES_PER_CELL)

            # Process the structs.
            interp_z = {k: struct.unpack(STRUCT_FMT, v)[0] for k, v in interp_z.items()}

            # Go through each point.
            elevations = []
            for target, interp in zip(target_coords, interp_coords):
                z = [interp_z.get(c) for c in interp]
                elevation = interp_integer_2d_grid(target[0], target[1], z)
                elevations.append(int(round(elevation)))

            # Prepare the results.
            data = {
                'status': 'OK',
                'results': [{'elevation': e, 'location': {'lat': p.lat, 'lon': p.lon}, 'resolution': RESOLUTION} for e, p in zip(elevations, locations)]
            }
            self.render_json(data)
        except Exception as e:
            logging.error(e)
            self.render_error('Server error.'.format(i), 'SERVER_ERROR', 500)
