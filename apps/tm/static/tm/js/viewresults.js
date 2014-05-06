/*global $, d3, lemmajson, tokenjson, document_year */
'use strict';

// Global variables
var ngram_url = 'https://books.google.com/ngrams/graph?year_start=1750&year_end=2000&corpus=15&smoothing=20&content=';
var oed_entry_url = 'http://www.oed.com/view/Entry/';
var oed_thes_url = 'http://www.oed.com/view/th/class/';
var base_wordclasses = {'NN': 1, 'VB': 1, 'JJ': 1, 'RB': 1};

var language_colours = [
	['Germanic', '#B2CCFF', '#66CCFF'],
	['Romance', '#FF7F7F', '#FF0000'],
	['Latin', '#C5A3CF', '#9A5EAB'],
	['Greek', '#99CC99', '#00FF00'],
	['Celtic', '#FF9900', '#FF9900'],
	['Slavonic', '#FF4FA7', '#FF2F97'],
	['other', '#FBEA74', '#FFDE00'] ];
var language_colours_hash = hashLanguageColours(language_colours);

var lemma_details,
	growth_details,
	thesaurus_details,
	theslinked_tokens,
	document_million_ratio,
	button_animator,
	colour_key,
	thesaurus_animation,
	thesaurus_slider;

// Expand token and lemma rows from compressed arrays to more legible objects 
var tokendata = uncompressTokenData(tokenjson);
var lemmadata = uncompressLemmaData(lemmajson);

// We make a shallow copy of lemmadata so that this can be re-sorted in the lemma
//  table. (We don't want to do this with the original version of lemmadata,
//  since this needs to be kept in its original order - other functions reference
//  lemmas by index position.)
var lemmadata_sortable = lemmadata.slice();

// Information that will be used when the thesaurus is animated
var thesaurusdata = initializeThesaurusData();
var thesaurusdata_loaded = false;


//===============================================================
// Functions to run once the page has loaded
//===============================================================

$(document).ready( function() {

	lemma_details = $('#lemmaDetails');
	thesaurus_details = $('#thesaurusDetails');
	growth_details = $('#growthDetails');
	colour_key = $('#continuousTextKey');
	thesaurus_slider = $('#thesaurusSlider');
	document_million_ratio = 1000000 / tokendata.length;

	FrequencyTable.setDeltaBracket();

	compileLinearText();
	compileStatistics();
	drawLanguageRatios();
	drawTimelineChart();
	drawGrowthChart();
	compileFrequencyChangeChart();
	writeThesaurusText();
	initializeLemmaTable();
	showUrlModal();

	// Set listeners for pop-up close buttons
	lemma_details.find('.lemmaDetailsCloser').click( function() {
		lemma_details.css('display', 'none');
	});
	thesaurus_details.find('.thesaurusDetailsCloser').click( function() {
		thesaurus_details.css('display', 'none');
	});
	// Set listeners for popovers on buttons and links
	$('button[data-toggle="popover"]').popover({trigger: 'hover', placement: 'top'});
	$('a[data-toggle="popover"]').popover({trigger: 'hover', placement: 'top'});
});


function showUrlModal() {
	if (location.search.substring(1) === 'notify') {
		var href = location.href.split('?')[0]
		$('#urlContainer').text(href);
		$('#urlModal').modal({show: true});
	}
}



//===============================================================
// Data preparation
//===============================================================

function uncompressLemmaData(compressed) {
	var expanded = [];
	for (var i = 0; i < compressed.length; i += 1) {
		var row = compressed[i];
		var lemma = new Lemma(row);
		expanded.push(lemma);
	}

	// Make sure that each lemma knows its own index position in the array.
	//  (This will be necessary when the lemmas get re-sorted as lemmadata_sortable.)
	for (var i = 0; i < expanded.length; i += 1) {
		expanded[i].idx = i;
	}

	return expanded;
}

function uncompressTokenData(compressed) {
	var expanded = [];
	for (var i = 0; i < compressed.length; i += 1) {
		var row = compressed[i];
		var data = {token: row[0], status: row[1], spacebefore: row[2] };
		if (data.status === 'oed') {
			data.lemma_index = row[3];
			data.wordclass = row[4];
		}
		expanded.push(data);
	}
	return expanded;
}

function initializeThesaurusData() {
	var data = {};
	for (var i = 0; i < lemmadata.length; i += 1) {
		var lemma = lemmadata[i];
		if (lemma.thesaurusid > 0) {
			data[lemma.thesaurusid] = null;
		}
	}
	return data;
}



//===============================================================
// Button handlers
//===============================================================

// Toggle the state of the button
function toggleButtonState(button, icon_class) {
	button.toggleClass('btn-info');
	button.toggleClass('btn-primary');
	var icon = button.find('i');
	if (icon.hasClass(icon_class)) {
		icon.removeClass(icon_class);
		icon.addClass('icon-remove');
	} else {
		icon.addClass(icon_class);
		icon.removeClass('icon-remove');
	}
}

// Test if the button is currently on
function buttonIsOn(button) {
	return button.hasClass('btn-primary');
}



//===============================================================
// Colour-coding by language family
//===============================================================

function hashLanguageColours(colourlist) {
	var hash = {};
	for (var i = 0; i < colourlist.length; i += 1) {
		var row = colourlist[i];
		hash[row[0]] = [row[1], row[2]];
	}
	return hash;
}

function languageToNormalizedLanguage(language) {
	// Given a language family (or null), return the normalized
	// language category that will be used for colour-coding
	var normalized;
	if (! language) {
		normalized = 'other';
	} else if (! language_colours_hash[language]) {
		normalized = 'other';
	} else {
		normalized = language;
	}
	return normalized;
}

function languageToColour(language, mode) {
	language = languageToNormalizedLanguage(language);
	var colourset = language_colours_hash[language];
	if (mode === 'bright') {
		return colourset[1];
	} else {
		return colourset[0];
	}
}

function colourKey(mode) {
	// Poll the set of language families appearing in this document; only
	//  these will appear in the key
	var languages_in_document = {};
	for (var i = 0; i < lemmadata.length; i += 1) {
		var family = languageToNormalizedLanguage(lemmadata[i].family);
		languages_in_document[family] = true;
	}

	// Create the HTML for the key
	var html = '<div class="colourKey"><span>Key:</span>';
	for (var i = 0; i < language_colours.length; i += 1) {
		var language = language_colours[i][0];
		if (languages_in_document[language]) {
			var colour = languageToColour(language, mode);
			html += '<span class="colourKeySegment" style="background-color: ' + colour + '">' + language + '</span>';
		}
	}
	html += '</div>';
	return html;
}



