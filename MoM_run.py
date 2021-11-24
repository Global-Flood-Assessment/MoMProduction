"""
main script to run various MoM processing jobs
"""

prolog="""
**PROGRAM**
    MoM_run.py
      
**PURPOSE**
    main script to run various MoM processing jobs

**USAGE**
"""
epilog="""
**EXAMPLE**
    MoM_run.py 
               
"""

import argparse
import logging
from settings import *

from GFMS_tool import GFMS_cron

def _getParser():
    parser = argparse.ArgumentParser(description=prolog,epilog=epilog,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    joblist = ['GFMS','HWRF','HWRF_MOM','DFO','DFO_MOM','VIIRS','VIIRS_MOM']
    parser.add_argument('-j','--job', action='store', type=str.upper, dest='job',required=True,help='run a job',choices=joblist)

    return parser

def run_job(cronjob):
    """run various cron job"""
    logging.info("run " + cronjob)
    if cronjob == "GFMS":
        GFMS_cron()

def main():
    """execute momjob"""
    # Read command line arguments
    parser = _getParser()
    results = parser.parse_args()
    run_job(results.job)

if __name__ == '__main__':
    main()
    