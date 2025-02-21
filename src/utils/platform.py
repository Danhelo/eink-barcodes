import platform
import os

def is_raspberry_pi():
    """Check if running on Raspberry Pi."""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Model'):
                    return 'Raspberry Pi' in line
        return False
    except:
        return False

def setup_display():
    """Configure display settings based on platform."""
    system = platform.system()

    if system == 'Darwin':  # macOS
        os.environ['QT_MAC_WANTS_LAYER'] = '1'
        return 'Virtual'

    elif system == 'Linux':
        if is_raspberry_pi():
            # Configure for Raspberry Pi
            if not os.environ.get('DISPLAY'):
                os.environ['DISPLAY'] = ':0'
            return 'Raspberry Pi'
        else:
            return 'Linux'

    else:
        return system
