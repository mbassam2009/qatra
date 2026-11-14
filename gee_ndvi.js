// Landsat 8 + 9 NDVI history for both pivot fields.
// Paste into https://code.earthengine.google.com , press Run,
// then Tasks > Run to export the CSV to Google Drive. Save it as data/ndvi.csv.

// Ring inside each circle: skip the bare pivot point (60 m) and stay 45 m inside the edge.
function ring(lon, lat, radius) {
  var c = ee.Geometry.Point([lon, lat]);
  return c.buffer(radius - 45).difference(c.buffer(60), 1);
}

var fields = ee.FeatureCollection([
  ee.Feature(ring(43.718483, 26.293592, 326), {field: 'pivot1'}),
  ee.Feature(ring(43.726511, 26.299203, 250), {field: 'pivot2'})
]);

function prep(img) {
  var qa = img.select('QA_PIXEL');
  var clear = qa.bitwiseAnd(1 << 3).eq(0)          // cloud
    .and(qa.bitwiseAnd(1 << 4).eq(0));             // cloud shadow
  var sr = img.select(['SR_B4', 'SR_B5']).multiply(0.0000275).add(-0.2);
  var ndvi = sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi');
  return ndvi.updateMask(clear).copyProperties(img, ['system:time_start']);
}

var col = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
  .filterBounds(fields)
  .filterDate('2015-01-01', '2026-01-01')
  .map(prep);

var series = col.map(function (img) {
  var date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd');
  return img.reduceRegions({collection: fields, reducer: ee.Reducer.mean(), scale: 30})
    .map(function (f) { return f.set('date', date).set('ndvi', f.get('mean')); });
}).flatten().filter(ee.Filter.notNull(['ndvi']));

Map.centerObject(fields, 15);
Map.addLayer(fields, {color: 'red'}, 'fields');
print(ui.Chart.feature.groups(series, 'date', 'ndvi', 'field').setOptions({title: 'Field NDVI'}));

Export.table.toDrive({
  collection: series,
  description: 'ndvi',
  fileFormat: 'CSV',
  selectors: ['field', 'date', 'ndvi']
});
