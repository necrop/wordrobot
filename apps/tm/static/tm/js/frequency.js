/* global $, d3, document_year */
'use strict';


function FrequencyTable(data, startyear) {
	this.startyear = startyear
	this.f = {};
	this.f[1100] = 0;
	this.f[1750] = data[0];
	this.f[1800] = data[1];
	this.f[1850] = data[2];
	this.f[1900] = data[3];
	this.f[1950] = data[4];
	this.f[2000] = data[5];
	// Run down to zero at the word's first year of use
	if (startyear <= 1150) {
		this.f[1150] = this.f[1750];
	} else {
		this.f[startyear] = 0;
	}

	this.ordered = [];
	for (var key in this.f) {
		this.ordered.push(key);
	}
	this.ordered.sort();

	// Values used for delta (change in frequency)
	this.delta_value = null;
	this.delta_start = null;
	this.delta_end = null;
}

// These dummy values should be overwritten by
//   FrequencyTable.setDeltaBracket()
FrequencyTable.delta_floor = 1750;
FrequencyTable.delta_ceiling = 2000;


FrequencyTable.prototype.frequency = function(year, store) {
	if (year < this.startyear) {
		return 0;
	} else if (year > 2000) {
		return this.f[2000];
	} else if (this.f[year] != null) {
		return this.f[year];
	} else {
		var value = this.interpolate(year);
		if (store) {
			this.f[year] = value;
		}
		return value;
	}
}

FrequencyTable.prototype.interpolate = function(year) {
	var ceiling, floor;
	for (var i = 1; i < this.ordered.length; i += 1) {
		if (this.ordered[i] > year) {
			ceiling = this.ordered[i];
			floor = this.ordered[i-1];
			break;
		}
	}
	// Linear interpolation between floor and ceiling
	var progress = (year - floor) / (ceiling - floor);
	var value = this.f[floor] + (this.f[ceiling] - this.f[floor]) * progress;
	if (value > 1) {
		return Math.round(value.toPrecision(2) * 1.0);
	} else {
		return value.toPrecision(2) * 1.0;
	}
}

FrequencyTable.prototype.delta = function() {
	// Return the rate of change (positive or negative) from the start to
	// the end of the delta bracket
	if (this.delta_value == null) {
		var z = this.compute_delta();
		this.delta_value = z[0];
		this.delta_start = z[1];
		this.delta_end = z[2];
	}
	return this.delta_value;
}

FrequencyTable.prototype.increasing = function() {
	// Return true if frequency is increasing during the delta bracket
	//  (i.e. this.delta() is greater than 1).
	if (this.delta() > 1) {
		return true;
	} else {
		return false;
	}
}


FrequencyTable.prototype.compute_delta = function() {
	// Avoid using a start-date that's earlier than the lemma's
	// first date (where frequency=0), since this could produce
	// an infinite result
	var delta;

	var start_date = FrequencyTable.delta_floor;
	if (start_date < this.startyear + 5) {
		start_date = this.startyear + 5;
	}

	if (document_year < 1730) {
		delta = 1;
	} else if (FrequencyTable.delta_ceiling - start_date < 20) {
		delta = 1;
	} else {
		var start_frequency = this.frequency(start_date, false);
		if (start_frequency < 0.0001) {
			start_frequency = 0.0001;
		}
		var end_frequency = this.frequency(FrequencyTable.delta_ceiling, false);
		if (end_frequency < 0.0001) {
			end_frequency = 0.0001;
		}
		delta = (end_frequency / start_frequency).toPrecision(2);
	}
	return [delta, start_date, FrequencyTable.delta_ceiling];
}



//------------------------------------------------------
// Class methods
//------------------------------------------------------

FrequencyTable.setDeltaBracket = function() {
	var ceiling, floor;
	ceiling = document_year + 50;
	if (ceiling > 2010) {
		ceiling = 2010;
	}
	floor = document_year - 50;
	if (floor < 1750) {
		floor = 1750;
	}
	FrequencyTable.delta_floor = floor;
	FrequencyTable.delta_ceiling = ceiling;
}
