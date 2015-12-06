# usps_shipping_api
Gets shipping rates and shipping labels from USPS, and also does another cool shipping-related thing (specifics TBD)

##Usage: 
###Shipping Rates
To get shipping rates, POST the following json object as raw data to /get_shipping_rates with Content-type='application/json'. All fields are required except for "irregular_shape", which is a boolean and should be set to true whenever you are shipping something in a particularly unusual container. Of course, the value associated with each key in the JSON object below is meant as an example, and should be replaced with whatever value is relevant to the package you wish to ship.

```
{
    "destination_zip": "78749",
    "origin_zip": "60660",
    "weight": "12",
    "size": {
        "length":1,
        "width": 2,
        "height": 3
    },
    "irregular_shape": false
}
```