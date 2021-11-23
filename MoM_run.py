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

def _getParser():
    parser = argparse.ArgumentParser(description=prolog,epilog=epilog,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    joblist = ['GFMS','HWRF','HWRF_MOM','DFO','DFO_MOM','VIIRS','VIIRS_MOM']
    parser.add_argument('-j','--job', action='store', type=str.upper, dest='job',required=True,help='run a job',choices=joblist)

    return parser

def main():
    """execute momjob"""
    # Read command line arguments
    parser = _getParser()
    results = parser.parse_args()
    print(results)

if __name__ == '__main__':
    main()
    