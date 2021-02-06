var x = document.querySelectorAll("a");
var myarray = []
for (var i=0; i<x.length; i++){
	//if the strong contains boxscores and .html

	var nametext = x[i].textContent;

 	if (x[i].href.includes("boxscores/") && x[i].href.includes(".html") ) {
		var cleantext = nametext.replace(/\s+/g, ' ').trim();
		var cleanlink = x[i].href;
		myarray.push([cleanlink]);
 	}
};
function make_table() {
    var table = '<table><thead><th>Name</th><th>Links</th></thead><tbody>';
   for (var i=0; i<myarray.length; i++) {
            table += '<tr><td>'+ myarray[i][0] + '</td></tr>';
    };
 
    var w = window.open("");
w.document.write(table); 
}
make_table()
