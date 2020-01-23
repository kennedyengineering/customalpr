# utility function
# return how long the server has been running


def get_system_uptime():
	with open('/proc/uptime', 'r') as f:
		uptime_seconds = float(f.readline().split()[0])

	return uptime_seconds
