std_msgs/Header header

# Sequential sample number assigned by the Hyperion instrument.
uint64 serial

# Instrument timestamp, expressed as seconds since Unix epoch.
float64 instrument_timestamp

# Number of detected peaks on each Hyperion channel.
uint32[] peak_counts

# Peak wavelengths returned by the instrument, in nm.
# Values are ordered by channel, matching peak_counts.
float64[] wavelengths
