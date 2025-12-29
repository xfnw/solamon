# solamon

slurp up some metrics from irc into a influxdb-compatible time series
database such as [greptime](https://docs.greptime.com/) or
[victoriametrics](https://docs.victoriametrics.com/)

designed to collect anonymized stuff solanum makes available to normal
users (hence the name) without requiring joining any channels (that'd
be creepy), but other ircds that allow `LUSERS` and `STATS m`
should also work

