import requests, flask
from flask_sqlalchemy import SQLAlchemy
import xml.etree.ElementTree as ET

from flask import Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://scottneaves:8hub9jin@localhost/ordoro'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['API_KEY'] = '885ORDOR3254'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username

@app.route('/get_shipping_rate')
def get_shipping_rate():
    #TODO: calculate pounds and ounces from decimal pounds.
    request_params_start = 'http://production.shippingapis.com/ShippingApi.dll?API=RateV4&XML=<RateV4Request USERID="{}">'.format(str(app.config['API_KEY']))
    request_params = """
     <Package ID="1ST"> 
        <Service>All</Service> 
        <ZipOrigination>{origin_zip}</ZipOrigination> 
        <ZipDestination>{destination_zip}</ZipDestination> 
        <Pounds>{pounds}</Pounds> 
        <Ounces>{ounces}</Ounces> 
        <Container>NONRECTANGULAR</Container> 
        <Size>LARGE</Size> 
        <Width>15</Width> 
        <Length>30</Length> 
        <Height>15</Height> 
        <Girth>55</Girth> 
        <Machinable>true</Machinable>
    </Package> 
    </RateV4Request>""".format(origin_zip='60660', destination_zip='78749', pounds=1, ounces=2)

    print request_params_start + request_params
    result_raw = requests.post(request_params_start + request_params).text
    result_xml = ET.fromstring(result_raw)

    result = {'result':{}}
    for node in result_xml.iter('Postage'):
        print node
        serviceType = node.find('MailService').text
        rate = node.find('Rate').text
        print serviceType
        print rate
        result['result'][serviceType]={'price':rate}

    return flask.jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)