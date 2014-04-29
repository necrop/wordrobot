/* global $, d3 */
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

function f2000() {
	return this.ftable.frequency(2000, false);
}
Lemma.prototype.f2000 = f2000;
