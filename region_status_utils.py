# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 15:26:04 2019

@author: buriona
"""

import re
import json
from os import path
import branca
import folium
import pandas as pd
# import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime
from requests import get as r_get

STATIC_URL = f'https://www.usbr.gov/uc/water/hydrodata/assets'
NRCS_URL = r'https://www.nrcs.usda.gov/Internet/WCIS/basinCharts/POR'
GIS_URL = r'https://www.usbr.gov/uc/water/hydrodata/assets/gis'

def get_plotly_js():
    return f'{STATIC_URL}/plotly.js'

def get_favicon():
    return f'{STATIC_URL}/img/favicon.ico'

def get_bootstrap():
    return {
        'css': f'{STATIC_URL}/bootstrap/css/bootstrap.min.css',
        'js': f'{STATIC_URL}/bootstrap/js/bootstrap.bundle.js',
        'jquery': f'{STATIC_URL}/jquery.js',
        'popper': f'{STATIC_URL}/popper.js',
        'fa': f'{STATIC_URL}/font-awesome/css/font-awesome.min.css',
    }

def get_bor_seal(orient='default', grey=False):
    color = 'cmyk'
    if grey:
        color = 'grey'
    seal_dict = {
        'default': f'BofR-horiz-{color}.png',
        'shield': f'BofR-shield-cmyk.png',
        'vert': f'BofR-vert-{color}.png',
        'horz': f'BofR-horiz-{color}.png'
        }
    return f'{STATIC_URL}/img/{seal_dict[orient]}'

def get_bor_js():
    return [
        ('leaflet',
          f'{STATIC_URL}/js/leaflet/leaflet.js'),
        ('jquery',
          f'{STATIC_URL}/js/jquery/3.4.0/jquery.min.js'),
        ('bootstrap',
          f'{STATIC_URL}/js/bootstrap/3.2.0/js/bootstrap.min.js'),
        ('awesome_markers',
          f'{STATIC_URL}/js/leaflet/leaflet.awesome-markers.js'),  # noqa
        ]

def get_bor_css():
    return [
        ('leaflet_css',
          f'{STATIC_URL}/css/leaflet/leaflet.css'),
        ('bootstrap_css',
          f'{STATIC_URL}/css/bootstrap/3.2.0/css/bootstrap.min.css'),
        ('bootstrap_theme_css',
          f'{STATIC_URL}/css/bootstrap/3.2.0/css/bootstrap-theme.min.css'),  # noqa
        ('awesome_markers_font_css',
          f'{STATIC_URL}/css/font-awesome.min.css'),  # noqa
        ('awesome_markers_css',
          f'{STATIC_URL}/css/leaflet/leaflet.awesome-markers.css'),  # noqa
        ('awesome_rotate_css',
          f'{STATIC_URL}/css/leaflet/leaflet.awesome.rotate.css'),  # noqa
        ]

def get_default_js():
    bootstrap_dict = get_bootstrap()
    return [
        ('leaflet', 
         f'{STATIC_URL}/leaflet/js/leaflet.js'),
        ('jquery', 
         bootstrap_dict['jquery']),
        ('bootstrap', 
         bootstrap_dict['js']),
        ('awesome_markers', 
         f'{STATIC_URL}/leaflet-awesome-markers/leaflet.awesome-markers.min.js'),
        ('popper', 
         bootstrap_dict['popper']),
    ]


def get_default_css():
    bootstrap_dict = get_bootstrap()
    return [
        ('leaflet_css', 
         f'{STATIC_URL}/leaflet/css/leaflet.css'),
        ('bootstrap_css', 
         bootstrap_dict['css']),
        ('awesome_markers_font_css', 
          bootstrap_dict['fa']),
        ('awesome_markers_css', 
        f'{STATIC_URL}/leaflet-awesome-markers/leaflet.awesome-markers.css'),
        ('awesome_rotate_css', 
         f'{STATIC_URL}/leaflet-awesome-markers/leaflet.awesome.rotate.css'),
    ]

def get_fa_icon(obj_type='default', source='hdb'):
    if source.lower() == 'hdb':
        fa_dict = {
            'default': 'map-pin',
            1: 'sitemap',
            2: 'umbrella',
            3: 'arrow-down',
            4: 'exchange',
            5: 'plug',
            6: 'arrows-v',
            7: 'tint',
            8: 'snowflake-o',
            9: 'tachometer',
            10: 'cogs',
            11: 'arrows-h',
            12: 'rss',
            13: 'flask',
            14: 'table',
            15: 'info',
            20: 'exchange'
        }
    if source.lower() == 'awdb':
        fa_dict = {
            'default': 'map-pin',
            'SCAN': 'umbrella',
            'PRCP': 'umbrella',
            'BOR': 'tint',
            'SNTL': 'snowflake-o',
            'SNOW': 'snowflake-o',
            'SNTLT': 'snowflake-o',
            'USGS': 'tachometer',
            'MSNT': 'snowflake-o',
            'MPRC': 'umbrella'
        }
    fa_icon = fa_dict.get(obj_type, 'map-pin')
    return fa_icon

def get_icon_color(row, source='hdb'):
    if source.lower() == 'hdb':
        obj_owner = 'BOR'
        if not row.empty:
            if row['site_metadata.scs_id']:
                obj_owner = 'NRCS'
            if row['site_metadata.usgs_id']:
                obj_owner = 'USGS'
    if source.lower() == 'awdb':
        obj_owner = row
    color_dict = {
        'BOR': 'blue',
        'NRCS': 'red',
        'USGS': 'green',
        'COOP': 'gray',
        'SNOW': 'darkred',
        'PRCP': 'lightred',
        'SNTL': 'red',
        'SNTLT': 'lightred',
        'SCAN': 'lightred',
        'MSNT': 'orange',
        'MPRC': 'beige',
        
    }
    icon_color = color_dict.get(obj_owner, 'black')
    return icon_color

def add_optional_tilesets(folium_map):
    tilesets = {
        "Terrain": 'Stamen Terrain',
        'Street Map': 'OpenStreetMap',
        'Toner': 'Stamen Toner',
        'Watercolor': 'Stamen Watercolor',
        'Positron': 'CartoDB positron',
        'Dark Matter': 'CartoDB dark_matter',
    }
    for name, tileset in tilesets.items():
        folium.TileLayer(tileset, name=name).add_to(folium_map)

def add_huc_layer(huc_map, level=2, huc_geojson_path=None, embed=False, show=True, filter_on=None):
    try:
        weight = -0.25 * float(level) + 2.5
        if not huc_geojson_path:
            huc_geojson_path = f'{STATIC_URL}/gis/HUC{level}.geojson'
        else:
            embed = True
        if filter_on:
           huc_style = lambda x: {
            'fillColor': '#ffffff00', 'color': '#1f1f1faa', 
            'weight': weight if x['properties'][f'HUC{level}'][:len(filter_on)] == filter_on else 0
        } 
        else:
            huc_style = lambda x: {
                'fillColor': '#ffffff00', 'color': '#1f1f1faa', 'weight': weight
            }
        folium.GeoJson(
            huc_geojson_path,
            name=f'HUC {level}',
            embed=embed,
            style_function=huc_style,
            show=show
        ).add_to(huc_map)
    except Exception as err:
        print(f'Could not add HUC {level} layer to map! - {err}')

def clean_coords(coord_series, force_neg=False):
    
    coord_series = coord_series.apply(
        pd.to_numeric, 
        errors='ignore', 
        downcast='float'
    )
    if not coord_series.apply(type).eq(str).any():
        if force_neg:
            return -coord_series.abs()
        return coord_series
    results = []
    for idx, coord in coord_series.iteritems():
        if not str(coord).isnumeric():
            coord_strs = str(coord).split(' ')
            coord_digits = []
            for coord_str in coord_strs:
                coord_digit = ''.join([ch for ch in coord_str if ch.isdigit() or ch == '.'])
                coord_digits.append(float(coord_digit))
            dec = None
            coord_dec = 0
            for i in reversed(range(0, len(coord_digits))):
                if dec:
                    coord_dec = abs(coord_digits[i]) + dec
                dec = coord_digits[i] / 60
            if str(coord)[0] == '-':
                coord_dec = -1 * coord_dec
            results.append(coord_dec)
        else:
            results.append(coord)
    if force_neg:
        results[:] = [-1 * result if result > 0 else result for result  in results]
    clean_series = pd.Series(results, index=coord_series.index)
    return clean_series

def get_huc(geo_df, lat, lon, level='12'):

    for idx, row in geo_df.iterrows():
        polygon = row['geometry']
        point = Point(lon, lat)
        if polygon.contains(point):
            return row[f'HUC{level}']
    return None

def get_season():
    curr_month = datetime.now().month
    if curr_month > 3:
        return 'spring'
    if curr_month > 5:
        return 'summer'
    if curr_month > 10:
        return 'fall'
    return 'winter'

def get_nrcs_basin_stat(basin_name, huc_level='2', data_type='wteq'):
    stat_type_dict = {'wteq': 'Median', 'prec': 'Average'}
    url = f'{NRCS_URL}/{data_type.upper()}/assocHUC{huc_level}/{basin_name}.html'
    try:
        response = r_get(url)
        if not response.status_code == 200:
            print(f'      Skipping {basin_name} {data_type.upper()}, NRCS does not publish stats.')
            return 'N/A'
        html_txt = response.text
        stat_type = stat_type_dict.get(data_type, 'Median')
        regex = f"(?<=% of {stat_type} - )(.*)(?=%<br>%)"
        swe_re = re.search(regex, html_txt, re.MULTILINE)
        stat = html_txt[swe_re.start():swe_re.end()]
    except Exception as err:
        print(f'      Error gathering data for {basin_name} - {err}')
        stat = 'N/A'
    return stat
    
def get_huc_nrcs_stats(huc_level='6'):
    topo_json_path = f'./gis/HUC{huc_level}.topojson'
    with open(topo_json_path, 'r') as tj:
        topo_json = json.load(tj)
    huc_str = f'HUC{huc_level}'
    attrs = topo_json['objects'][huc_str]['geometries']
    for attr in attrs:
        props = attr['properties']
        huc_name = props['Name']
        print(f'  Getting NRCS stats for {huc_name}...')
        props['swe_percent'] = get_nrcs_basin_stat(
            huc_name, huc_level=huc_level, data_type='wteq'
        )
        props['prec_percent'] = get_nrcs_basin_stat(
            huc_name, huc_level=huc_level, data_type='prec'
        )
    topo_json['objects'][huc_str]['geometries'] = attrs
    with open(topo_json_path, 'w') as tj:
        json.dump(topo_json, tj)

def add_huc_chropleth(m, data_type='swe', show=False, huc_level='6', 
                      gis_path='gis', filter_str=None, use_topo=False):
    
    huc_str = f'HUC{huc_level}'
    stat_type_dict = {'swe': 'Median', 'prec': 'Avg.'}
    stat_type = stat_type_dict.get(data_type, '')
    layer_name = f'{huc_str} % {stat_type} {data_type.upper()}'
    if use_topo:
        topo_json_path = path.join(gis_path, f'{huc_str}.topojson')
        with open(topo_json_path, 'r') as tj:
            topo_json = json.load(tj)
        if filter_str:
            topo_json = filter_topo_json(
                topo_json, huc_level=huc_level, filter_str=filter_str
            )
    style_function = lambda x: style_chropleth(
        x, data_type=data_type, huc_level=huc_level, huc_filter=filter_str
    )
       
    if use_topo:
        folium.TopoJson(
            topo_json,
            f'objects.{huc_str}',
            name=layer_name,
            overlay=True,
            show=show,
            smooth_factor=2.0,
            style_function=style_function,
            tooltip=folium.features.GeoJsonTooltip(
                ['Name', f'{data_type}_percent'],
                aliases=['Basin Name:', f'{layer_name}:'])
        ).add_to(m)
    else:
        json_path = f'{STATIC_URL}/gis/HUC{huc_level}.geojson'
        folium.GeoJson(
            json_path,
            name=layer_name,
            embed=False,
            overlay=True,
            control=True,
            smooth_factor=2.0,
            style_function=style_function,
            show=show,
            tooltip=folium.features.GeoJsonTooltip(
                ['Name', f'{data_type}_percent'],
                aliases=['Basin Name:', f'{layer_name}:'])
        ).add_to(m)

def style_chropleth(feature, data_type='swe', huc_level='2', huc_filter=''):
    huc_filter = str(huc_filter)
    huc_level = str(huc_level)
    colormap = get_colormap()
    stat_value = feature['properties'].get(f'{data_type}_percent', 'N/A')
    huc_id = str(feature['properties'].get(f'HUC{huc_level}', 'N/A'))
    if stat_value == 'N/A':
        fill_opacity = 0
    else:
        stat_value = float(stat_value)
        fill_opacity = (abs(stat_value - 100)) / 100 + 0.1
        if fill_opacity > 0.75:
            fill_opacity = 0.75
    return {
        'fillOpacity': 
            0 if stat_value == 'N/A' or 
            not huc_id[:len(huc_filter)] == huc_filter else 
            fill_opacity,
        'weight': 0,
        'fillColor': 
            '#00000000' if stat_value == 'N/A' or 
            not huc_id[:len(huc_filter)] == huc_filter else 
            colormap(stat_value)
    }

def filter_geo_json(geo_json_path, filter_attr='HUC2', filter_str='14'):
   
    f_geo_json = {'type': 'FeatureCollection'}
    with open(geo_json_path, 'r') as gj:
        geo_json = json.load(gj)
    features = [i for i in geo_json['features'] if 
                i['properties'][filter_attr][:2] == filter_str]
    f_geo_json['features'] = features
    
    return f_geo_json

def filter_topo_json(topo_json, huc_level=2, filter_str='14'):
    
    geometries = topo_json['objects'][f'HUC{huc_level}']['geometries']
    geometries[:] = [i for i in geometries if 
                i['properties'][f'HUC{huc_level}'][:len(filter_str)] == filter_str]
    topo_json['geometries'] = geometries
    return topo_json

def get_colormap(low=50, high=150):
    # colormap = branca.colormap.linear.RdYlBu_09.scale(low, high)
    colormap = branca.colormap.LinearColormap(
        # colors=['red','yellow','green','blue', 'purple'],
        colors=[
            (255,51,51,150), 
            (255,255,51,150), 
            (51,255,51,150), 
            (51,153,255,150), 
            (153,51,255,150)
        ], 
        index=[50, 75, 100, 125, 150], 
        vmin=50,
        vmax=150
    )
    colormap.caption = '% of Average Precipitation or % Median Snow Water Equivalent'
    return colormap
   
if __name__ == '__main__':
    print('Just a utility module')
