/* global $, d3 */
'use strict';

var ceilings = [1800, 1850, 1900, 1950, 2000];

function FrequencyTable(data, year) {
	this.f = {};
	this.f[1750] = data[0];
	this.f[1800] = data[1];
	this.f[1850] = data[2];
	this.f[1900] = data[3];
	this.f[1950] = data[4];
	this.f[2000] = data[5];
	this.startyear = year
}

function frequencyValue(year, store) {
	if (year < this.startyear) {
		return 0;
	} else if (year < 1750) {
		return this.f[1750];
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
FrequencyTable.prototype.frequency = frequencyValue;

function linearInterpolation(year) {
	var ceiling, floor;
	for (var i = 0; i < ceilings.length; i += 1) {
		if (ceilings[i] > year) {
			ceiling = ceilings[i];
			floor = ceilings[i] - 50;
			break;
		}
	}
	var progress = (year - floor) / 50;
	var value = this.f[floor] + (this.f[ceiling] - this.f[floor]) * progress;
	if (value > 1) {
		return Math.round(value.toPrecision(2) * 1.0);
	} else {
		return value.toPrecision(2) * 1.0;
	}
}
FrequencyTable.prototype.interpolate = linearInterpolation;
