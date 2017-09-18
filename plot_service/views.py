import os
import itertools
from osgeo import gdal
from flask import render_template, safe_join, flash, request, Flask, redirect, url_for
from flask import send_file, send_from_directory
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
from plot_service import app, api
from terrautils.gdal import get_raster_extents
#from terrautils.sensors import check_site, check_sensor, get_file_paths


TERRAREF_BASE = '/projects/arpae/terraref/sites/ua-mac/Level_1/fullfield/'
PLOT_SERVICE_HOST = 'http://141.142.170.38:8000/'


class ReusableForm(Form):
    site = TextField('Site:', validators=[validators.required()])
    sensor = TextField('Sensor:', validators=[validators.required()])
    date = TextField('Date:', validators=[validators.required()])


def get_download_links(station, sensor, sitename, starting_date,
                           ending_date):

    links = []
    start_tuple = map(int, starting_date.split('-'))
    end_tuple = map(int, ending_date.split('-'))

    years =  range(start_tuple[0], end_tuple[0]+1)
    months =  range(start_tuple[1], end_tuple[1]+1)
    days = range(start_tuple[2], end_tuple[2]+1)

    for year, month, day in itertools.product(years, months, days):

        if day<10:
            day = '0' + str(day)
        if month<10:
            month = '0' + str(month)

        date = '{}-{}-{}'.format(str(year),str(month),day)
        paths = get_file_paths(station, sensor, date)
        host = os.environ.get('PLOT_SERVICE_HOST',PLOT_SERVICE_HOST)
        if os.path.exists(paths[0]):
            link = '{}api/v1/sites/{}/sensors/{}/{}?sitename={}'\
                   .format(host, station, sensor, date, sitename)
            links.append(link)
        '''
        fullpath = TERRAREF_BASE + date
        if os.path.exists(fullpath):
            os.chdir(fullpath)
            filename = '{}_fullfield.tif'.format(sensor)
            if filename in os.listdir('.'):
                host = os.environ.get('PLOT_SERVICE_HOST', 
                                      PLOT_SERVICE_HOST)
                link = ['{}download_links/{}'.format(host, filename),
                        fullpath, sitename]
                links.append(link)
        '''
    return links


@app.route('/fullfield', methods=['GET', 'POST'])
def fullfield():
    ''' The web interface for getting a fullfield image '''
    form = ReusableForm(request.form)
    if request.method == 'POST':
        site = request.form['site']
        sensor = request.form['sensor']
        date = request.form['date']

        if form.validate():
            return redirect(url_for('mapserver'))

    return render_template('fullfield.html', form=form, info={"status": ""})


@app.route('/mapserver', methods=['POST'])
def mapserver():
    ''' The web interface for showing the fullfield image on a map '''
    # get variables
    mapfile = ('/media/roger/sites/{}/Level_1/{}/{}' +
               '/stereoTop_fullfield_jpeg75.map').format(
                  request.form['site'], request.form['sensor'],
                  request.form['date'])

    # TODO Fix product filename
    product = check_sensor(request.form['site'],
                           request.form['sensor'],
                           request.form['date']) + '/ff.tif'

    extent, center = get_raster_extents(product)

    return render_template('mapserver.html', mapfile=mapfile,
                           extent=extent, center=center)


@app.route('/plot_service', methods=['GET', 'POST'])
def plot():
    ''' The web interface for getting a plot image '''
    form = ReusableForm(request.form)
    if request.method == 'POST':
        site = request.form['site']
        sensor = request.form['sensor']
        date = request.form['date']
        range_ = request.form['range']
        column = request.form['column']

        if form.validate():
            url = url_for('extract_plot', site=site, sensor=sensor,
                          date=date, range_=range_, column=column)
            return redirect(url)

    return render_template('plot_service.html', form=form, info={"status": ""})


@app.route('/download_links', methods=['GET','POST'])
def download():

    form = ReusableForm(request.form)
    if request.method == 'POST':
        station = request.form['station']
        sensor = request.form['sensor']
        sitename = request.form['sitename']
        starting_date = request.form['starting_date']
        ending_date = request.form['ending_date']

        #if form.validate():
        links = get_download_links(station, sensor, sitename,
                                   starting_date, ending_date)

        return render_template('download_links.html', links=links)

    return render_template('download_links.html')

@app.route('/api', methods=['GET','POST'])
def api():
    form = ReusableForm(request.form)
    if request.method == 'POST':
        site = request.form['site']
        sensor = request.form['sensor']
        date = request.form['date']
        return redirect(url_for('get_sensor_dates', site=site, sensor=sensor))
    return render_template('api.html', form=form)
