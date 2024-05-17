set terminal pdfcairo enhanced size 8in,6in font "Arial,24"
set output 'prio-latency.pdf'
fn(v) = sprintf("%.0f", v)
compare(a, b) = a / b
fn2(v) = sprintf("%.2f", v)

set key horizontal center top Left reverse at graph 0.5, 1.125

fn(v) = sprintf("%.0f", v)
compare(a, b) = a / b
fn2(v) = sprintf("%.2f", v)

# unset key
set noborder
set xtics nomirror
set ytics nomirror
set grid ytics
set grid linetype 0

set xrange [0.5 : 8.5]
set xtics ("0" 1, "1" 2, "2" 3, "3" 4, "4" 5, "5" 6, "6" 7, "7" 8)
set xlabel "Priorities"

# set logscale y 2
set ylabel 'Latency(s)'
# set y2range [0 : 2000]
# set logscale y2
# set y2tics
datafile = 'prio-latency.dat'
set size 1.0, 0.9
set style fill solid 1 border -1
plot datafile using ($2/1000000) with linespoints title 'core-1', '' \
    using ($3/1000000) with linespoints title 'core-2', '' \
    using ($4/1000000) with linespoints title 'core-3'
