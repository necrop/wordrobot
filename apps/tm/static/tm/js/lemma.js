/* global $, d3, document_year */
'use strict';

var expansions = {F: 'French', L: 'Latin', G: 'Germanic', R: 'Romance',
	WG: 'West Germanic', OE: 'Old English'};

function expandLanguage(lang) {
	var exp = expansions[lang];
	if (!exp) { exp = lang; }
	return exp;
}

function Lemma(row) {
	this.id = row[0];
	this.url = row[1];
	this.lemma = row[2];
	this.sort = row[3] || row[2];
	this.year = row[4];
	this.language = expandLanguage(row[5]);
	this.family = expandLanguage(row[6]);
	this.count = row[7];
	this.definitionid = row[8];
	this.thesaurusid = row[9];
	this.ftable = new FrequencyTable(row.slice(10), this.year);
}

Lemma.prototype.f2000 = function() {
	return this.ftable.frequency(2000, false);
}

Lemma.prototype.getDefinition = function() {
	if (this.definition) {
		return this.definition;
	} else if (this.definitionid > 0) {
		definitionAjaxCall(this);
		return this.definition;
	} else {
		return null;
	}
}

function definitionAjaxCall(lemma) {
	$.ajax({
		type: 'GET',
		dataType: 'json',
		url: definition_url + lemma.definitionid,
		success: function(data) { lemma.definition = data[0]},
		fail: function(data) { lemma.definition = '[Definition not found]'},
		async: false
	});
}

Lemma.prototype.linesplitDefinition = function() {
	var definition = this.getDefinition();
	if (definition) {
		var lines = [];
		var text = '';
		var words = definition.split(/ /);
		for (var i = 0; i < words.length; i += 1) {
			text += words[i] + ' ';
			if (text.length > 50) {
				lines.push(text);
				text = '';
			}
		}
		if (text) {
			lines.push(text);
		}
		return lines.join('<br/>');
	} else {
		return null;
	}
}



//------------------------------------------------------
// Class methods
//------------------------------------------------------

Lemma.setDefinitionUrl = function(url) {
	Lemma.definition_url = url;
}
