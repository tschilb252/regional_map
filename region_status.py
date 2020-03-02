# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 06:55:24 2020

@author: buriona
"""

from io import StringIO
from datetime import datetime as dt
from os import path, makedirs
from requests import get as r_get
import folium
import branca
import pandas as pd
from folium.plugins import FloatImage
from folium.features import DivIcon
# import geopandas as gpd
# from shapely.geometry import Point
# from shapely.ops import cascaded_union
from region_status_utils import get_fa_icon, get_icon_color, get_season
from region_status_utils import add_optional_tilesets, add_huc_layer, get_huc
from region_status_utils import get_favicon, get_bor_seal
from region_status_utils import get_bor_js, get_bor_css, NRCS_URL
from region_status_utils import get_default_js, get_default_css
from region_status_utils import get_nrcs_basin_stat, add_huc_chropleth
from region_status_utils import get_huc_nrcs_stats, get_colormap

bor_js = get_bor_js()
bor_css = get_bor_css()

default_js = get_default_js()
default_css = get_default_css()

folium.folium._default_js = default_js
folium.folium._default_css = default_css
# folium.folium._default_js = bor_js
# folium.folium._default_css = bor_css

regions = {
    'Arkansas-White-Red': {
        'coords': [37, -103], 'level': 2,
    }, 
    'California': {
        'coords': [37.5, -123.5], 'level': 2,
    },
    'Great Basin': {
        'coords': [40.75, -117], 'level': 2,
    },
    'Lower Colorado': {
        'coords': [35, -113], 'level': 2,
    },
    'Missouri': {
        'coords': [46.7, -106.2], 'level': 2,
    },
    'Pacific Northwest': {
        'coords': [45, -117.5], 'level': 2,
    },
    'Rio Grande':{
        'coords': [35.2, -107.7], 'level': 2,
    },
    'Upper Colorado': {
        'coords': [39.5, -110.7], 'level': 2,
    }
}

reservoirs = {
    'Canyon Ferry': {
        'coords': [46.487414, -111.544201], 'region': 'gp', 'anno': 1, 'cap': 1891.888, 'id': 'cfr'
    },
    'Bighorn': {
        'coords': [44.848426, -108.179062], 'region': 'gp', 'anno': 1, 'cap': 1020.573, 'id': 'bhr'
    },
    'Shadehill Reservoir': {
        'coords': [45.729203, -102.256583], 'region': 'gp', 'anno': 1, 'cap': 120.172, 'id': 'shr'
    },
    'Angostura Reservoir': {
        'coords': [43.308556, -103.422114], 'region': 'gp', 'anno': 1, 'cap': 123.048, 'id': 'agr'
    },
    'Palisades Reservoir': {
        'coords': [43.194831, -111.081225], 'region': 'pn', 'anno': 1, 'cap': 1200, 'id': 'pal'
    },
    'Arrowrock Reservoir': {
        'coords': [43.604093, -115.858169], 'region': 'pn', 'anno': 1, 'cap': 272.2, 'id': 'ark'
    },
    'Trinity Dam': {
        'coords': [40.969630, -122.676816], 'region': 'mp', 'anno': 1, 'cap': 2447.7, 'id': 'cle'
    },
    'Shasta Lake': {
        'coords': [40.735191, -122.414965], 'region': 'mp', 'anno': 1, 'cap': 4552, 'id': 'sha'
    },
    'Folsom Lake': {
        'coords': [38.729518, -121.119817], 'region': 'mp', 'anno': 1, 'cap': 977, 'id': 'fol'
    },
    'Millerton Lake': {
        'coords': [37.004422, -119.690673], 'region': 'mp', 'anno': 1, 'cap': 520.5, 'id': 'mil'
    },
    'Flaming Gorge': {
        'coords': [41.093419, -109.540657], 'region': 'uc', 'anno': 1, 'cap': 3749, 'id': 1718
    },
    'Lake Powell': {
        'coords': [37.068847, -111.243924], 'region': 'uc', 'anno':2, 'cap': 24322, 'id': 1719
    },
    'Lake Mead': {
        'coords': [36.145605, -114.41476], 'region': 'lc', 'anno': 2, 'cap': 28945, 'id': 1721
    },
    'Elephant Butte': {
        'coords': [33.251770, -107.166321], 'region': 'uc', 'anno': 2, 'cap': 1973.358, 'id': 2684
    },
}

forecasts = {
    'Grand Coulee': {
        'coords': [47.952807, -118.980527], 'region': 'pn', 'anno': 1, 'avg': 56763, 'id': 'GCDW1'
    },
    'Columbia River': {
        'coords': [45.604048, -121.173913], 'region': 'pn', 'anno': 1, 'avg': 87532, 'id': 'TDAO3'
    }
}
    
def get_dev_link():
    dev_link = '''
    <div style="position: fixed; top: 10px; right: 90px; z-index:9999;">
      <a class="btn btn-danger btn-sm" href="./regional_status_dev.html" role="button">
        Link to dev map.
      </a>
    </div>
    '''
    return dev_link

def get_legend():
    update_date = dt.now().strftime('%B %d, %Y')
    legend_html = f'''
  <div>
    <div style="position: fixed; bottom: 205px; left: 30px; z-index:9999; font-size:x-large;">
      <b>Reclamation West-Wide Summary</b><br>
    </div>
    <div style="position: fixed; bottom: 185px; left: 35px; z-index:9999; font-size:medium;">
        Precipitation and Storage Figures<br>
    </div>
    <div style="position: fixed; bottom: 30px; left: 40px; z-index:9999; font-size:small;">
      <sup>1</sup>Storage percent of capacity more sensitive to seasonal flows<br>
      <sup>2</sup>Storage percent of capacity less sensitive to seasonal flows<br>
      <i class="fa fa-umbrella"></i>&nbsp Water year-to-date precipitation (precip) provided as % of average<br>
      <i class="fa fa-snowflake-o"></i>&nbsp Snow water equivalent (snow) provided as % of median<br>
      <i class="fa fa-tint"></i>&nbsp Reservoir storage provided as percentage of capacity<br>
      <i class="fa fa-tachometer"></i>&nbsp Forecast volumes provided as percentage of 30-yr average<br>
      Precipitation, SWE, and reservoir data available from 
      <a href="https://www.wcc.nrcs.usda.gov/">NRCS</a>/
      <a href="https://www.usbr.gov/">BOR</a>/
      <a href="https://cdec.water.ca.gov/">CDEC</a><br>
      Updated as of {update_date}
    </div>
  </div>
    '''
    return legend_html

def get_uc_data(sdi, map_date=dt.now()):
    base_url = 'https://www.usbr.gov/pn-bin/hdb/hdb.pl?svr=uchdb2'
    sdi = f'&sdi={sdi}'
    tstp = '&tstp=DY'
    now = map_date
    dt_t1 = dt(now.year - 1, now.month, now.day).strftime('%Y-%m-%dT00:00')
    t1 = f'&t1={dt_t1}'
    dt_t2 = dt(now.year, now.month, now.day).strftime('%Y-%m-%dT00:00')
    t2 = f'&t2={dt_t2}'
    suffix= '&table=R&mrid=0&format=88'
    request_url = f'{base_url}{sdi}{tstp}{t1}{t2}{suffix}'
    response = StringIO(r_get(request_url).text)
    df = pd.read_csv(
        response, index_col='Date', parse_dates=True
    )
    df = df.astype(float)
    df.dropna(inplace=True)
    return {
        'data': df.iloc[-1,0], 
        'dt': df.index[-1].to_pydatetime(),
        'url': request_url.replace('format=88', 'format=html')
    }

def get_lc_data(sdi, map_date=dt.now()):
    base_url = 'https://www.usbr.gov/pn-bin/hdb/hdb.pl?svr=lchdb2'
    sdi = f'&sdi={sdi}'
    tstp = '&tstp=DY'
    now = map_date
    dt_t1 = dt(now.year - 1, now.month, now.day).strftime('%Y-%m-%dT00:00')
    t1 = f'&t1={dt_t1}'
    dt_t2 = dt(now.year, now.month, now.day).strftime('%Y-%m-%dT00:00')
    t2 = f'&t2={dt_t2}'
    suffix= '&table=R&mrid=0&format=88'
    request_url = f'{base_url}{sdi}{tstp}{t1}{t2}{suffix}'
    response = StringIO(r_get(request_url).text)
    df = pd.read_csv(
        response, index_col='Date', parse_dates=True
    )
    df = df.astype(float)
    df.dropna(inplace=True)
    return {
        'data': df.iloc[-1,0], 
        'dt': df.index[-1].to_pydatetime(),
        'url': request_url.replace('format=88', 'format=html')
    }

def get_pn_data(site_id, map_date=dt.now()):
    base_url = 'https://www.usbr.gov/pn-bin/daily.pl'
    station = f'?station={site_id}'
    frmt = '&format=csv'
    now = map_date
    dt_t1 = dt(now.year - 1, now.month, now.day)
    s_date = f'&year={dt_t1.year}&month={dt_t1.month}&day={dt_t1.day}'
    dt_t2 = dt(now.year, now.month, now.day)
    e_date = f'&year={dt_t2.year}&month={dt_t2.month}&day={dt_t2.day}'
    pcode = '&pcode=af'
    request_url = f'{base_url}{station}{frmt}{s_date}{e_date}{pcode}'
    response = StringIO(r_get(request_url).text)
    df = pd.read_csv(
        response, index_col='DateTime', parse_dates=True
    )
    df = df.astype(float)
    df.dropna(inplace=True)
    return {
        'data': df.iloc[-1,0], 
        'dt': df.index[-1].to_pydatetime(),
        'url': request_url.replace('csv', 'html')
    }

def get_gp_data(site_id, map_date=dt.now()):
    base_url = 'https://www.usbr.gov/gp-bin/webarccsv.pl'
    param = f'?parameter={site_id.upper()}%20AF'
    now = map_date
    dt_t1 = dt(now.year - 1, now.month, now.day)
    s_date = f'&syer={dt_t1.year}&smnth={dt_t1.month}&sdy={dt_t1.day}'
    dt_t2 = dt(now.year, now.month, now.day)
    e_date = f'&eyer={dt_t2.year}&emnth={dt_t2.month}&edy={dt_t2.day}'
    frmt = '&format=4'
    request_url = f'{base_url}{param}{s_date}{e_date}{frmt}'
    response = StringIO(r_get(request_url).text)
    df = pd.read_csv(
        response, index_col='#DATE', parse_dates=True, na_values='MISSING'
    )
    df = df.astype(float)
    df.dropna(inplace=True)
    df.index = pd.to_datetime(df.index)
    return {
        'data': df.iloc[-1,0], 
        'dt': df.index[-1].to_pydatetime(),
        'url': request_url.replace('format=4', 'format=3')
    }

def get_mp_data(site_id, map_date=dt.now()):
    base_url = 'http://cdec.water.ca.gov/dynamicapp/req/CSVDataServlet'
    station = f'?Stations={site_id.upper()}'
    sensor = '&SensorNums=15'
    duration = '&dur_code=D'
    now = map_date
    t1 = dt(now.year - 1, now.month, now.day).strftime('%Y-%m-%d')
    s_date = f'&Start={t1}'
    t2 = dt(now.year, now.month, now.day).strftime('%Y-%m-%d')
    e_date = f'&End={t2}'
    request_url = f'{base_url}{station}{sensor}{duration}{s_date}{e_date}'
    df_all = pd.read_csv(
        request_url, index_col='DATE TIME', parse_dates=True, na_values='---'
    )
    df = df_all[['VALUE']].copy()
    df = df.astype(float)
    df.dropna(inplace=True)
    df.index = pd.to_datetime(df.index)
    return {
        'data': df.iloc[-1,0], 
        'dt': df.index[-1].to_pydatetime(),
        'url': request_url
    }

def get_frcst_data(site_id, map_date=dt.now()):
    base_url = 'https://www.nwrfc.noaa.gov/water_supply/ws_text.cgi'
    station = f'?id={site_id.upper()}'
    now = map_date
    wy = now.year
    if now.month > 9:
        wy += 1
    wy_str = f'&wy={wy}'
    period = '&per=APR-AUG'
    frcst_type = '&type=ESP10'
    prob = '&prob=0'
    request_url = f'{base_url}{station}{wy_str}{period}{frcst_type}{prob}'
    request_txt = r_get(request_url).text
    request_txt = request_txt.replace('<br>', '\n')
    request_txt = request_txt.replace('</pre></body>', '')
    request_io = StringIO()
    request_io.write(request_txt)
    request_io.seek(0)
    df_all = pd.read_csv(
        request_io, skiprows=4, index_col='Issuance Date', 
        parse_dates=True, na_values=''
    )
    df = df_all[['50% FCST']].copy()
    df = df.astype(float)
    df.dropna(inplace=True)
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    return {
        'data': df.iloc[-1,0], 
        'dt': df.index[-1].to_pydatetime(),
        'url': request_url
    }

def get_embed(href):
    embed = (
        f'<div class="container embed-responsive embed-responsive-4by3" style="overflow: hidden; height: 650px; width: 720px;">'
        f'  <iframe class="embed-responsive-item" src="{href}" scrolling="no" frameborder="0" allowfullscreen></iframe>'
        f'</div>'
    )   
    return embed

def add_region_markers(rs_map, regions=regions, nrcs_url=NRCS_URL, map_date=None):
    for region, region_meta in regions.items():
        print(f'    Adding {region} to the map...')
        basin_name = region
        huc_level = region_meta['level']
        if str(huc_level) == '2':
            basin_name = f'{region} Region'
        swe_percent = get_nrcs_basin_stat(
            basin_name, huc_level=huc_level, data_type='wteq'
        )
        prec_percent = get_nrcs_basin_stat(
            basin_name, huc_level=huc_level, data_type='prec'
        )
        swe_url = f'{nrcs_url}/WTEQ/assocHUC{huc_level}/{basin_name}.html'
        prec_url = f'{nrcs_url}/PREC/assocHUC{huc_level}/{basin_name}.html'
        seasonal_url = swe_url
        other_season_url = prec_url
        other_chart_type = 'Precip.'
        if get_season() == 'summer':
            seasonal_url = prec_url
            other_season_url = swe_url
            other_chart_type = 'Snow'
            
        popup_html = (
                f'<div class="container">'
                f'<div class="row justify-content-center">'
                f'<div class="col">'
                f'<a href="{other_season_url}" target="_blank">'
                f'<button class="btn btn-primary btn-sm btn-block">'
                f'Go to {region} {other_chart_type} Chart...</button></a></div>'
                f'<div class="row justify-content-center">{get_embed(seasonal_url)}</div>'
                f'</div></div>'
            )
        popup = folium.map.Popup(html=popup_html)
            
        marker_label = f'''
        <button type="button" class="btn btn-primary btn-md">
          <span style="white-space: nowrap;">{region}</span><br>
          <span style="white-space: nowrap;">
            {prec_percent}% <i class="fa fa-umbrella"></i>
            {swe_percent}% <i class="fa fa-snowflake-o"></i>
          </span>
        </button>
        '''
        
        div_icon = DivIcon(
            icon_anchor=(0,0),
            html=marker_label,
        )
        folium.Marker(
            location=region_meta['coords'],
            popup=popup,
            tooltip='Click for chart.',
            icon=div_icon
        ).add_to(rs_map)

def add_res_markers(rs_map, reservoirs=reservoirs, map_date=None):
    for res_name, res_meta in reservoirs.items():
        print(f'    Adding {res_name} to map...')
        try:
            if res_meta['region'] == 'uc':
                current_data = get_uc_data(res_meta['id'], map_date=map_date)
            elif res_meta['region'] == 'lc':
                current_data = get_lc_data(res_meta['id'], map_date=map_date)
            elif res_meta['region'] == 'pn':
                current_data = get_pn_data(res_meta['id'], map_date=map_date)
            elif res_meta['region'] == 'gp':
                current_data = get_gp_data(res_meta['id'], map_date=map_date)
            elif res_meta['region'] == 'mp':
                current_data = get_mp_data(res_meta['id'], map_date=map_date)
            else:
                current_data = None
        except Exception as err:
            print(f'      Error gathering data for {res_name} - {err}')
            current_data = None
                
        if current_data:
            percent_cap = 100 * round(current_data['data'] / (1000 * res_meta['cap']), 2)
            percent_cap = f'{percent_cap:0.0f}'
            tooltip = f"As of: {current_data['dt'].strftime('%x')}"
            anno = res_meta['anno']
            url = current_data['url']
        else:
            percent_cap = 'N/A'
            tooltip = 'Error retrieving data!'
            anno = ''
            url = ''
            
        marker_label = f'''
        <a href="{url}" target="_blank">
          <button type="button" class="btn btn-sm btn-info">
            <span style="white-space: nowrap;">{res_name}</span><br>
            <span style="white-space: nowrap;">
              {percent_cap}%<sup>{anno}</sup> <i class="fa fa-tint"></i>
            </span>
          </button>
        </a>
        '''
        icon_anchor = (0,0)
        if res_name.lower() in ['elephant butte', 'trinity dam']:
            icon_anchor = (80,35)
            
        div_icon = DivIcon(
            # icon_size=(120,40),
            icon_anchor=icon_anchor,
            html=marker_label,
        )
        
        folium.Marker(
            location=res_meta['coords'],
            # popup=popup,
            tooltip=tooltip,
            icon=div_icon
        ).add_to(rs_map)

def add_frcst_markers(rs_map, forecasts=forecasts, map_date=None):
    for frcst_name, frcst_meta in forecasts.items():
        print(f'    Adding {frcst_name} to map...')
        
        try:
            if frcst_meta['region'] == 'pn':
                current_data = get_frcst_data(frcst_meta['id'], map_date=map_date)
            else:
                current_data = None
        except Exception as err:
            print(f'      Error gathering data for {frcst_name} - {err}')
            current_data = None
                
        if current_data:
            percent_cap = 100 * round(current_data['data'] / (frcst_meta['avg']), 2)
            percent_cap = f'{percent_cap:0.0f}'
            tooltip = f"As of: {current_data['dt'].strftime('%x')}"
            anno = frcst_meta['anno']    
            url = current_data['url']
        else:
            percent_cap = 'N/A'
            tooltip = 'Error retrieving data!'         
            anno = ''
            url = ''
            
        marker_label = f'''
        <a href="{url}" target="_blank">
          <button type="button" class="btn btn-sm btn-info">
            <span style="white-space: nowrap;">{frcst_name}</span><br>
            <span style="white-space: nowrap;">
              Apr-Aug Forecast
            </span>
            <span style="white-space: nowrap;">
              {percent_cap}%<sup>{anno}</sup> <i class="fa fa-tachometer"></i>
            </span>
          </button>
        </a>
        '''

        div_icon = DivIcon(
            # icon_size=(120,40),
            icon_anchor=(0,0),
            html=marker_label,
        )
        
        folium.Marker(
            location=frcst_meta['coords'],
            # popup=popup,
            tooltip=tooltip,
            icon=div_icon
        ).add_to(rs_map)
        
if __name__ == '__main__':

    import argparse
    cli_desc = 'Creates West-Wide Summary map for USBR.'
    parser = argparse.ArgumentParser(description=cli_desc)
    parser.add_argument("-V", "--version", help="show program version", action="store_true")
    parser.add_argument("-d", "--date", help="run for specific date (YYYY-MM-DD), currently no support for region prec/swe data, only res/frcst data")
    parser.add_argument("-o", "--output", help="set output folder")
    parser.add_argument("-n", "--name", help="use alternate name *.html")
    parser.add_argument("-m", "--makedir", help="create output folder if it doesn't exist", action='store_true')
    parser.add_argument("-g", "--gis", help="update local gis files with current NRCS data", action='store_true')
    
    args = parser.parse_args()
    
    if args.version:
        print('region_status.py v1.0')
    map_date = dt.now()
    if args.date:
        try:
            map_date = dt.strptime(args.date, "%Y-%m-%d")
        except ValueError as err:
            print(f'Could not parse {args.date}, using current date instead. - {err}')    
    
    if args.gis:
        huc2 = get_huc_nrcs_stats(2)
        huc6 = get_huc_nrcs_stats(6)

    this_dir = path.dirname(path.realpath(__file__))
    map_dir = path.join(this_dir, 'maps')
    makedirs(map_dir, exist_ok=True)
    if args.output:
        if path.exists(args.output):
            map_dir = args.output
        else:
            if args.makedir:
                try:
                    map_dir = args.output
                    makedirs(map_dir, exist_ok=True)
                except Exception as err:
                    print(f'Cannot create {args.output}, using {map_dir} instead. - {err}')
            else:
                print(f'{args.output} does not exist, using {map_dir} instead.')  
    if args.name:
        map_path = path.join(map_dir, f'{args.name}.html')
    else:
        map_path = path.join(map_dir, 'regional_status.html')
        
    print(f'Creating map here: {map_dir}')
    gis_dir = path.join(this_dir, 'gis')
    
    rs_map = folium.Map(tiles=None)
    show_prec = False
    show_swe = True
    if get_season() =='summer':
        show_prec = True
        show_swe = False
    add_huc_chropleth(
        rs_map, data_type='swe', show=show_swe, huc_level='6', gis_path='gis'
    )
    add_huc_chropleth(
        rs_map, data_type='prec', show=show_prec, huc_level='6', gis_path='gis'
    )
    add_huc_layer(rs_map, level=2, show=True)
    add_optional_tilesets(rs_map)
    folium.LayerControl('topleft').add_to(rs_map)
    FloatImage(
        get_bor_seal(orient='horz'),
        bottom=78,
        left=1
    ).add_to(rs_map)
    get_colormap().add_to(rs_map)
    # MousePosition(prefix="Location: ").add_to(rs_map)
    
    print('  Adding Regional Forecast markers...')
    add_frcst_markers(rs_map, map_date=map_date)
    print('  Adding Regional Reservoir markers...')
    add_res_markers(rs_map, map_date=map_date)
    print('  Adding Regional PREC/SWE markers...')
    add_region_markers(rs_map, map_date=map_date)
    
    all_coords = [i['coords'] for i in reservoirs.values()]
    all_coords = all_coords + [i['coords'] for i in forecasts.values()]
    all_coords = all_coords + [i['coords'] for i in regions.values()]
    rs_map.fit_bounds(all_coords)

    legend = folium.Element(get_legend())
    rs_map.get_root().html.add_child(legend)
    
    # dev_link = folium.Element(get_dev_link())
    # rs_map.get_root().html.add_child(dev_link)
    
    rs_map.save(map_path)
    flavicon = (
        f'<link rel="shortcut icon" '
        f'href="{get_favicon()}"></head>'
    )
    with open(map_path, 'r') as html_file:
        chart_file_str = html_file.read()

    with open(map_path, 'w') as html_file:
        chart_file_str = chart_file_str.replace(r'</head>', flavicon)
        replace_str = (
            '''left:100px; top:10px; max-width:15%; max-height:15%;
                background-color:rgba(255,255,255,0.5);
                border-radius: 10px; padding: 10px;'''
        )
        chart_file_str = chart_file_str.replace(r'left:1%;', replace_str)
        html_file.write(chart_file_str)
    print(f'\nCreated map here: {map_path}')