//===============================================================
// Pop-up displaying lemma information
//===============================================================

function showLemmaDetails(lemma, event) {
	var occurrences = lemma.count;
	var frequency = lemma.f2000();
	var year = lemma.year;

	var occurrence_text;
	if (occurrences === 1) {
		occurrence_text = 'once';
	} else if (occurrences === 2) {
		occurrence_text = 'twice';
	} else {
		occurrence_text = occurrences + ' times';
	}

	var year_text;
	if (year < 1150) {
		year_text = 'before 1150';
	} else {
		year_text = year;
	}

	var equivalent_text;
	if (occurrences > 7) {
		var eq_frequency = equivalentFrequency(occurrences).toPrecision(2) * 1;
		equivalent_text = '(~ ' + eq_frequency + ' per million tokens)';
	} else {
		equivalent_text = '';
	}

	// Fill in various blank fields in the pop-up
	lemma_details.find('h2 a').html(lemma.lemma);
	lemma_details.find('#popupLemma').html(lemma.lemma);
	lemma_details.find('#popupInverseFrequency').text(inverseFrequency(frequency, true));
	lemma_details.find('#popupOldFrequency').text(frequencyText(lemma.ftable.frequency(document_year, true)));
	lemma_details.find('#popupModFrequency').text(frequencyText(frequency));
	lemma_details.find('#popupFirstDate').text(year_text);
	lemma_details.find('#popupLanguage').text(lemma.language);
	lemma_details.find('#popupCountInDocument').text(occurrence_text);
	lemma_details.find('#popupEquivalentFrequency').text(equivalent_text);

	lemma_details.find('a.a-oed').attr('href', oed_entry_url + lemma.url);
	lemma_details.find('a.a-ngram').attr('href', ngram_url + lemma.lemma);

	// The definition (if any) is not included in the JSON packet, so we
	//  have to fetch this dynamically from the database via AJAX
	insertDefinition(lemma);

	// Reposition the pop-up
	lemma_details.css('left', (event.pageX) + 'px');
	lemma_details.css('top', (event.pageY) + 'px');
	lemma_details.css('display', 'block');
}

function frequencyText(f) {
	if (f < 0.0001) {
		return 'less than .0001';
	} else {
		return 'about ' + f;
	}
}

function insertDefinition(lemma) {
	var definition = lemma.linesplitDefinition();
	if (definition) {
		lemma_details.find('defn').html("'" + definition + "'");
	}
	else {
		lemma_details.find('defn').html('');
	}
}




//===============================================================
// Continuous text
//===============================================================

function compileLinearText() {
	// Write out the text
	writeContinuousText();

	// Hide the colour key
	colour_key.css('visibility', 'hidden');

	// Make the buttons flash
	var buttons = d3.select('#continuousTextButtons > button[data-toggle]');
	button_animator = setInterval(function () {
		buttons.transition()
			.duration(500)
			.style('opacity', 0.3)
			.each('end', function() {
				buttons.transition()
					.duration(500)
					.style('opacity', 1)
			});
	}, 1000);


	// Button-click event listeners
	$('#continuousTextButtons > button[data-toggle]').click( function() {
		clearInterval(button_animator);
	});

	$('#colourCodeButton').click( function() {
		if (buttonIsOn($(this))) {
			removeColourCoding();
		} else {
			colourCodeByOrigin();
		}
		toggleButtonState($(this), 'icon-tint');
	});

	$('#focusRareButton').click( function() {
		if (buttonIsOn($(this))) {
			normalizeSize();
		} else {
			highlightLowFrequency();
		}
		toggleButtonState($(this), 'icon-search');
		// Override the settings for the 'recent' button
		var button = $('#focusRecentButton');
		if (buttonIsOn(button)) {
			toggleButtonState(button, 'icon-search');
		}
	});

	$('#focusRecentButton').click( function() {
		if (buttonIsOn($(this))) {
			normalizeSize();
		} else {
			highlightRecent();
		}
		toggleButtonState($(this), 'icon-search');
		// Override the settings for the 'rare' button
		var button = $('#focusRareButton');
		if (buttonIsOn(button)) {
			toggleButtonState(button, 'icon-search');
		}
	});
}


function writeContinuousText() {
	var text_html = compileContinuousText('regular');
	$('#continuousText').html(text_html);
	$('#continuousTextKey').append(colourKey('pale'));

	// Token-click event listener
	$('.token-oed').click( function(event) {
		displayLemmaDetails($(this), event);
	});
}


// Return the lemma object corresponding to a given token
function elementToLemma(element) {
	return lemmadata[element.attr('idx')];
}

function displayLemmaDetails (token, event) {
	var lemma = elementToLemma(token);
	showLemmaDetails(lemma, event);
}

function colourCodeByOrigin() {
	var tokens = $('#continuousText').find('.token-oed');
	tokens.each( function(i) {
		var lemma = elementToLemma($(this));
		var colour = languageToColour(lemma.family, 'pale');
		$(this).css('background-color', colour);
	});
	colour_key.css('visibility', 'visible');
}

function removeColourCoding() {
	var tokens_all = $('#continuousText').find('.token-oed');
	tokens_all.css('background-color', 'inherit');
	colour_key.css('visibility', 'hidden');
}

function highlightLowFrequency() {
	normalizeSize();
	var tokens = $('#continuousText').find('.token-oed');
	tokens.each( function() {
		var lemma = elementToLemma($(this));
		var band = frequency_band(lemma.f2000());
		$(this).css('font-size', (band * 0.5) + 'em').css('opacity', 0.9);
	});
}

function highlightRecent() {
	normalizeSize();
	var tokens = $('#continuousText').find('.token-oed');
	tokens.each( function(i) {
		var lemma = elementToLemma($(this));
		var band = year_band(lemma.year);
		$(this).css('font-size', (band * 0.5) + 'em').css('opacity', 0.9);
	});
}

function normalizeSize() {
	var tokens_all = $('#continuousText').find('.token-oed');
	tokens_all.css('font-size', '1em').css('opacity', 1);
}

function year_band(year) {
	var age = 2015 - year;
	if (age > 900) {
		age = 900;
	}
	return (1000 - age) / 120;
}

function frequency_band(frequency) {
	var band;
	if (frequency > 0) {
		var log = log10(frequency);
		if (log > 3) {
			log = 3;
		}
		band = Math.abs(log - 4);
		if (band > 7) {
			band = 7;
		}
	} else {
		band = 8;
	}
	return band;
}



//===============================================================
// Continuous text with thesaurus variation
//===============================================================

