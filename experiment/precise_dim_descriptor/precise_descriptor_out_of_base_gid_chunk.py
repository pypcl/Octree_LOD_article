# -*- coding: utf-8 -*-
"""
Created on Wed Feb 17 18:53:09 2016

@author: RCura
"""
 
import psycopg2

def connect_to_base():
    conn = psycopg2.connect(  
        database='test_pointcloud'
        ,user='postgres'
        ,password='postgres'
        ,host='172.16.3.50'
        ,port='5432' ) 
    cur = conn.cursor()
    return conn, cur  

def execute_querry(q,arg_list,conn,cur):  
    #print q % arg_list    
    cur.execute( q ,arg_list)
    conn.commit()
    
    
def get_list_of_job(limit):
    import numpy as np
    #connect to database
    conn, cur = connect_to_base()
    #get thelist of job
    q = """ SELECT gid 
        FROM lod.bench_small_cubes
        WHERE dim_loddiff_broad IS NULL
        LIMIT %s """ 
    execute_querry(q,[limit],conn,cur)
    gid = cur.fetchall() 
    gids = np.asarray(gid).T[0]
    cur.close()
    conn.close()
    return gids


def cut_list_into_chunk(gid, max_chunk_size):
    """ given a list , tries to cut it into smaller parts of max_chunk_size """
    import numpy as np
    import math
    result = []
    for i in np.arange(0,math.floor(gid.size/max_chunk_size)+1):
        key_local_start = int(math.ceil(i * max_chunk_size)) 
        key_local_end = int(math.trunc((i+1) * max_chunk_size))
        key_local_end = gid.size if key_local_end > gid.size else key_local_end
        extract = gid[np.arange(key_local_start,key_local_end)]
        if extract.size >0 :
            result.append(gid[np.arange(key_local_start,key_local_end)])
                
    return result 


def process_one_chunk( gid_extract  ):
    """ given a subset of the gid, do something with it"""     
    #create connection
    conn, cur = connect_to_base()
    
    q = """ 
        SET SEARCH_PATH TO lod, rc_lib, public;     
        SELECT lod.rc_update_ppls_dim_lods(gid, tot_level:= 1, tot_level_broad:=3, broad_pow:=0)
        FROM lod.bench_small_cubes
        WHERE gid = ANY (%s);"""
    arg_list = [gid_extract.tolist() ]
    #printing_arglist(arg_list)
    execute_querry(q,arg_list,conn,cur)  
    #print("gid dealt with : ", gid_extract) 
    #close connection
    cur.close()
    conn.close()
    return None

 
    
    
def test_mono():
    import numpy as np
    max_chunk_size = 50
    overall_max = 100
    
    gids = get_list_of_job(overall_max)
    #print("gid : ",gid)
    gid_sequenced = cut_list_into_chunk(np.asarray(gids), max_chunk_size)
    #print('gid_sequenced ',gid_sequenced)
    for i in gid_sequenced:
        process_one_chunk(i)



def multiprocess():
    import  multiprocessing as mp; 
    import random;  
    import numpy as np
    import datetime ; 
    
    time_start = datetime.datetime.now(); 
    print 'starting : %s ' % (time_start); 
    
    processes = 12
    max_chunk_size = 200
    overall_max = 1000000
    
    gid = get_list_of_job(overall_max)
    
    #print("gid : ",gid)
    gid_sequenced = cut_list_into_chunk(np.asarray(gid), max_chunk_size) 
    random.shuffle(gid_sequenced)
    print 'job in line, ready to process : %s ' % (datetime.datetime.now()); 
    #print('gid_sequenced ',gid_sequenced) 
    pool = mp.Pool(processes)
    results = pool.map(process_one_chunk, gid_sequenced)
    time_end = datetime.datetime.now(); 
    print 'ending : %s ' % (time_end); 
    print 'duration : %s ' % (time_end-time_start)
    return results
    
#test_mono()


##dirty windows trick
def main():
    multiprocess()
if __name__ == "__main__":
    main()