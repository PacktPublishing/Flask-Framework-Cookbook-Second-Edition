activate_this = '/home/ubuntu/workspace/cookbook11/bin/activate_this.py'
exec(open(activate_this).read(), dict(__file__=activate_this))

from my_app import app as application
import sys, logging
logging.basicConfig(stream = sys.stderr)
