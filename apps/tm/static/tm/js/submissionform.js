/*global $*/
'use strict';

var max_words = 500;
var textarea,
	wordcount_target;

//===============================================================
// Functions to run once the page has loaded
//===============================================================

$(document).ready( function() {
	textarea = $('#submissionForm textarea');
	wordcount_target = $('#submissionForm numWords');

	if (textarea.length) {
		checkWordCount();
		textarea.bind('keydown', function() { checkWordCount() });
		textarea.bind('blur', function() { checkWordCount() });
	}
});


function checkWordCount() {
	var words = textarea.val().split(/[^ \t][ \t]+/);
	var lines = textarea.val().split(/\n\b/);
	var wordcount = words.length + lines.length - 2;
	wordcount_target.text(wordcount);
	if (wordcount > max_words) {
		wordcount_target.css('color', 'red');
	} else {
		wordcount_target.css('color', 'black');
	}
}