function loadCompleteThesaurusData() {
	// Set cursors to 'wait'
	$('body').css({cursor: 'wait'});
	$('.btn-info').css({cursor: 'wait'});
	// Make a comma-separated list of all the thesaurus IDs
	var idstring = Object.keys(thesaurusdata).join();
	$.getJSON(thesaurus_url + idstring, {}, function(json) {
		for(var i = 0; i < json.length; i += 1) {
			var record = json[i];
			thesaurusdata[record.id] = record;
		}
		thesaurusdata_loaded = true;
		// Restore cursors
		$('body').css({cursor: 'default'});
		$('.btn-info').css({cursor: 'pointer'});
		// Riff the text now, so we're sure that this happens at least once
		// when the load process has completed.
		varyTheslinkedTokens();
	});
}

function writeThesaurusText() {
	var text_html = compileContinuousText('thesaurus');
	$('#thesaurusText').html(text_html);
	theslinked_tokens = $('#thesaurusText').find('.token-theslinked');

	// Token-click event listener
	theslinked_tokens.click( function(event) {
		displayThesaurusRecord($(this), event);
	});

	// Initialize the date-range slider
	var slider_text = $('#thesaurusSliderText');
	thesaurus_slider.slider({
		range: true,
		min: 1150,
		max: 2015,
		values: [1200, 2015],
		slide: function(event, ui) {
			slider_text.text(ui.values[0] + ' - ' + ui.values[1]);
		}
	});
	// Initialize the date-range text alongside the slider
	slider_text.text(thesaurus_slider.slider('values', 0) + ' - ' + thesaurus_slider.slider('values', 1));


	// Button-click event listeners
	$('#thesaurusPlayButton').click( function() {
		var icon = $(this).find('i');
		if (icon.hasClass('icon-pause')) {
			stopThesaurusAnimation();
		} else {
			if (! thesaurusdata_loaded) {
				loadCompleteThesaurusData();
			}
			varyTheslinkedTokens();
			animateThesaurus();
		}
	});

	$('#thesaurusRiffButton').click( function() {
		stopThesaurusAnimation();
		if (! thesaurusdata_loaded) {
			loadCompleteThesaurusData();
		} else {
			varyTheslinkedTokens();
		}
	});

	$('#thesaurusResetButton').click( function() {
		stopThesaurusAnimation();
		resetTheslinkedTokens();
	});
}

function displayThesaurusRecord(token, event) {
	var source = token.find('.src').text();
	var classid = token.attr('classid') * 1;
	if (classid > 0) {
		// Get the record (via AJAX if not already acquired)
		if (thesaurusdata[classid] == null) {
			$.getJSON(thesaurus_url + classid, {}, function(json) {
				if (json.length === 1) {
					thesaurusdata[classid] = json[0];
					displayThesaurusPopup(source, json[0], event);
				}
			});
		} else {
			displayThesaurusPopup(source, thesaurusdata[classid], event);
		}
	}
}

function displayThesaurusPopup(source, record, event) {
	// Populate the popup with the record
	var title_node = thesaurus_details.find('#thesaurusDetailsTitle');
	var breadcrumb_node = thesaurus_details.find('#thesaurusDetailsBreadcrumb');
	var instances_node = thesaurus_details.find('#thesaurusDetailsInstanceContainer');
	title_node.text(source);
	breadcrumb_node.text(record.breadcrumb);
	breadcrumb_node.attr('href', oed_thes_url + record.id);

	instances_node.html('');
	for (var i = 0; i < record.instances.length; i+= 1) {
		var instance = record.instances[i];
		var url = oed_entry_url + instance.refentry + '#eid' + instance.refid;

		var row = $('<div><a href="' + url + '" target="ext">' + instance.lemma + '</a> &nbsp;&nbsp; ' + dateRange(instance) + '</div>');
		row.appendTo(instances_node);
	}

	// Reposition and display the pop-up
	thesaurus_details.css('left', (event.pageX) + 'px');
	thesaurus_details.css('top', (event.pageY) + 'px');
	thesaurus_details.css('display', 'block');
}

function dateRange(instance) {
	var date_range = '(' + instance.start_year;
	if (instance.end_year > 2000) {
		date_range += '&mdash;';
	} else if (instance.end_year > instance.start_year) {
		date_range += '&ndash;' + instance.end_year;
	}
	date_range += ')';
	return date_range;
}

function animateThesaurus() {
	thesaurus_animation = setInterval(function() {
		varyTheslinkedTokens();
	}, 3000);
	$('#thesaurusPlayButton').find('i')
		.addClass('icon-pause')
		.removeClass('icon-play');
}

function stopThesaurusAnimation() {
	clearInterval(thesaurus_animation);
	$('#thesaurusPlayButton').find('i')
		.addClass('icon-play')
		.removeClass('icon-pause');
}

function varyTheslinkedTokens() {
	// Get the date range from the present state of the slider
	var yearfrom = thesaurus_slider.slider('values', 0);
	var yearto = thesaurus_slider.slider('values', 1);

	theslinked_tokens.each(function(i) {
		var classid = $(this).attr('classid') * 1;
		var wordclass = $(this).attr('wordclass');
		if (classid > 0) {
			var lemma;
			lemma = randomLemma(thesaurusdata[classid], yearfrom, yearto, wordclass);
			if (lemma == null) {
				lemma = '<i>[' + $(this).find('.src').text() + ']</i>';
			}
			else {
				lemma = alignCapitalization($(this), lemma);
			}
			$(this).find('.disp').html(lemma);
		}
	})
}

function resetTheslinkedTokens() {
	theslinked_tokens.each(function() {
		var src = $(this).find('.src').text();
		$(this).find('.disp').html(src);
	})
}

function alignCapitalization(token, lemma) {
	// Ensure that the replacement is capitalized in the same way as
	// the original
	var source = token.find('.src').text();
	if (source.charAt(0).toUpperCase() === source.charAt(0)) {
		lemma = lemma.charAt(0).toUpperCase() + lemma.slice(1);
	}
	return lemma;
}

function randomLemma(record, yearfrom, yearto, wordclass) {
	var instance = randomInstance(record, yearfrom, yearto);
	var lemma;
	if (instance == null) {
		lemma = null;
	} else {
		lemma = instance.lemma;
		// Replace the base lemma with its inflected form, if the source
		//  token is not a base wordclass
		if (base_wordclasses[wordclass] == null && instance.infstring) {
			if (instance.inflections == null) {
				instance.inflections = parseInflections(instance.infstring);
			}
			if (instance.inflections[wordclass] != null) {
				lemma = instance.inflections[wordclass];
			}
		}
	}
	return lemma;
}

