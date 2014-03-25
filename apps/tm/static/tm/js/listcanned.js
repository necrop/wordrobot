/*global $, documentjson*/
'use strict';

var documentlist;

$(document).ready( function() {
	documentlist = uncompressData(documentjson);
	initializeDocumentTable();
});


//===============================================================
// Sortable table of lemmas
//===============================================================

var document_table_sortcolumn, document_table_direction;

function initializeDocumentTable() {
	composeDocumentTable();
	document_table_sortcolumn = 'author';
	document_table_direction = 'ascending';

	// Listeners
	$('#documentsTable > thead').find('th').click( function() {
		resortDocumentTable($(this));
	});
}

function composeDocumentTable() {
	var tbody = $('#documentsTable > tbody');
	tbody.html(''); // discard any existing rows
	for (var i = 0; i < documentlist.length; i += 1) {
		var doc = documentlist[i];
		var row = '<tr><td>' + doc.author + '</td>';
		row += '<td><a href="' + doc.url + '"><em>' + doc.title + '</em></a></td>';
		row += '<td>&lsquo;' + doc.teaser + '...&rsquo;</td><td>' + doc.date + '</td></tr>';
		row = $(row);
		row.appendTo(tbody);
	}

}

// Sorting functions
function resortDocumentTable(cell) {
	var column = cell.attr('sort');
	if (column) {
		$('#documentsTable > thead').find('th').removeClass('highlighted');
		cell.addClass('highlighted');

		var direction = 'ascending';
		if (column === document_table_sortcolumn && document_table_direction === 'ascending') {
			direction = 'descending';
		}
		if (column === 'author') {
			sortByAuthor(direction);
		} else if (column === 'title') {
			sortByTitle(direction);
		} else if (column === 'date') {
			sortByDate(direction);
		}
		composeDocumentTable();
		document_table_sortcolumn = column;
		document_table_direction = direction;
	}
}

function sortByAuthor(direction) {
	documentlist.sort(function(a, b) {
		if (a.authorsort < b.authorsort) {
			return -1;
		} else if (a.authorsort > b.authorsort) {
			return 1;
		} else {
			return 0;
		}
	});
	if (direction === 'descending') {
		documentlist.reverse();
	}
}

function sortByTitle(direction) {
	documentlist.sort(function(a, b) {
		if (a.titlesort < b.titlesort) {
			return -1;
		} else if (a.titlesort > b.titlesort) {
			return 1;
		} else {
			return 0;
		}
	});
	if (direction === 'descending') {
		documentlist.reverse();
	}
}


function sortByDate(direction) {
	documentlist.sort(function(a, b) {
		return a.date - b.date;
	});
	if (direction === 'descending') {
		documentlist.reverse();
	}
}


function uncompressData(compressed) {
	var expanded = [];
	for (var i = 0; i < compressed.length; i += 1) {
		var row = compressed[i];
		var item = {url: row[0],
					author: row[1],
					authorsort: row[2],
					title: row[3],
					titlesort: row[4],
					date: row[5],
					teaser: row[6] };
		expanded.push(item);
	}
	return expanded;
}
