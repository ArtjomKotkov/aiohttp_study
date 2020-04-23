$(document).ready(function() {

	$.getJSON('/content/art', function(json, textStatus) {
			console.log(json)
	});

});