function parseInflections(inflections_string) {
	var inflections = {};
	var parts = inflections_string.split('|');
	for (var i = 0; i < parts.length; i += 1) {
		var z = parts[i].split('=');
		inflections[z[0]] = z[1];
	}
	return inflections;
}

function randomInstance(record, yearfrom, yearto) {
	var instances = instancesAtYear(record, yearfrom, yearto);
	if (instances.length === 1) {
		return instances[0];
	} else if (instances.length > 1) {
		var index = Math.floor(Math.random() * instances.length);
		return instances[index];
	} else {
		return null;
	}
}

function instancesAtYear(record, yearfrom, yearto) {
	// Return the subset of a record's instances that were around
	// at a given year (with some leeway)
	var instances = [];
	if (record) {
		for (var i = 0; i < record.instances.length; i += 1) {
			var instance = record.instances[i];
			if (instance.start_year <= yearto && instance.end_year >= yearfrom) {
				instances.push(instance);
			}
		}
	}
	return instances;
}



//===============================================================
// Statistics table
//===============================================================

function compileStatistics() {
	var characters = 0,
		words = 0,
		word_characters = 0;
	for (var i = 0; i < tokendata.length; i += 1) {
		var t = tokendata[i];
		characters += t.token.length;
		if (t.status != 'punc') {
			words += 1;
			word_characters += t.token.length;
		}
	}
	var average_word_length = (word_characters / words).toPrecision(2);

	var stats_table = $('#statistics');
	stats_table.find('#ntokens').text(tokendata.length);
	stats_table.find('#nlemmas').text(lemmadata.length);
	stats_table.find('#nwords').text(words);
	stats_table.find('#ncharacters').text(characters);
	stats_table.find('#avechars').text(average_word_length);
}




//===============================================================
// Chart showing language-family ratios
//===============================================================

function drawLanguageRatios() {
	var i,
		languages = {},
		total = 0;
	for (i = 0; i < lemmadata.length; i += 1) {
		var l = lemmadata[i];
		var family = languageToNormalizedLanguage(l.family);
		if (! languages[family]) { languages[family] = 0; }
		languages[family] += l.count;
		total += l.count;
	}

	var percentages = [];
	for (i = 0; i < language_colours.length; i += 1) {
		var language = language_colours[i][0];
		if (language in languages) {
			var pcnt = ((100 / total) * languages[language]);
			percentages.push([language, pcnt]);
		}
	}

	var canvas_width = $('#languageRatioContainer').innerWidth();
	var bar_height = canvas_width * 0.03;
	var canvas_height = bar_height * percentages.length;

	// x-axis scale
	var x_scale = d3.scale.linear()
		.domain([0, d3.max(percentages, function(d) { return d[1]; })])
		.range([0, canvas_width * 0.8]);

	// Create the SVG element (as a child of the #languageRatioContainer div)
	var canvas = d3.select('#languageRatioContainer').append('svg')
		.attr('width', canvas_width)
		.attr('height', canvas_height)
		.attr('overflow', 'hidden');

	// Add a bordered rectangle the same size as the SVG element, for the background
	canvas.append('rect')
		.attr('x', 0)
		.attr('y', 0)
		.attr('width', canvas_width)
		.attr('height', canvas_height)
		.attr('class', 'chartBackground');

	// Draw blocks
	var blocks = canvas.selectAll('.languageRatioBlock')
		.data(percentages, function (d) { return d[0]; });

	blocks.enter().append('rect')
		.attr('class', 'languageRatioBlock')
		.attr('x', 0)
		.attr('y', function (d, i) { return bar_height * i; })
		.attr('width', function (d) { return x_scale(d[1]); })
		.attr('height', bar_height)
		.style('fill', function (d) { return languageToColour(d[0], 'bright'); });

	// Draw text labels overlaying each bar
	var labels = canvas.selectAll('.languageRatioLabel')
		.data(percentages, function (d) { return d[0]; });
	labels.enter().append('text')
		.attr('class', 'languageRatioLabel')
		.attr('x', 5)
		.attr('y', function (d, i) { return (bar_height * (1 + i)) - (bar_height * 0.1) ; }) 
		.text(function(d) { return d[0] + ' (' + (d[1].toPrecision(2) * 1) + '%)'; })
		.style('fill', 'black')
		.style('font-size', (bar_height * 0.6) + 'px');

}



//===============================================================
// Scatter chart showing frequency vs. first recorded use
//===============================================================

