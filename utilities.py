'''
utilities.py
routines shared across the modules

'''

import settings
import geopandas 

def watersheds_gdb_reader():
    """reader watersheds gdb into geopandas"""
    
    # pfaf_id, areakm2
    watersheds = geopandas.read_file(settings.WATERSHED_SHP)
    # issue #1
    # some old code use aqid, need to be updated
    #watersheds.rename(columns={"pfaf_id": "aqid"},inplace=True)
    #watersheds.set_index("aqid",inplace=True)
    watersheds.set_index("pfaf_id",inplace=True) 

    return watersheds

def main():
    ''' test routines'''

    watershed = watersheds_gdb_reader()
    print(watershed.head)

if __name__ == '__main__':
    main()
