# usps_shipping_api
Gets shipping rates and shipping labels from USPS. Fun new feature added to the shipping labels API: you can optionally get your labels emailed to you! More on that below.

##Usage: 
###Shipping Rates
The shipping rates API is intended to provide e-commerce shippers with prices for each USPS shipping option available for the package they wish to ship, so that they may choose which USPS delivery option best suits their price and urgency requirements.

To get shipping rates, POST the following json object as raw data to /get_shipping_rates with Content-type='application/json'. All fields are required except for "irregular_shape", which is a boolean and should be set to true whenever you are shipping something in a particularly unusual container. Of course, the value associated with each key in the JSON object below is meant as an example, and should be replaced with whatever value is relevant to the package you wish to ship.

*Example request object*

```
{
    "destination_zip": "78749",		//zip code    
    "origin_zip": "60660",			//zip code
    "weight": "12",					//unit: pounds
    "size": {
        "length": 1,				//unit: inches
        "width": 10,				//unit: inches
        "height": 10				//unit: inches
    },
    "irregular_shape": false		//Optional. Either true or false.
}
```
Note: It is assumed that the shipper is a small-to-medium e-commerce business who is only interested in learning the shipping rates for shipping arbitrary items straight to customers' doorsteps. Thus, pricing options for "Library Mail Parcel", "Media Mail Parcel", and "Hold For Pickup" are excluded. Also, the API does not check for unlikely weight/size combinations. For example, you may ask for the shipping rates for a 1''x1''x1'' object which weighs 50 pounds, and receive a price in the response which includes the pricing for a Flat-Rate gift card envelope. It is rather unlikely that you will be able to fit a 50-pound object into a gift-card envelope :).

*Example response object*

```
{
  "result": {
    "Priority Mail 2-Day": {
      "price": "28.85"
    },
    "Priority Mail 2-Day Large Flat Rate Box": {
      "price": "17.90"
    },
    "Priority Mail 2-Day Medium Flat Rate Box": {
      "price": "12.65"
    },
    "Priority Mail Express 1-Day": {
      "price": "82.40"
    },
    "Priority Mail Express 1-Day Flat Rate Boxes": {
      "price": "44.95"
    },
    "Standard Post": {
      "price": "23.57"
    }
  }
}
```
###Label Creation

This shipping label API acts as a wrapper around the USPS shipping label API, allowing you to provide your data in a friendly JSON format instead of XML and also automatically downloading the resulting label as an image instead of base64 code. If you supply your email address in the optional "emailAddress" fields, your shipping lable will be emailed to you instead of downloaded!

All fields are required except for "zip4", "firm", and "emailAddress".

*Example request object*

```
{
    "to":{
        "name": "Ordoro",
        "firm": "Ordoro",
        "address1": "Suite 405",
        "address2": "101 W 6th St",
        "city": "Austin",
        "state": "TX",
        "zip5": "78701"
    },
    "from":{
        "name": "Scott Neaves",
        "address1": "",
        "address2": "5916 Lomita Verde Circle",
        "city": "Austin",
        "state": "TX",
        "zip5": "78749",
        "zip4": "4203"
    },
    "weight": 70,								//unit: pounds
    "serviceType": "PRIORITY",					//"PRIORITY", "FIRST CLASS", or "STANDARD POST"
    "imageFormat": "PDF",						//must be either "TIF" or "PDF"
    "emailAddress": "your_email_address@gmail.com"
}
```

The response will be the resulting image file, in either TIF or PDF format, whichever you specified in the request.