function drawTimelineChart() {
	var buttons,
		scatter_tooltip,
		scatter_animator,
		scatter_animator_year;

	// Draw the colour-coding key
	$('div#scatterKey').append(colourKey('bright'));

	buttons = $('button.scatterFrequencyControl');
	buttons.each( function() {
		$(this).data('year', $(this).text() * 1);
	});

	var canvas_width = $('#scatterChart').innerWidth() * 0.95;
	var canvas_height = canvas_width * 0.6;
	var y_padding = canvas_height * 0.1;

	// x-axis scale
	var end_year = document_year + 50;
	var x_scale = d3.scale.linear()
		.domain([970, end_year])
		.range([0, canvas_width]);

	// y-axis scale
	var max_frequency = d3.max(lemmadata, function(d) { return d.f2000(); });
	var y_scale = d3.scale.pow().exponent(0.1)
		.domain([0, max_frequency * 2])
		.range([canvas_height, 0]);

	// coefficient used to set the radius of balloons
	var dotscaler = canvas_width * 0.005;

	// Create the SVG element (as a child of the #scatterChart div)
	var canvas = d3.select('#scatterChart').append('svg')
		.attr('width', canvas_width)
		.attr('height', canvas_height)
		.attr('overflow', 'hidden');

	// Add a bordered rectangle the same size as the SVG element, for the background
	canvas.append('rect')
		.attr('x', 0)
		.attr('y', 0)
		.attr('width', canvas_width)
		.attr('height', canvas_height)
		.attr('class', 'chartBackground');

	// Add a darker rectangle to indicate the pre-1150 period
	canvas.append('rect')
		.attr('x', 0)
		.attr('y', 0)
		.attr('width', x_scale(1150))
		.attr('height', canvas_height)
		.attr('id', 'scatterPre1150');

	// Draw line indicating the document year
	canvas.append('rect')
		.attr('x', x_scale(document_year))
		.attr('y', 0)
		.attr('width', 1)
		.attr('height', canvas_height - y_padding)
		.attr('fill', '#FF0000');
	canvas.append('text')
		.attr('x', x_scale(document_year))
		.attr('y', canvas_height * 0.1)
		.text(document_year)
		.attr('fill', '#FF0000')
		.style('font-size', (canvas_height * 0.03) + 'px');


	// Draw axes
	var format_as_year = d3.format('d');
	var x_axis = d3.svg.axis()
					.scale(x_scale)
					.orient('bottom');
	x_axis.tickFormat(format_as_year);
	canvas.append('g')
		.attr('class', 'scatterAxis')
		.attr('transform', 'translate(0,' + (canvas_height - y_padding) + ')')
		.call(x_axis);

	/*
	var y_axis = d3.svg.axis()
					.scale(y_scale)
					.orient('left')
					.ticks(5, 'e');
	canvas.append('g')
		.attr('class', 'scatterAxis')
		.attr('transform', 'translate(' + x_padding + ',0)')
		.call(y_axis);
	*/


	// Draw balloons
	var balloons = canvas.selectAll('.scatterBalloon')
		.data(lemmadata, function (d) { return d.idx; });

	balloons.enter().append('circle')
		.attr('class', function(d) {
			return 'scatterBalloon scatterBalloon'
				+ languageToNormalizedLanguage(d.family);
		})
		.attr('cx', function (d) {
			if (d.year > 1150) {
				return x_scale(d.year);
			} else {
				var random_year = Math.random() * (1150 - 1000) + 1000;
				return x_scale(random_year);
			}
		})
		.style('fill', function (d) { return languageToColour(d.family, 'bright'); })
		.attr('r', function (d) { return Math.sqrt(d.count) * dotscaler; });

	// Set y-axis position of each bubble to frequencies for the document year
	showFrequenciesForYear(document_year, 0);
	// Highlight the appropriate button
	highlightButton(document_year);


	// Set event listeners for mouseovers on the colour key
	$('div#scatterKey').find('span.colourKeySegment')
		.mouseover( function() {
			var language = $(this).text();
			$('div#scatterChart circle.scatterBalloon' + language)
				.css('stroke-width', '3');
			balloons.each( function(d) {
				if (languageToNormalizedLanguage(d.family) === language) {
					var x = ($(this).attr('cx') * 1) + ($(this).attr('r') * 1);
					var y = $(this).attr('cy') * 1;
					canvas.append('text')
						.attr('x', x + 5)
						.attr('y', y)
						.style('fill', 'darkgreen')
						.style('font-size', '20px')
						.text(d.lemma);
				}
			});
		})
		.mouseout( function() {
			$('div#scatterChart circle.scatterBalloon')
				.css('stroke-width', '');
			$('div#scatterChart text').remove();
		});


	// Set event listeners for clicks/mouseovers on balloons
	balloons
		.on('click', function (d) {
			hideScatterTooltip();
			showLemmaDetails(d, d3.event);
		})
		.on('mouseover', function(d) {
			showScatterTooltip(d, d3.event);
		})
		.on('mouseout', function() {
			hideScatterTooltip();
		});


	// Player function used to animate the scatter chart display
	var scatter_player = function() {
		showFrequenciesForYear(scatter_animator_year, 0);
		highlightButton(scatter_animator_year);
		if (scatter_animator_year >= 2000) {
			clearInterval(scatter_animator);
		}
		scatter_animator_year += 5;
	};
	$('#playDiachronicFrequency').click( function() {
		scatter_animator_year = document_year;
		if (1750 < document_year) {
			scatter_animator_year = 1750;
		}
		highlightButton(scatter_animator_year);
		scatter_animator = setInterval(scatter_player, 100);
	});


	// Set event listeners for changing frequency display to different years
	buttons.click( function() {
		clearInterval(scatter_animator);
		highlightButton($(this).data('year'));
		showFrequenciesForYear($(this).data('year'), 300);
	});

	function showFrequenciesForYear(year, duration) {
		balloons.transition()
			.duration(duration)
			.attr('cy', function (d) { return y_scale(clampedFrequency(d.ftable.frequency(year))); })
	}

	function highlightButton(target_year) {
		buttons.removeClass('btn-primary');
		var target = null;
		buttons.each( function() {
			if ($(this).data('year') <= target_year) {
				target = $(this);
			}
		});
		if (target) {
			target.addClass('btn-primary');
		}
	}


	// Display the small pop-up showing the lemma name
	scatter_tooltip = $('#scatterTooltip');
	function showScatterTooltip(d, event) {
		// Populate the pop-up
		scatter_tooltip.find('h2').html(d.lemma);
		// Reposition the pop-up
		scatter_tooltip.css('left', (event.pageX) + 'px');
		scatter_tooltip.css('top', (event.pageY) + 'px');
		scatter_tooltip.css('display', 'block');
	}

	// Hide the small pop-up showing the lemma name
	function hideScatterTooltip() {
		scatter_tooltip.css('display', 'none');
	}
}






//===============================================================
// Chart showing lexicon growth over time
//===============================================================

