import ast, numpy as np, matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, MultiPolygon #Geodesic calculations
# Graphing
from matplotlib.collections import LineCollection
from geographiclib.geodesic import Geodesic
import contextily as ctx
import tqdm
from shapely.ops import transform
from pyproj import Transformer

DATA = """
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -80.163009,
              25.731541
            ],
            [
              -80.16206,
              25.731536
            ],
            [
              -80.162081,
              25.730599
            ],
            [
              -80.162859,
              25.730604
            ],
            [
              -80.163009,
              25.731541
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -80.164452,
              25.730913
            ],
            [
              -80.164452,
              25.731179
            ],
            [
              -80.163894,
              25.731179
            ],
            [
              -80.163894,
              25.730913
            ],
            [
              -80.164452,
              25.730913
            ]
          ]
        ]
      }
    }
  ]
}
"""
def extract_geometry(string_json):
    data = ast.literal_eval(string_json)

    polygons = []
    points = []

    for f in data['features']:
        geo = f['geometry']
        type = geo['type']
        if type == "Point":
            points.append(geo)
        elif type == "Polygon":
            coords = geo["coordinates"][0]  # outer ring
            poly = Polygon(coords)
            polygons.append(poly)
        else:
            print(f"Unknown type: {type}")
    return {"poly": polygons, "pts": points }

RESOLUTION = 5

def generate_points(min_lon, min_lat, max_lon, max_lat, spacing):
    geod = Geodesic.WGS84
    points = []

    east = geod.Direct(min_lat, min_lon, 90, spacing[0])
    dLon = east['lon2'] - min_lon
    north = geod.Direct(min_lat, min_lon, 0, spacing[1])
    dLat = north['lat2'] - min_lat

    NLon = max(int(np.ceil((max_lon - min_lon) / dLon)), 3)
    NLat = max(int(np.ceil((max_lat - min_lat) / dLat)), 3)

    lon = np.linspace(min_lon + 1e-8, max_lon - 1e-8, NLon)
    lat = np.linspace(min_lat + 1e-8, max_lat - 1e-8, NLat)
    LAT, LON = np.meshgrid(lat, lon)
    res = np.dstack([LON, LAT])
    return res


def points_from_poly(poly, resolution):
    """
    Uniformly sample points inside a polygon or multipolygon.
    """
    points = []
    
    minx, miny, maxx, maxy = poly.bounds

    r = generate_points(minx, miny, maxx, maxy, resolution)

    nx = max(4, int(np.ceil((maxx - minx) / resolution)))
    ny = max(4, int(np.ceil((maxx - minx) / resolution)))

    Y, X = np.meshgrid(np.linspace(miny, maxy, ny), np.linspace(minx, maxx, nx))
    for (x, y) in zip(X.flatten(), Y.flatten()):
        p = Point(x, y)
        if poly.contains(p):
            points.append([x, y])

    return points

def get_poly_path(poly, spacing, progress):
    points = generate_points(*poly.bounds, spacing)

    points[::2] = points[::2, ::-1, :]
    directions = np.ones(points.shape[:2])
    directions[::2] *= -1
    directions = directions.flatten()
    points = points.reshape((-1, 2))

    mask = np.array([poly.contains(Point(point[0], point[1])) for point in progress.tqdm(points, "Fitting points to shape")])
    return points[mask], directions[mask].flatten()


def get_path(point_id, points, v = np.zeros(2)):
    point = points[point_id]
    remaining = np.vstack([
        points[:point_id],
        points[1 + point_id:]
    ])

    points = [point]
    while len(remaining) > 0:
        d = remaining - point
        norm = np.linalg.norm(d, axis=-1) # slightly wrong bc missing lat,lon jacobian
        cos = np.vecdot(d / norm[..., np.newaxis], v[np.newaxis, :])

        loss = norm - cos * 1e-16
        best_id = np.argmin(loss)
        best = remaining[best_id]
        v = best - point
        v /= np.linalg.norm(v)
        points.append(best)
        point = best
        remaining = np.vstack([
            remaining[:best_id],
            remaining[best_id + 1:]
        ])
    return points

def get_best_path_exhaustive(points, progress=tqdm):
    best = np.inf
    best_path = []
    dirs = np.array([
        [0, 1],
        [0, -1],
        [1, 0],
        [-1, 0],
    ])
    for start in progress.tqdm(range(len(points)), "Finding Optimal Flight Path (Exact)"):
        for dir in dirs:
            p = np.array(get_path(
                start,
                points,
                dir
            ))
            d = np.sum(np.linalg.norm(p[1:] - p[:-1], axis=-1))
            if d < best:
                best = d
                best_path = p
    return best_path

