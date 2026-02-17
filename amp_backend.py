import geopandas as gpd
# Input a kml file
# Sample points
# Make path
# Export plan file

from matplotlib.collections import LineCollection

PATH = "/Users/noahpikielny/Downloads/KML_Samples-2.kml"

gpd.read_file(PATH, driver="KML")

import fiona
import contextily as ctx
import matplotlib.pyplot as plt

import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon
import matplotlib.pyplot as plt

def sample_points_in_polygon(polygon, num_points):
    """
    Uniformly sample points inside a polygon or multipolygon.
    """
    points = []
    
    minx, miny, maxx, maxy = polygon.bounds

    n = int(np.sqrt(num_points))

    X, Y = np.meshgrid(np.linspace(minx, maxx, n), np.linspace(miny, maxy, n))
    for (x, y) in zip(X.flatten(), Y.flatten()):
        p = Point(x, y)
        if polygon.contains(p):
            points.append([x, y])
    # while len(points) < num_points:
    #     # Random point within bounding box
    #     x = np.random.uniform(minx, maxx)
    #     y = np.random.uniform(miny, maxy)
    #     p = Point(x, y)
    #     if polygon.contains(p):
    #         points.append(p)
    
    return np.array(points)

# def get_path(point, v, remaining):
#     if len(remaining) == 0:
#         return [point]
#     else:
#         print(len(remaining))
#     v = remaining - point
#     norm = np.linalg.norm(v, axis=-1) # slightly wrong bc missing lat,lon jacobian
#     cos = np.vecdot(v / norm[..., np.newaxis], v[np.newaxis, :])

#     loss = norm - cos * 1e-2
#     best_id = np.argmin(loss)
#     best = remaining[best_id]
#     v = best - point
#     v /= np.linalg.norm(v)
#     return [point] + get_path(best, v, np.vstack([remaining[:best_id], remaining[best_id + 1:]]))

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

        loss = norm - cos * 1e-2
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



def get_best_path_exhaustive(points):
    best = np.inf
    best_path = []
    dirs = np.array([
        [0, 1],
        [0, -1],
        [1, 0],
        [-1, 0],
    ])
    for start in range(len(points)):
        print(start / len(points))
        for dir in dirs:
            p = np.array(get_path(
                start,
                points,
                dir
            ))
            d = np.sum(np.linalg.norm(p[:1] - p[:-1], axis=-1))
            if d < best:
                best = d
                best_path = p
    return best_path

def get_best_path_random(n_tests, points):
    best = np.inf
    best_path = []
    if n_tests >= len(points):
        print("large n, shifting to exhaustive")
        return get_best_path_exhaustive(points)
    print(n_tests, len(points))
    for _ in range(n_tests):
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



        

print(fiona.listlayers(PATH))

gdf = gpd.read_file(PATH, layer="Extruded Polygon")

num_points = 100

# Sample points for all polygons
sampled_points = []
for geom in gdf.geometry:
    if geom.is_empty:
        continue
    if geom.type == "Polygon":
        sampled_points.extend(sample_points_in_polygon(geom, num_points))
    elif geom.type == "MultiPolygon":
        for poly in geom.geoms:
            sampled_points.extend(sample_points_in_polygon(poly, num_points))

sampled_points = np.array(sampled_points).reshape((-1, 2))

path = np.array(get_best_path_random(100000, sampled_points))

# fig, ax = plt.subplots(figsize=(8, 8))

# # Plot polygons
# gdf.plot(ax=ax, facecolor="lightblue", edgecolor="black")

# # Plot sampled points
# ax.scatter(sampled_points[:, 0], sampled_points[:, 1], color="red", s=10)
# # ax.plot(
# #     path[:, 0],
# #     path[:, 1],
# # )

# print("PATH LENGTH", len(path), len(sampled_points))

# p = path.reshape((-1, 1, 2))
# segments = np.concatenate([p[:-1], p[1:]], axis=1)

# # Create a LineCollection with a colormap
# lc = LineCollection(segments, cmap='magma', linewidth=2)
# lc.set_array(np.linspace(0, 1, len(p)))  # gradient along the line
# ax.add_collection(lc)

# ax.set_title("Uniformly Sampled Points in Polygons")
# plt.show()
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString
from matplotlib.collections import LineCollection
import contextily as ctx

print(dir(ctx.providers))

gdf_web = gdf.to_crs(epsg=3857)

from shapely.ops import transform
from pyproj import Transformer

transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
sampled_points_web = np.array([transformer.transform(x, y) for x, y in sampled_points])
path_web = np.array([transformer.transform(x, y) for x, y in path])

# Create figure
fig, ax = plt.subplots(figsize=(10, 10))

# Plot polygons
gdf_web.plot(ax=ax, facecolor="lightblue", edgecolor="black")

# Plot sampled points
ax.scatter(sampled_points_web[:, 0], sampled_points_web[:, 1], color="red", s=10)

# Create LineCollection for path with gradient
p = path_web.reshape((-1, 1, 2))
segments = np.concatenate([p[:-1], p[1:]], axis=1)
lc = LineCollection(segments, cmap='magma', linewidth=2)
lc.set_array(np.linspace(0, 1, len(p)))
ax.add_collection(lc)

# Add background map
ctx.add_basemap(ax)

# Set title and axis
ax.set_title("Uniformly Sampled Points in Polygons with Background")
ax.set_axis_off()
plt.show()