function drawGrowthChart() {
	// calculate the two data series
	var cumulative = computeCumulative();

	var canvas_width = $('#growthChartContainer').innerWidth() * 0.95;
	var canvas_height = canvas_width * 0.5;
	var y_padding = canvas_height * 0.1;
	var x_padding = canvas_width * 0.05;

	// x-axis scale
	var end_year = document_year + 50;
	var x_scale = d3.scale.linear()
		.domain([1150, end_year])
		.range([x_padding, canvas_width]);

	// y-axis scale
	var y_scale = d3.scale.linear()
		.domain([0, 109])
		.range([canvas_height - y_padding, 0]);

	// Create the SVG element (as a child of the #growthChartContainer div)
	var canvas = d3.select('#growthChartContainer').append('svg')
		.attr('width', canvas_width)
		.attr('height', canvas_height)
		.attr('overflow', 'hidden');

	// Add a bordered rectangle the same size as the SVG element, for the background
	canvas.append('rect')
		.attr('x', 0)
		.attr('y', 0)
		.attr('width', canvas_width)
		.attr('height', canvas_height)
		.attr('class', 'chartBackground');


	// Draw line indicating the document year
	canvas.append('rect')
		.attr('x', x_scale(document_year))
		.attr('y', y_scale(100))
		.attr('width', 1)
		.attr('height', y_scale(0))
		.attr('fill', '#FF0000');
	canvas.append('text')
		.attr('x', x_scale(document_year + 5))
		.attr('y', y_scale(90))
		.text(document_year)
		.attr('fill', '#FF0000');


	// Draw axes
	var format_as_year = d3.format('d');
	var x_axis = d3.svg.axis()
					.scale(x_scale)
					.orient('bottom');
	x_axis.tickFormat(format_as_year);
	canvas.append('g')
		.attr('class', 'scatterAxis')
		.attr('transform', 'translate(0,' + (canvas_height - y_padding) + ')')
		.call(x_axis);

	var y_axis = d3.svg.axis()
					.scale(y_scale)
					.orient('left');
	canvas.append('g')
		.attr('class', 'scatterAxis')
		.attr('transform', 'translate(' + x_padding + ', 0)')
		.call(y_axis);


	// Draw lines
	var line = d3.svg.line()
		.x(function(d) { return x_scale(d[0]); })
		.y(function(d) { return y_scale(d[1]); });
	canvas.append('path')
		.attr('d', line(cumulative.tokens))
		.attr('class', 'growthPath');
	canvas.append('path')
		.attr('d', line(cumulative.lemmas))
		.attr('class', 'growthPath');

	// Draw circles
	var circles1 = canvas.selectAll('.growthChartCircle')
		.data(cumulative.lemmas);
	circles1.enter().append('circle')
		.attr('class', 'growthCircle')
		.attr('cx', function (d) { return x_scale(d[0]); })
		.attr('cy', function (d) { return y_scale(d[1]); })
		.attr('r', 4)
		.style('fill', 'blue');

	var circles2 = canvas.selectAll('.growthChartCircle')
		.data(cumulative.tokens);
	circles2.enter().append('circle')
		.attr('class', 'growthCircle')
		.attr('cx', function (d) { return x_scale(d[0]); })
		.attr('cy', function (d) { return y_scale(d[1]); })
		.attr('r', 4)
		.style('fill', 'red');


	// Listeners for mouseover events on datapoints in the chart
	circles1
		.on('mouseover', function (d) {
			showGrowthDetails(d, 'lemmas', d3.event);
		})
		.on('mouseout', function () {
			hideGrowthDetails();
		});

	circles2
		.on('mouseover', function (d) {
			showGrowthDetails(d, 'tokens', d3.event);
		})
		.on('mouseout', function () {
			hideGrowthDetails();
		});

	// Fill in the values in the commentary text
	var percentile95 = null;
	for (var i = 0; i < cumulative.tokens.length; i += 1) {
		if (cumulative.tokens[i][1] >= 95) {
			percentile95 = cumulative.tokens[i][0];
			break;
		}
	}
	if (!percentile95) {
		percentile95 = '?';
	}

	$('#growthChart1150').text(cumulative.tokens[0][1].toPrecision(2));
	$('#growthChart95').text(percentile95);
}


function showGrowthDetails(d, mode, event) {
	// Populate the pop-up
	growth_details.find('h2').text(d[0]);
	growth_details.find('#growthDetailsValue').text(d[1].toPrecision(2));
	growth_details.find('#growthDetailsYear').text(d[0]);
	var description_text;
	if (mode === 'tokens') {
		description_text = 'the content of';
	} else {
		description_text = 'the lemmas used in';
	}
	growth_details.find('#growthDetailsDesc').text(description_text);
	// Reposition the pop-up
	growth_details.css('left', (event.pageX) + 'px');
	growth_details.css('top', (event.pageY) + 'px');
	growth_details.css('display', 'block');
}

function hideGrowthDetails() {
	growth_details.css('display', 'none');
}

function computeCumulative() {
	var counts = {lemmas: {}, tokens: {}};
	var totals = {lemmas: 0, tokens: 0};
	for (var i = 0; i < lemmadata.length; i += 1) {
		var lemma = lemmadata[i];
		var year = clampedDate(lemma.year);
		var decade = Math.floor(year/10) * 10;
		if (!counts.lemmas[decade]) {
			counts.lemmas[decade] = 0;
			counts.tokens[decade] = 0;
		}
		counts.lemmas[decade] += 1;
		totals.lemmas += 1;
		counts.tokens[decade] += lemma.count;
		totals.tokens += lemma.count;
	}

	var cumulative = {lemmas: [], tokens: []};
	var running_totals = {lemmas: 0, tokens: 0};
	for (var period = 1150; period < document_year; period += 10) {
		for (var mode in running_totals) {
			if (counts[mode][period]) {
				running_totals[mode] += counts[mode][period];
			}
			// convert to percentage
			var percentage = (100 / totals[mode]) * running_totals[mode];
			cumulative[mode].push([period, percentage]);
		}
	}

	return cumulative;
}



//===============================================================
// Lemmas increasing/decreasing in frequency
//===============================================================

