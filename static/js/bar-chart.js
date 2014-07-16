function add_bar_chart(row, cnt_ok, cnt_error, cnt_missing) {

	var cell = $('<td></td>');

	if (!cnt_missing)
		cnt_missing = 0;

	var cnt_total = cnt_ok + cnt_error + cnt_missing;

	/* complete chart (green bar) */
	if (cnt_total > 0)
		var chart = $('<div class="bar-box" title="' + Math.round(100 * cnt_ok / cnt_total) + '%"></div>');
	else
		var chart = $('<div class="bar-box bar-empty"></div>');

	/* the width is always a multiple of 5% */

	pct_error = (cnt_error * 100.0 / cnt_total);
	pct_missing = (cnt_missing * 100.0 / cnt_total);
	
	pct_error_rnd = (5 * Math.round(pct_error/5));
	pct_missing_rnd = (5 * Math.round(pct_missing/5));

	/* if either of the values is (<5), increment it to 5% (and decrement the other value, if needed) */
	if ((pct_error_rnd > 0) && (pct_error_rnd < 5.0)) {
		pct_error_rnd = 5.0;
		pct_missing_rnd = (pct_missing_rnd > 95.0) ? 95.0 : pct_missing_rnd;
	}

	if ((pct_missing_rnd > 0) && (pct_missing_rnd < 5.0)) {
		pct_missing_rnd = 5.0;
		pct_error_rnd = (pct_error_rnd > 95.0) ? 95.0 : pct_error_rnd;
	}

	if (pct_error_rnd > 0)
		chart.append('<div class="chart-bar bar-error" style="width: ' + pct_error_rnd + '%" title="' + Math.round(pct_error) + '%"><div class="bar-box-border">&nbsp;</div></div>');

	/* missing (orange bar) */
	if (pct_missing_rnd > 0)
		chart.append('<div class="chart-bar bar-warning" style="width: ' + pct_missing_rnd + '%" title="' + Math.round(pct_missing) + '%"><div class="bar-box-border">&nbsp;</div></div>');

	cell.append(chart);
	row.append(cell);

}