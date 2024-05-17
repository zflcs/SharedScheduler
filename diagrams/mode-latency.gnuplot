set terminal pdfcairo enhanced size 8in,6in font "Arial,24"
set output 'mode-latency.pdf'
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
set xtics ("1" 1, "2" 2, "4" 3, "8" 4, "16" 5, "32" 6, "64" 7, "96" 8)
set xlabel "Connections"

set logscale y 10
set ylabel 'Latency(ms)'
# set y2range [0 : 2000]
# set logscale y2
# set y2tics
datafile = 'mode-latency.dat'
set size 1.0, 0.9
set style fill solid 1 border -1
plot datafile using ($2/1000) with histogram title 'kcuc', '' \
    using ($3/1000) with histogram title 'kcut', '' \
    using ($4/1000) with histogram title 'ktut', '' \
    using ($5/1000) with histogram title 'ktuc', \
