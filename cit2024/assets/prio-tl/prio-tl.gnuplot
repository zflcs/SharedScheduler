set terminal pdfcairo enhanced size 20in,8in font "Arial,54"
set output '../prio-tl.pdf'

set key samplen 1 width 0.5 horizontal center top Left reverse at graph -0.2, 1.2 
set noborder
set xtics nomirror
set ytics nomirror
set grid ytics
set grid linetype 0

set xrange [0.5 : 8.5]
set xtics ("0" 1, "1" 2, "2" 3, "3" 4, "4" 5, "5" 6, "6" 7, "7" 8)
set xtics border in scale -0.5,0 offset 0,0.25
# set xlabel "Priorities"

set multiplot layout 1, 2

set ylabel 'Throughput(IOPS)'

############################################################## 
datafile = 'prio-throughput.dat'
set size 0.525, 0.9
set origin 0.0, 0.0
set style fill solid 1 border -1
plot datafile using 2 with linespoints lw 10 title '', '' \
    using 3 with linespoints lw 10 title '', '' \
    using 4 with linespoints lw 10 title ''

############################################################## 
set ylabel 'Latency(s)'
datafile = 'prio-latency.dat'
set size 0.55, 0.9
set origin 0.475, 0.0
set style fill solid 1 border -1
plot datafile using ($2/1000000) with linespoints lw 10 title 'core1', '' \
    using ($3/1000000) with linespoints lw 10 title 'core2', '' \
    using ($4/1000000) with linespoints lw 10 title 'core3'

############################################################## 

unset multiplot