function compileFrequencyChangeChart() {
	var frequency_change_tooltip,
		increases,
		decreases,
		lemmas;

	// Compile the set of lemmas that will be displayed (those with the
	// greatest increase or decrease in frequency)
	increases = [];
	decreases = [];
	for (var i = 0; i < lemmadata_sortable.length; i += 1) {
		var l = lemmadata_sortable[i];
		if (l.ftable.frequency(document_year) > 0.001) {
			if (l.ftable.delta() > 1.3) {
				increases.push(l);
			} else if (l.ftable.delta() < 0.8) {
				decreases.push(l);
			}
		}
	}
	// Get the 10 lemmas with greatest increase in frequency
	increases.sort(function(a, b) {
		return b.ftable.delta() - a.ftable.delta();
	});
	increases = increases.slice(0, 10);

	// Get the 10 lemmas with the greatest decrease in frequency
	decreases.sort(function(a, b) {
		return a.ftable.delta() - b.ftable.delta();
	});
	decreases = decreases.slice(0, 10);
	// ... make sure they're sorted consistently with increases
	decreases.sort(function(a, b) {
		return b.ftable.delta() - a.ftable.delta();
	});
	// Concatenate to give a single array of data points
	lemmas = increases.concat(decreases);


	var canvas_width = $('#frequencyChangeContainer').innerWidth();
	var canvas_height = canvas_width * 0.5;
	var radius = canvas_height * 0.01;

	// Create the SVG element (as a child of the #frequencyChangeContainer div)
	var canvas = d3.select('#frequencyChangeContainer').append('svg')
		.attr('width', canvas_width)
		.attr('height', canvas_height)
		.attr('overflow', 'hidden');

	// Add a bordered rectangle the same size as the SVG element, for the background
	canvas.append('rect')
		.attr('x', 0)
		.attr('y', 0)
		.attr('width', canvas_width)
		.attr('height', canvas_height)
		.attr('class', 'chartBackground');

	// Draw up and down arrows
	var upArrowFunction = d3.svg.line()
		.x(function(d) { return d.x * canvas_width; })
		.y(function(d) { return d.y * canvas_height; })
		.interpolate('linear');
	var downArrowFunction = d3.svg.line()
		.x(function(d) { return d.x * canvas_width; })
		.y(function(d) { return (1 - d.y) * canvas_height; })
		.interpolate('linear');
	var arrow_data = [{'x': 0.3, 'y': 0.35},  {'x': 0.5, 'y': 0.05},
						{'x': 0.7, 'y': 0.35}, {'x': 0.6, 'y': 0.35},
						{'x': 0.6, 'y': 0.45}, {'x': 0.4, 'y': 0.45},
						{'x': 0.4, 'y': 0.35}, {'x': 0.3, 'y': 0.35}];
	canvas.append('path')
		.attr('d', upArrowFunction(arrow_data))
		.style('stroke', 'none')
		.style('fill', 'green')
		.style('opacity', 0.2);
	canvas.append('path')
		.attr('d', downArrowFunction(arrow_data))
		.style('stroke', 'none')
		.style('fill', 'red')
		.style('opacity', 0.2);

	// Draw red line to indicate mid point
	canvas.append('rect')
		.attr('x', 0)
		.attr('y', canvas_height * 0.5)
		.attr('width', canvas_width)
		.attr('height', 1)
		.attr('fill', '#FF0000');


	// x-axis scale - absolute frequency at document year
	var x_domain;
	if (lemmas.length > 1) {
		x_domain = [d3.min(lemmas, function(d) { return d.ftable.frequency(document_year); }),
					d3.max(lemmas, function(d) { return d.ftable.frequency(document_year); })];
	} else if (lemmas.length === 1) {
		x_domain = [0.1, lemmas[0].ftable.frequency(document_year)];
	} else {
		x_domain = [0.1, 1];
	}
	var x_scale = d3.scale.log()
		.domain(x_domain)
		.range([canvas_width * 0.05, canvas_width * 0.9]);

	// y-axis scale - rate of change
	// Two separate y-scales, since we essentially draw two charts: one in
	//   the top half for lemmas increasing in frequency, the other in the
	//   bottom half for lemmas decreasing in frequency.
	var y_domain1;
	if (increases.length > 1) {
		y_domain1 = [increases[0].ftable.delta(), increases[increases.length-1].ftable.delta()];
	} else if (increases.length === 1) {
		y_domain1 = [0.1, increases[0].ftable.delta()];
	} else {
		y_domain1 = [0.1, 1];
	}
	var y_scale_increasing = d3.scale.log()
		.domain(y_domain1)
		.range([canvas_height * 0.05, canvas_height * 0.45]);

	var y_domain2;
	if (decreases.length > 1) {
		y_domain2 = [decreases[0].ftable.delta(), decreases[decreases.length-1].ftable.delta()];
	} else if (decreases.length === 1) {
		y_domain2 = [0.1, decreases[0].ftable.delta()];
	} else {
		y_domain2 = [0.1, 1];
	}
	var y_scale_decreasing = d3.scale.log()
		.domain(y_domain2)
		.range([canvas_height * 0.55, canvas_height * 0.95]);

	// Draw lemma labels
	var font_size = canvas_height * 0.03;
	var labels = canvas.selectAll('text')
		.data(lemmas);

	labels.enter().append('text')
		.attr('class', 'frequencyChangeText')
		.attr('x', function(d) { return x_position(d) + (radius * 2); })
		.attr('y', function(d) { return y_position(d); })
		.text( function(d) { return d.lemma; })
		.style('fill', 'black')
		.style('font-size', font_size + 'px');

	// Draw data points
	var datapoints = canvas.selectAll('circle')
		.data(lemmas, function (d) { return d.id; });

	datapoints.enter().append('circle')
		.attr('class', 'frequencyChangePoint')
		.attr('cx', function(d) { return x_position(d); })
		.attr('cy', function(d) { return y_position(d); })
		.attr('r', radius)
		.style('fill', function(d) { return frequencyChangeColor(d); });

	function x_position(d) {
		return x_scale(d.ftable.frequency(document_year));
	}

	function y_position(d) {
		if (d.ftable.increasing()) {
			return y_scale_increasing(d.ftable.delta());
		} else {
			return y_scale_decreasing(d.ftable.delta());
		}
	}

	function frequencyChangeColor(d) {
		if (d.ftable.increasing()) {
			return '#00CC00';
		} else {
			return '#FF0000';
		}
	}


	// Set event listeners for clicks/mouseovers on data points
	datapoints
		.on('click', function (d) {
			hideFrequencyChangeTooltip();
			showLemmaDetails(d, d3.event);
		})
		.on('mouseover', function(d) {
			showFrequencyChangeTooltip(d, d3.event);
		})
		.on('mouseout', function() {
			hideFrequencyChangeTooltip();
		});

	// Display the small pop-up showing the lemma name
	frequency_change_tooltip = $('div#frequencyChangeTooltip');
	function showFrequencyChangeTooltip(d, event) {
		var text = frequencyChangeTooltipText(d);
		// Populate the pop-up
		frequency_change_tooltip.find('h2').html(d.lemma);
		frequency_change_tooltip.find('p#frequencyChangeDetails').html(text);
		// Reposition the pop-up
		frequency_change_tooltip.css('left', (event.pageX) + 'px');
		frequency_change_tooltip.css('top', (event.pageY) + 'px');
		frequency_change_tooltip.css('display', 'block');
	}

	// Hide the small pop-up showing the lemma name
	function hideFrequencyChangeTooltip() {
		frequency_change_tooltip.css('display', 'none');
	}

	function frequencyChangeTooltipText(d) {
		var text = 'This word ';
		if (d.ftable.increasing()) {
			text += 'increased';
		} else {
			text += 'decreased';
		}
		text += ' in frequency<br/>by x ' + (d.ftable.delta() * 1.0);
		text += ' between ' + d.ftable.delta_start + ' and ' + d.ftable.delta_end + '.';
		return text;
	}
}




//===============================================================
// Sortable table of lemmas
//===============================================================

var lemma_table_sortcolumn, lemma_table_direction;

function initializeLemmaTable() {
	lemmaAlphaSort('ascending');
	composeLemmaTable();
	lemma_table_sortcolumn = 'lemma';
	lemma_table_direction = 'ascending';

	// Listeners
	$('#lemmaRank > thead').find('th').click( function() {
		resortLemmaTable($(this));
	});
}

