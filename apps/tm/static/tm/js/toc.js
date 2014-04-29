/* global $, d3 */
'use strict';


$(document).ready( function() {
	generateToc();
});


//===============================================================
// Tables of contents
//===============================================================

function generateToc() {
	var menu_container = $('#sectionsTocContainer');
	var menu_list1 = $('#sectionsToc > ul').first();
	var menu_list2 = $('#sectionsTocShort > ul').first();

	var menu = [];
	var sections = $('.row-fluid');
	sections.each(function(i) {
		var toc_id = 'toc-' + (i + 1);
		var header = $(this).find('h2').first();
		$(this).attr('id', toc_id);

		if (header.text() === 'Tinker') {
			$('#tinkerlink').attr('href', '#' + toc_id);
		}

		addSectionNumber(header, i);
		menu.push([toc_id, header.text(), i + 1]);
	});

	// Populate the menu container
	for (var i = 0; i < menu.length; i += 1) {
		var item = menu[i];
		var rowfull = '<li><a href="#' + item[0] + '">' + item[1] + '&nbsp;<i class="icon-chevron-right"></i></a></li>';
		var rowshort = '<li><a href="#' + item[0] + '">' + item[2] + '</a></li>';
		menu_list1.append(rowfull);
		menu_list2.append(rowshort);
	}

	// Reposition
	var distance_from_bottom = ($(window).height() / 2) - (menu_container.outerHeight() / 2);
	menu_container.css('bottom', distance_from_bottom + 'px');

	// Set listeners for mouseovers and clicks
	menu_container.hover(function() {
		$('#sectionsToc').show();
		$('#sectionsTocShort').hide();
	}, function() {
		$('#sectionsToc').hide();
		$('#sectionsTocShort').show();
	});
	menu_container.find('a[href]').click( function(event) {
		scrollToSection(event, $(this));
	});
}

function scrollToSection(event, element) {
	var target = $('body').find(element.attr('href')).first();
	var offset = target.offset(),
		destination = offset.top;
	// Scroll to the target element
	$('html, body').animate({scrollTop: destination}, 500);
	event.preventDefault();
}

function addSectionNumber(header, i) {
	var current_text = header.text();
	header.text((i + 1) + '. ' + current_text);
}
