#!/usr/bin/python
from application import db, direct
import sys

reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('/var/packages/subliminal/target/app/configobj')

if __name__ == '__main__':
    db.setup()
    subliminal = direct.Subliminal()
    subliminal.setup()
