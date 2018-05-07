# Altitude

Elevation API, running on Google App Engine. An instance is running at [altitude.andrewnisbet.nz](https://altitude.andrewnisbet.nz/) with full documentation. I wrote a bit about the process of developing the API on my [blog](https://www.andrewnisbet.nz/blog/elevation-api).

## Getting the data

The data is the ETOPO1 dataset from NOAA. It's too big for git, but you can [download it from NOAA](https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO1/data/ice_surface/grid_registered/binary/etopo1_ice_g_i2.zip). I'm using the ice surface, grid registered, 2-byte integer dataset.

The data is also too big for Google App Engine, so it needs to be split into 30MB parts:

```bash
split -b 30000000 -d  data/etopo1_ice_g_i2.bin  data/etopo1_ice_g_i2
``` 

then renamed like etopo1_ice_g_i2.bin.XX.

## Running locally

The `gcloud ` command doesn't include the App Engine development server, but it's included in the source. If you have the Google Cloud SDK installed in `/opt/google-cloud-sdk`, the API can be started with:

```bash
python /opt/google-cloud-sdk/platform/google_appengine/dev_appserver.py ./app.yaml
```