function composeLemmaTable() {
	var tbody = $('#lemmaRank > tbody');
	tbody.html(''); // discard any existing rows
	for (var i = 0; i < lemmadata_sortable.length; i += 1) {
		var l = lemmadata_sortable[i];
		var display_year = l.year;
		if (display_year < 1150) {
			display_year = '&lt; 1150';
		}
		var display_fq = l.f2000() * 1;
		if (display_fq < .0001) {
			display_fq = '&lt; .0001';
		}

		var row = $('<tr><td>' + (i + 1) + '</td><td class="lemmaCell token-oed" idx="' + l.idx + '">' + l.lemma + '</td><td>' + l.count + '</td><td>' + l.ftable.frequency(document_year, true) + '</td><td>' + display_fq + '</td><td>' + display_year + '</td><td>' + l.language + '</td></tr>');
		row.css('background-color', languageToColour(l.family, 'pale'));
		row.appendTo(tbody);
	}

	// Set listeners for clicks on any row in the table body
	$('#lemmaRank > tbody').find('td.lemmaCell').click( function(event) {
		displayLemmaDetails($(this), event);
	});
}

// Sorting functions
function resortLemmaTable(cell) {
	var column = cell.attr('sort');
	if (column) {
		$('#lemmaRank > thead').find('th').removeClass('highlighted');
		cell.addClass('highlighted');

		var direction = 'ascending';
		if (column === lemma_table_sortcolumn && lemma_table_direction === 'ascending') {
			direction = 'descending';
		}
		if (column === 'lemma') {
			lemmaAlphaSort(direction);
		} else if (column === 'occurrences') {
			lemmaOccurrenceSort(direction);
		} else if (column === 'frequency') {
			lemmaFrequencySort(direction);
		} else if (column === 'modfrequency') {
			lemmaModFrequencySort(direction);
		} else if (column === 'year') {
			lemmaDateSort(direction);
		} else if (column === 'origin') {
			lemmaLangSort(direction);
		}
		composeLemmaTable();
		lemma_table_sortcolumn = column;
		lemma_table_direction = direction;
	}
}

function lemmaAlphaSort(direction) {
	lemmadata_sortable.sort(function(a, b) {
		if (a.sort < b.sort) {
			return -1;
		} else if (a.sort > b.sort) {
			return 1;
		} else {
			return 0;
		}
	});
	if (direction == 'descending') {
		lemmadata_sortable.reverse();
	}
}

function lemmaLangSort(direction) {
	if (direction === 'ascending') {
		lemmadata_sortable.sort(function(a, b) {
			if (a.family < b.family) {
				return -1;
			} else if (a.family > b.family) {
				return 1;
			} else {
				return 0;
			}
		});
	} else {
		lemmadata_sortable.sort(function(a, b) {
			if (a.family > b.family) {
				return -1;
			} else if (a.family < b.family) {
				return 1;
			} else {
				return 0;
			}
		});
	}
}

function lemmaDateSort(direction) {
	if (direction === 'ascending') {
		lemmadata_sortable.sort(function(a, b) {
			return clampedDate(a.year) - clampedDate(b.year);
		});
	} else {
		lemmadata_sortable.sort(function(a, b) {
			return clampedDate(b.year) - clampedDate(a.year);
		});
	}
}

function lemmaFrequencySort(direction) {
	if (direction === 'ascending') {
		lemmadata_sortable.sort(function(a, b) {
			return clampedFrequency(a.ftable.frequency(document_year, true)) - clampedFrequency(b.ftable.frequency(document_year, true));
		});
	} else {
		lemmadata_sortable.sort(function(a, b) {
			return clampedFrequency(b.ftable.frequency(document_year, true)) - clampedFrequency(a.ftable.frequency(document_year, true));
		});
	}
}

function lemmaModFrequencySort(direction) {
	if (direction === 'ascending') {
		lemmadata_sortable.sort(function(a, b) {
			return clampedFrequency(a.f2000()) - clampedFrequency(b.f2000());
		});
	} else {
		lemmadata_sortable.sort(function(a, b) {
			return clampedFrequency(b.f2000()) - clampedFrequency(a.f2000());
		});
	}
}

function lemmaOccurrenceSort(direction) {
	if (direction === 'ascending') {
		lemmadata_sortable.sort(function(a, b) {
			return a.count - b.count;
		});
	} else {
		lemmadata_sortable.sort(function(a, b) {
			return b.count - a.count;
		});
	}
}




//===============================================================
// Utilities
//===============================================================

function equivalentFrequency(occurrences) {
	return document_million_ratio * occurrences;
}


function inverseFrequency(frequency, as_text) {
	var inv_fq = 1000000 / clampedFrequency(frequency);
	inv_fq = inv_fq.toPrecision(1) * 1;

	if (as_text) {
		if (inv_fq === 1000000) {
			inv_fq = 'million';
		} else if (inv_fq >= 1000000) {
			inv_fq = inv_fq / 1000000;
			inv_fq = (inv_fq * 1) + ' million';
		} else if (inv_fq === 1000) {
			inv_fq = 'thousand';
		} else if (inv_fq >= 1000) {
			inv_fq = inv_fq / 1000;
			inv_fq = (inv_fq * 1) + ',000';
		} else {
			inv_fq = inv_fq * 1;
		}
	}

	return inv_fq;
}


function clampedFrequency(frequency) {
	return d3.max([frequency, 0.0001]);
}


function clampedDate(year) {
	return d3.max([year, 1150]);
}


function log10(val) {
	return Math.log(val) / Math.LN10;
}


function compileContinuousText(mode) {
	var text_html = '<p>';
	for (var i = 0; i < tokendata.length; i += 1) {
		var t = tokendata[i];

		if (t.spacebefore === 2) {
			text_html += '</p><p>';
		} else if (t.spacebefore === 1) {
			text_html += ' ';
		}

		if (t.status === 'punc' || t.status === 'exception') {
			text_html += t.token;
		} else if (mode === 'thesaurus') {
			text_html += thesaurusSensitiveToken(t);
		} else {
			text_html += lemmaSensitiveToken(t);
		}
	}
	text_html += '</p>';
	return text_html;
}

function lemmaSensitiveToken(t) {
	var node;
	if (t.status === 'proper') {
		node = '<span class="token-proper">' + t.token + '</span>';
	} else if (t.status === 'missing') {
		node = '<span class="token-missing">' + t.token + '</span>';
	} else {
		node = '<span class="token-oed" idx="' + t.lemma_index + '">' + t.token + '</span>';
	}
	return node;
}

function thesaurusSensitiveToken(t) {
	var node;
	var wordclass = t.wordclass;
	if (wordclass === 'VBND') {
		wordclass = 'VBD';
	}
	if (t.status === 'oed' && lemmadata[t.lemma_index].thesaurusid > 0) {
		node = '<span class="token-theslinked" classid="' + lemmadata[t.lemma_index].thesaurusid + '" wordclass="' + wordclass + '">';
		node += '<span class="disp">' + t.token + '</span><span class="src">' + t.token + '</span>';
		node += '</span>';
	} else {
		node = t.token;
	}
	return node;
}
