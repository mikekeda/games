var sass = require('node-sass');
sass.render({
  file: 'sass/style.scss',
  outFile: 'static/css/style.css',
}, function(err, result) {

});
