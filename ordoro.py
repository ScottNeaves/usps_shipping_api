import math, requests, flask
from flask import request
from flask_sqlalchemy import SQLAlchemy
import xml.etree.ElementTree as ET

from flask import Flask
app = Flask(__name__)
app.config['API_KEY'] = '885ORDOR3254'
#import pdb; pdb.set_trace()

@app.route('/get_shipping_rate', methods=['POST'])
def get_shipping_rate():
    params = request.get_json()

    #Region Pre-USPS Validation
    error = {'error':'', 'error_type': 'Ordoro (Pre-USPS API request)'}
    #Make sure all required keys are present and sensible:
    missing_keys = []
    invalid_keys = [] #keys with invalid values
    for key in ['origin_zip', 'destination_zip', 'weight', 'size']:
        if key not in params:
            missing_keys+=[key]
        else:
            if type(params[key])!=dict and int(params[key])<=0:
                invalid_keys+=[key]

    if 'size' in params:
        for dim in ['height', 'length', 'width']:
            if dim not in params['size']:
                missing_keys += ['size[\''+dim+'\']']
            else:
                if params['size'][dim]<=0:
                    invalid_keys+=[dim]

    if missing_keys:
        error['error'] += "JSON request payload missing the following keys: " + ', '.join(missing_keys) + '. '
    if invalid_keys: 
        error['error'] += "The following keys have invalid values: " + ', '.join(invalid_keys)
    if error['error']:
        return flask.jsonify(error)

    #Make sure that all values are allowable:
    if float(params['weight'])>70:
        error['error']="Package weight cannot exceed 70 pounds."
        return flask.jsonify(error)
    #Endregion Pre-USPS Validation

    #Region Caculations
    ounces, pounds = math.modf(float(params['weight']))
    ounces *= 16 #convert fraction of a pound to ounces
    dimsensions = [params['size']['width'], params['size']['length'], params['size']['height']]
    girth = sum(dimsensions)
    size = "LARGE" if any(dim > 12 for dim in dimsensions) else "REGULAR"
    #When the package is large, the value for "CONTAINER" is required and must be either 'RECTANGULAR' or 'NONRECTANGULR'. 
    if size=="LARGE":
        shape = "NONRECTANGULAR" if ('irregular_shape' in params and params['irregular_shape']==True) else "RECTANGULAR"
    else:
        shape=""
    #Endregion Calculations

    request_head = 'http://production.shippingapis.com/ShippingApi.dll?API=RateV4&XML=<RateV4Request USERID="{}">'.format(str(app.config['API_KEY']))
    request_body = """
     <Package ID="1ST"> 
        <Service>All</Service> 
        <ZipOrigination>{origin_zip}</ZipOrigination> 
        <ZipDestination>{destination_zip}</ZipDestination> 
        <Pounds>{pounds}</Pounds> 
        <Ounces>{ounces}</Ounces> 
        <Container>{shape}</Container>
        <Size>{size}</Size> 
        <Width>{width}</Width> 
        <Length>{length}</Length> 
        <Height>{height}</Height> 
        <Girth>{girth}</Girth> 
        <Machinable>true</Machinable>
    </Package> 
    </RateV4Request>"""\
    .format(origin_zip=params['origin_zip'], \
        destination_zip=params['destination_zip'], \
        pounds=pounds, \
        ounces=ounces, \
        shape=shape, \
        size=size, \
        width=params['size']['width'], \
        length=params['size']['length'], \
        height=params['size']['height'], \
        girth=girth)

    result_raw = requests.post(request_head + request_body).text
    print result_raw
    result_xml = ET.fromstring(result_raw)

    #Region Post-USPS Validation
    if result_xml.find('Package').find('Error'):
        error = {'error': result_xml.find('Package').find('Error').find('Description').text, 'error_type': 'USPS (Post-USPS API request)'}
        return flask.jsonify(error)
    #Endregion Post-USPS Validation

    result = {'result':{}}
    for node in result_xml.iter('Postage'):
        serviceType = node.find('MailService').text
        rate = node.find('Rate').text
        result['result'][serviceType]={'price':rate}
    print result

    return flask.jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)

