# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 17:42:02 2020

@author: SimoneVaccari
"""

%%writefile app.py

# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 16:48:04 2020

@author: SimoneVaccari
"""

import streamlit as st
from streamlit_folium import folium_static
import folium
import geopandas as gpd
from osgeo import gdal
from matplotlib import cm
import matplotlib.pyplot as plt
import os
from shapely.geometry import Point
import branca #https://stackoverflow.com/questions/52911688/python-folium-choropleth-map-colors-incorrect/52981115#52981115
import rasterio as rio

def getRasterBounds(rst_g):
    ulx, xres, xskew, uly, yskew, yres  = rst_g.GetGeoTransform()
    lrx = ulx + (rst_g.RasterXSize * xres)
    lry = uly + (rst_g.RasterYSize * yres)
    return lry, ulx, uly, lrx

# Datasets
flood_rst_fname = 'geonode_flood_hazard_map.tif'
flood_rst_g = gdal.Open(flood_rst_fname)
flood_rst = flood_rst_g.ReadAsArray()
landslide_shp = gpd.read_file('landslides_1_4326.shp')
landslide_json = 'landslides_1_4326.geojson'

# ================================================
st.title("Extract Values")
# Folium Tutorial link: https://python-visualization.github.io/folium/quickstart.html

#======================================================
# Below are some points and expected results for checking
#x, y = (-61.4198, 15.396)
#x, y = (-61.37618,15.43130) # should return 2 & "NO Landslide"
#x, y = (-61.346482,15.393996) # should return 1 & "NO Landslide"

#x, y = (-61.346078,15.394703) # should return 1 & Pol_1
#x, y = (-61.419855,15.396184) # should return 3 & Pol_1771 # this is outside the AOI clip
#x, y = (-61.415726,15.399853) # should return 1 & Pol_16 
x, y = (-61.413723,15.402079) # should return 5 & Pol_16 # this is outside the AOI clip

longitude=x; latitude=y

m = folium.Map(location=[latitude, longitude], zoom_start=10)

# Show Landslide GeoJSON to the map
folium.GeoJson(
    landslide_json,
    name='Landslide Shapefile'
).add_to(m)
#-------------

# Show Raster on the Map
showRaster = True
if showRaster:
    # Calculate bounds of the raster data
    lat_min, lon_min, lat_max, lon_max = getRasterBounds(flood_rst_g)
    
    #colormap_cm = branca.colormap.linear.YlOrRd_09.scale(1, 5)
    #colormap = colormap_cm.to_step(index=[1, 2, 3, 4, 5])
    #colormap.caption = 'Flood Risk'
    #colormap.add_to(m)
    
    # Setup colormap
    colors = ['#2b83ba', '#abdda4', '#ffffbf', '#fdae61', '#d7191c']
    levels = len(colors)
    cmap = branca.colormap.LinearColormap(colors, vmin=1, vmax=5).to_step(levels)
    cmap.add_to(m)
    
    # add the Flood Risk raster to the map https://python-visualization.github.io/folium/modules.html#module-folium.raster_layers
    folium.raster_layers.ImageOverlay(
        flood_rst,
        bounds=[[lat_min, lon_min], [lat_max, lon_max]],
        opacity=1,
        name='Flood Risk Raster',
        #colormap=cm.viridis # plt.get_cmap('RdYlGn'),#      cm.colors.ListedColormap(colors), #cmap, #cm.get_cmap(plt.get_cmap('YlOrRd')), # would be good to match with the branca colormap YlOrRd_09 below, but not working for some reason... https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html; programcreek.com/python/example/90946/matplotlib.cm.get_cmap
    ).add_to(m)

#--------------

# add marker 
tooltip = "Selected Point"
folium.Marker(
    [latitude, longitude], tooltip=tooltip
).add_to(m)

# Enable lat-long Popup; LayerControl; Call to render Folium map in Streamlit
m.add_child(folium.LatLngPopup())
folium.LayerControl().add_to(m)
folium_static(m)
#--------------------------------------
p = Point(longitude,latitude)
st.header('Extracting Results for the location:\n(Lat: ' + str(latitude) +' & Long: ' + str(longitude) + ')')

# ======= Get Value from Shapefile
landslide_code = 'No Landslide'

# From a given Point coordinates, quickly/efficiently check if it's contained in any polygons geometry, and print out the LANDSLIDE code of that polygon if so. 
# this works, but is this teh most efficient way?!? Think it can be improved with lampda / apply / map, without iterating on the whole dataframe?
for elem in landslide_shp.loc[:,'geometry']:
  if p.within(elem): 
    landslide_code = landslide_shp.loc[landslide_shp.loc[:,'geometry'] == elem]['LANDSLIDES'].values[0]
st.text('The point is contained in the polygon: '+ landslide_code)

# ======= Get Value from Raster
flood = rio.open(flood_rst_fname)
flood_band = flood.read(1)
row, col = flood.index(x, y)
frisk = flood_band[row, col]

st.text('Flood risk category: ' + str(frisk))