def get_best_path_random(n_tests, points, progress=tqdm):
    best = np.inf
    best_path = []
    if n_tests >= len(points):
        print("large n, shifting to exhaustive")
        return get_best_path_exhaustive(points, progress=progress)
    for _ in progress.tqdm(range(n_tests), "Finding Optimal Flight Path (Approximate)"):
        start = np.random.randint(0, len(points))
        p = np.array(get_path(
            start,
            points
        ))
        d = np.sum(np.linalg.norm(p[:1] - p[:-1], axis=-1))
        if d < best:
            best = d
            best_path = p
    return p

def connect_paths(paths):
    best_score = np.inf
    best = []
    for i in range(len(paths)):
        last = paths[i]
        path = list(last)
        remaining = list(paths[:i]) + list(paths[i + 1:])
        score = 0
        while len(remaining) > 1:
            st = np.array([i[0] for i in remaining])
            loss = np.linalg.norm(st - np.array(last[-1])[np.newaxis, ...], axis=-1)
            best_id = np.argmin(loss)
            score += loss[best_id]
            last = paths[best_id]
            path += list(last)
            remaining = list(remaining[:best_id]) + list(remaining[best_id + 1:])
        for i in remaining:
            path += list(i)

        if score < best_score:
            best_score = score
            best = path
    return best

"""
Ocean Sampling Distance

Equivalent to ground sampling distance, but at MSL

Inputs:
- altitude [meters]
- fov [°]
– res_v: vertical resolution dimension [pixels] 
– res_h: horizontal resolution dimension [pixels]
- overlap_v: vertical overlap (%)
- overlap_h: vertical overlap (%)
"""
def compute_sampling_spacing(altitude, fov, res_v, res_h, overlap_v=60.0, overlap_h=70.0):
    if overlap_v > 1:
        overlap_v /= 100
    if overlap_h > 1:
        overlap_h /= 100

    # The dimension of the ocean visible by the camera
    # i.e. [30m, 20m], so an overlap of 50% would mean a translation of [15m, 10m]
    view_frustum = np.tan(fov / (2 * 180) * np.pi) * altitude * np.array([res_v, res_h]) / np.linalg.norm([res_v, res_h]) * 2
    return view_frustum * (1 - np.array([overlap_v, overlap_h]))

# import geopandas as gdf
def show_results(polygons, points, path, directions, plot=None, progress=tqdm):
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    sampled_points_web = np.array([transformer.transform(x, y) for x, y in progress.tqdm(points, "Transforming Points")])#.reshape((-1, 2))
    path_web = np.array([transformer.transform(x, y) for x, y in progress.tqdm(path.reshape((-1, 2)), "Transforming Path")])

    # Create figure
    if plot is None:
        fig, ax = plt.subplots(figsize=(10, 10))
    else:
        fig, ax = plot
    ax.scatter(sampled_points_web[:, 0], sampled_points_web[:, 1], c=directions, s=20, cmap='jet', zorder=10)

    # Create LineCollection for path with gradient
    p = path_web.reshape((-1, 1, 2))
    ax.set_aspect('equal')
    segments = np.concatenate([p[:-1], p[1:]], axis=1)
    lc = LineCollection(segments, cmap='magma', linewidth=2, zorder=1)
    lc.set_array(np.linspace(0, 1, len(p)))
    ax.add_collection(lc)

    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")

    # Add background map
    ctx.add_basemap(ax)

    # Set title and axis
    ax.set_axis_off()
    plt.show()

def get_paths_for_data(data_str, altitude=60, fov=53.3, v_res=5460, h_res=8192, seperate_paths=False, progress=tqdm):
    geo = extract_geometry(data_str)
    points = []
    directions = []
    for pt in geo['pts']:
        points.append(pt['coordinates'])

    paths = []
    if len(points) > 0:
        paths.append(get_best_path_random(500, np.array(points)))

    spacing = compute_sampling_spacing(altitude, 53.3, 5460, 8192)

    if seperate_paths:
        for p in progress.tqdm(geo['poly'], "Unpacking polygons"):
            pts, dirs = get_poly_path(p, spacing, progress)
            points.extend(pts)
            directions.extend(dirs.flatten())
            paths.append(pts)
        points = np.array(points)

        paths = np.array(connect_paths(paths))
        return (geo['poly'], np.array(points).reshape((-1, 2)), np.array(paths).reshape((-1, 2)), directions)
    else:
        geo['poly'] = [MultiPolygon(geo['poly'])]
        points, directions = get_poly_path(geo['poly'][0], spacing, progress)
        paths = points
        return (geo['poly'], np.array(points).reshape((-1, 2)), np.array(paths).reshape((-1, 2)), directions.flatten())

if __name__ == "__main__":
    poly, points, path = get_paths_for_data(DATA, False)
    show_results(poly, points, path)


