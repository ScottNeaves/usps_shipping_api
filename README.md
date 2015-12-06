# usps_shipping_api
Gets shipping rates and shipping labels from USPS, and also does another cool shipping-related thing (specifics TBD)

###Usage: 
To get shipping rates, POST the following json object as raw data to /get_shipping_rates with Content-type='application/json'. All fields are required except for "irregular_shape" which is a boolean and should be set to true whenever you are shipping something in a particularly unusual container.

```
{
    "destination_zip": "78749",
    "origin_zip": "60660",
    "weight": "71",
    "size": {
        "length":1,
        "width": 2,
        "height": 3
    },
    "irregular_shape": false
}
```