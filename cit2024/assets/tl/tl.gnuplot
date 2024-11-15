set terminal pdfcairo enhanced size 20in,8in font "Arial,54"
set output '../tl.pdf'

set key samplen 0.5 width 0.5 horizontal center top Left reverse at graph -0.2, 1.2

# unset key
set noborder
set xtics nomirror
set ytics nomirror
set grid ytics
set grid linetype 0

set xrange [0.5 : 8.5]
set xtics ("1" 1, "2" 2, "4" 3, "8" 4, "16" 5, "32" 6, "64" 7, "96" 8)
# set xlabel "Connections"

set multiplot layout 1, 2

############################################################## 
set logscale y 2
set ytics ("2^4" 16, "2^5" 32, "2^6" 64, "2^7" 128, "2^8" 256, "2^9" 512, "2^{10}" 1024)
set ylabel 'Throughput(IOPS)'
datafile = 'mode-throughput.dat'
set size 0.525, 0.9
set origin 0, 0
set style fill solid 1 border -1
plot datafile using 2 with histogram title '', '' \
    using 3 with histogram title '', '' \
    using 4 with histogram title '', '' \
    using 5 with histogram title '', \

############################################################## 
unset ytics
set ytics nomirror
set grid ytics
set logscale y 10
set ytics format "10^{%T}"
set ylabel 'Latency(ms)'
datafile = 'mode-latency.dat'
set size 0.55, 0.9
set origin 0.475, 0
set style fill solid 1 border -1
plot datafile using ($2/1000) with histogram title 'kcuc', '' \
    using ($3/1000) with histogram title 'kcut', '' \
    using ($4/1000) with histogram title 'ktut', '' \
    using ($5/1000) with histogram title 'ktuc', \

unset multiplot