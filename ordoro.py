import math, requests, flask, datetime, email, smtplib
from tempfile import NamedTemporaryFile
from shutil import copyfileobj
from flask import request, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import xml.etree.ElementTree as ET
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import email.mime.text, email.mime.application
from email.MIMEMultipart import MIMEMultipart
#ordoro.shipping.api@gmail.com, password 885ORDOR3254

from flask import Flask
app = Flask(__name__)
app.config['API_KEY'] = '885ORDOR3254'
#import pdb; pdb.set_trace()

@app.route('/get_shipping_rates', methods=['POST'])
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

    #Region data transformation
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
    #Endregion data transformation

    query = """http://production.shippingapis.com/ShippingApi.dll?API=RateV4&XML= \
    <RateV4Request USERID="{user_id}">
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
    .format(\
        user_id=app.config['API_KEY'], \
        origin_zip=params['origin_zip'], \
        destination_zip=params['destination_zip'], \
        pounds=pounds, \
        ounces=ounces, \
        shape=shape, \
        size=size, \
        width=params['size']['width'], \
        length=params['size']['length'], \
        height=params['size']['height'], \
        girth=girth)

    result_raw = requests.post(query).text
    print result_raw
    result_xml = ET.fromstring(result_raw)

    #Region Post-USPS Validation
    if result_xml.find('Package').find('Error'):
        error = {'error': result_xml.find('Package').find('Error').find('Description').text, 'error_type': 'USPS (Post-USPS API request)'}
        return flask.jsonify(error)
    #Endregion Post-USPS Validation

    result = {'result':{}}
    for node in result_xml.iter('Postage'):
        #Replacing URL-encoded TM symbols with empty string to make response more legible.
        serviceType = node.find('MailService').text.replace("&lt;sup&gt;&#8482;&lt;/sup&gt;", "").replace("&lt;sup&gt;&#174;&lt;/sup&gt;", "")
        rate = node.find('Rate').text
        #There doesn't appear to be any way to specify multiple service types in the API call to USPS. You can either choose one service type or "All".
        #   Therefore, in order to avoid making a round trip for each service type we wish to receive pricing for, we just request "All" and 
        #   remove the undesireable service types upon receipt of the USPS results.
        if not any(s in serviceType for s in ['Hold For Pickup', 'Library Mail', 'Media Mail']):
            result['result'][serviceType]={'price':rate}
    print result

    return flask.jsonify(result)

@app.route('/get_shipping_label', methods=['POST'])
def get_shipping_label():
    params = request.get_json()

    #Region Pre-USPS Validation
    error = {'error':'', 'error_type': 'Ordoro (Pre-USPS API request)'}
    #Make sure all required keys are present and allowable:
    missing_keys = []
    invalid_keys = [] #keys with invalid values
    for key in ['to', 'from', 'weight', 'serviceType', 'imageFormat']:
        if key not in params:
            missing_keys+=[key]
        else:
            if key=="weight":
                if int(params[key])<=0:
                    invalid_keys+=[key]
            if key=='serviceType':
                if params[key] not in ["PRIORITY", "FIRST CLASS", "STANDARD POST"]:
                    invalid_keys+=[key]
            if key=='imageFormat':
                if params[key] not in ["TIF", "PDF"]:
                    invalid_keys+=[key]

    for addressee in ['to', 'from']:
       if addressee in params:
            for line in ['name', 'address1', 'address2', 'state', 'city', 'zip5']:
                if line not in params[addressee]:
                    missing_keys += ['\''+addressee+'[\''+line+'\']']

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

    #Region data transformation
    fromZip4 = "<FromZip4>"+params['from']['zip4']+"</FromZip4>" if 'zip4' in params['from'] else "<FromZip4/>"
    toZip4 = "<ToZip4>"+params['to']['zip4']+"</ToZip4>" if 'zip4' in params['to'] else "<ToZip4/>"
    toFirm = params['to']['firm'] if 'firm' in params['to'] else ""
    fromFirm = params['from']['firm'] if 'firm' in params['from'] else ""
    weight = int(params['weight'])*16 #convert pounds to ounces
    #Endregion data transformation

    query = """https://secure.shippingapis.com/ShippingAPI.dll?API=DelivConfirmCertifyV4&XML=<?xml version="1.0" encoding="UTF-8" ?>
    <DelivConfirmCertifyV4.0Request USERID="{user_id}">
      <FromName>{from_name}</FromName>
      <FromFirm>{from_firm}</FromFirm>
      <FromAddress1>{from_address1}</FromAddress1>
      <FromAddress2>4{from_address2}</FromAddress2>
      <FromCity>{from_city}</FromCity>
      <FromState>{from_state}</FromState>
      <FromZip5>{from_zip5}</FromZip5>
      {from_zip4}
      <ToName>{to_name}</ToName>
      <ToFirm>{to_firm}</ToFirm>
      <ToAddress1>{to_address1}</ToAddress1>
      <ToAddress2>{to_address2}</ToAddress2>
      <ToCity>{to_city}</ToCity>
      <ToState>{to_state}</ToState>
      <ToZip5>{to_zip5}</ToZip5>
      {to_zip4}
      <WeightInOunces>{weight}</WeightInOunces>
      <ServiceType>{service_type}</ServiceType>
      <ImageType>{image_format}</ImageType>
    </DelivConfirmCertifyV4.0Request>
    """.format(\
        user_id=app.config['API_KEY'], \
        from_name=params['from']['name'], \
        from_firm=fromFirm,
        from_address1=params['from']['address1'], \
        from_address2=params['from']['address2'], \
        from_city=params['from']['city'], \
        from_state=params['from']['state'], \
        from_zip5=params['from']['zip5'], \
        from_zip4=fromZip4, \
        to_name=params['to']['name'], \
        to_firm=toFirm, \
        to_address1=params['to']['address1'], \
        to_address2=params['to']['address2'], \
        to_city=params['to']['city'], \
        to_state=params['to']['state'], \
        to_zip5=params['to']['zip5'], \
        to_zip4=toZip4, \
        weight=weight,
        service_type=params['serviceType'],
        image_format=params['imageFormat']
        )
    print query
    result_raw = requests.post(query).text
    print result_raw
    result_xml = ET.fromstring(result_raw)
    
    #Region Post-USPS Validation
    if result_xml.tag=='Error':
        error = {'error': result_xml.find('Description').text, 'error_type': 'USPS (Post-USPS API request)'}
        return flask.jsonify(error)
    #Endregion Post-USPS Validation

    #In a production environment, "yourLabel" would probably be replaced by the customer's name,
    #   and instead of storing the files in the local directory, we might store them on a remote fileserver
    filename="yourLabel"+str(datetime.datetime.now())+"."+params['imageFormat']
    image_file = open(filename, "w+b")
    image_file.write(result_xml.find('DeliveryConfirmationLabel').text.decode('base64'))
    image_file.seek(0)

    deliveryType = 'Download' #download by default.
    if 'emailAddress' in params:
        deliveryType = 'Email'
        deliveryEmailAddress=params['emailAddress']

    if deliveryType=='Download':
        return send_from_directory('', filename, as_attachment=True)

    if deliveryType=='Email':
        try:
            msg=MIMEMultipart()
            msg['Subject'] = "Shipping Label"
            msg['From'] = "Ordoro"
            msg['To'] = deliveryEmailAddress
            att = email.mime.application.MIMEApplication(image_file.read(),_subtype=params['imageFormat'])
            att.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(att)
            session = smtplib.SMTP('smtp.gmail.com', 587)
            session.ehlo()
            session.starttls()
            session.ehlo()
            session.login('ordoro.shipping.api', '885ORDOR3254')
            session.sendmail('ordoro.shipping.api@gmail.com', deliveryEmailAddress, msg.as_string())
            result = {'result': 'Shipping label successfully emailed to ' + deliveryEmailAddress}
            return flask.jsonify(result)
        except:
            error = {'error': 'Email not able to be sent. Try again or remove the emailAddress field from the request object to do a direct download instead.'}
            return flask.jsonify(error)



if __name__ == '__main__':
    app.run(debug=True)

