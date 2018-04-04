#!/usr/bin/env python3
#
#
#
# #     |  get_omap_keys = validate_func(*args, **kwargs)
#      |  
#      |  get_omap_vals = validate_func(*args, **kwargs)
#      |  
#      |  get_omap_vals_by_keys = validate_func(*args, **kwargs)

#
#


# TODO: delete initial id in each table 


import os
import time, datetime
import rados 
import rbd 
import dataset
import json
import pprint
import logging
import sys 
from subprocess import PIPE, Popen


CONF_FILE = './ceph.conf'
KEYRING_FILE = './ceph.client.admin.keyring'
DATABASE_CONNECTION = 'sqlite:///'
DATABASE_FILE = 'ceph_timeline.db'
START_TIME = time.strftime("%Y%m%d:%H%M%S")
CWD = os.getcwd()


DIR_ROOT =  CWD + '/ceph_timeline_output_' + START_TIME
DIR_MAP_MON = DIR_ROOT + '/map_mon'
DIR_MAP_OSD = DIR_ROOT + '/map_osd'
DIR_MAP_PG = DIR_ROOT + '/map_pg'


INT_LENGTH = 5 


logging.basicConfig(level=logging.DEBUG)
pp = pprint.PrettyPrinter(indent=4)

def main():

    ## Create directory structure and chdir into root_dir

    os.mkdir(DIR_ROOT)
    os.mkdir(DIR_MAP_MON)
    os.mkdir(DIR_MAP_OSD)
    os.mkdir(DIR_MAP_PG)


    os.chdir(DIR_ROOT)

    ## Initiate _new_ database and tables ## 

    
    db = dataset.connect(DATABASE_CONNECTION + DATABASE_FILE)

    table_ceph_cluster = db.create_table('ceph_cluster', primary_id=False)
    table_ceph_pools = db.create_table('ceph_pools', primary_id=False)
    table_rbd_images = db.create_table('ceph_rbd_images', primary_id=False)
    table_snapshots = db.create_table('ceph_snapshots', primary_id=False)
    table_ceph_objects = db.create_table('ceph_objects')
    table_mon_map = db.create_table('ceph_monmap', primary_id=False)
    table_osd_map = db.create_table('ceph_osdmap', primary_id=False)



    # MON: check current epoch and fill MON table

    monmap = Popen(['ceph', 'mon', 'dump', '-f', 'json-pretty'], stdout=PIPE)
    monmap = monmap.stdout.read().decode('ascii')
    monmap = json.loads(monmap)
    mon_epoch = monmap['epoch']

    while ( mon_epoch > 0 ):

        monmap = Popen(['ceph', 'mon', 'dump', str(mon_epoch), '-f', 'json-pretty'], stdout=PIPE)
        monmap = monmap.stdout.read().decode('ascii')
        monmap_json = json.loads(monmap)

        ctime = datetime.datetime.strptime(monmap_json['created'], '%Y-%m-%d %H:%M:%S.%f')
        mtime = datetime.datetime.strptime(monmap_json['modified'], '%Y-%m-%d %H:%M:%S.%f')

        monmap_data = dict(
            fsid = monmap_json['fsid'],
            epoch = monmap_json['epoch'],
            created = monmap_json['created'],
            modified = monmap_json['modified'],
            mons_amount = monmap_json['mons'].__len__(),
        )

        with open(DIR_MAP_MON + '/epoch_' + str(mon_epoch).rjust(INT_LENGTH, '0') + '.json', 'w+') as mon_file:
            mon_file.write(monmap)

        table_mon_map.insert(monmap_data)
        mon_epoch -= 1 



    # OSD: check current epoch 

    osdmap = Popen(['ceph', 'osd', 'dump', '-f', 'json-pretty'], stdout=PIPE)
    osdmap = osdmap.stdout.read().decode('ascii')
    osdmap = json.loads(osdmap)
    osd_epoch = osdmap['epoch']

    while ( osd_epoch > 0 ):

        osdmap = Popen(['ceph', 'osd', 'dump', str(osd_epoch), '-f', 'json-pretty'], stdout=PIPE)
        osdmap = osdmap.stdout.read().decode('ascii')
        osdmap_json = json.loads(osdmap)

        ctime = datetime.datetime.strptime(osdmap_json['created'], '%Y-%m-%d %H:%M:%S.%f')
        mtime = datetime.datetime.strptime(osdmap_json['modified'], '%Y-%m-%d %H:%M:%S.%f')

        osdmap_data = dict(
            fsid = osdmap_json['fsid'],
            epoch = osdmap_json['epoch'],
            created = osdmap_json['created'],
            modified = osdmap_json['modified'],
            flags = osdmap_json['flags'],
            osds_amount = osdmap_json['osds'].__len__(),
            pool_amount = osdmap_json['pools'].__len__()
        )

        with open(DIR_MAP_OSD + '/epoch_' + str(osd_epoch).rjust(INT_LENGTH, '0') + '.json', 'w+') as osd_file:
            osd_file.write(osdmap)

        table_osd_map.insert(osdmap_data)
        osd_epoch -= 1 


    # PG: check current epoch 

    pgmap = Popen(['ceph', 'pg', 'dump', '-f', 'json-pretty'], stdout=PIPE)
    pgmap = pgmap.stdout.read().decode('ascii')
    pgmap_json = json.loads(pgmap)
    pgmap_epoch = pgmap_json['version']

    with open(DIR_MAP_PG + '/epoch_' + str(pgmap_epoch) + '.json', 'w+') as pg_file:
        pg_file.write(pgmap)  


    for element in pgmap_json['pg_stats']:
        pgid = element['pgid']
        print(pgid)

        pgquery = Popen(['ceph', 'pg', str(pgid), 'query', '-f', 'json-pretty'], stdout=PIPE)
        print(pgquery)

        pgquery = pgquery.stdout.read().decode('ascii')
        print(pgquery)

        with open(DIR_MAP_PG + '/pg_query_' + str(pgid) + '.json', 'w+') as pgquery_file:
            pgquery_file.write(pgquery)


    exit()

    ## Initiate new cluster and rbd instance and connect ##

    cluster = rados.Rados(conffile = CONF_FILE, conf = dict (keyring = KEYRING_FILE))
    rbd_inst = rbd.RBD()

    cluster.connect()


    ## Cluster: list properties and save statistics ##

    cluster_stats = cluster.get_cluster_stats()
    cluster_data = {
        'rados_id': cluster.rados_id, 
        # 'fsid': print(cluster.get_fsid()),
        'fsid': "Not implemented yet",
        'inconsistent_pgs': "Not implemented yet",
        'stats_kb': cluster_stats['kb'],
        'stats_kb_used': cluster_stats['kb_used'],
        'stats_kb_avail': cluster_stats['kb_avail'], 
        'stats_num_objects': cluster_stats['num_objects'], 
        'version': print(cluster.version()),
        'state': cluster.state
    }
    
    for key, value in cluster_data.items(): 
        table_ceph_cluster.insert(dict(Key=key, Value=value))


    ## Pools: list and save statistics ## 



    listpool = cluster.list_pools()


    for pool_name in listpool:

        # if pool_name != 'libvirt-pool':
        #    continue 


        ## Open Input/Output context on pool name ## 

        ioctx = cluster.open_ioctx(pool_name)
        pool_stats = ioctx.get_stats()

        
        # table_ceph_pools.insert(pool_data)

        

        ## RBD: List RADOS block devices ##

        listrbd = rbd_inst.list(ioctx)
        list_images = []
        list_image_id = []

        if listrbd.__len__() > 0: 
            
            for rbdname in listrbd:
                
                image = rbd.Image(ioctx, rbdname, read_only=True)
                image_id = image.id()
                image_stats = image.stat()
                
                try:
                    parent_id = image.parent_id()
                except:
                    parent_id = None 
                
                
                image_data = dict(
                    pool = pool_name,
                    image_name = rbdname, 
                    image_id = image_id,
                    image_stripe_count = image.stripe_count(),
                    image_block_name_prefix = image_stats['block_name_prefix'],
                    num_objs = image_stats['num_objs'],
                    obj_size = image_stats['obj_size'],
                    order = image_stats['order'],
                    parent_id = parent_id,
                    parent_name = image_stats['parent_name'],
                    parent_pool = str(image_stats['parent_pool']),
                    size = image_stats['size'],
                )


                ## Snapshot stuff

                snaplist = image.list_snaps()

                for snapshot in snaplist.__iter__():

                    snapshot_ctime = image.get_snap_timestamp(snapshot['id'])

                    snapshot_data = dict(
                        pool = pool_name,
                        image_id = image_id, 
                        image_name = rbdname,
                        snapshot_id = snapshot['id'],
                        size = snapshot['size'],
                        name = snapshot['name'],
                        ctime = snapshot_ctime.timestamp()
                    )

                    table_snapshots.insert(snapshot_data)


                list_images.append(image_data)
                list_image_id.append(image_id)
                table_rbd_images.insert(image_data)
                

            logging.debug(pp.pprint(list_images))
            
        
        ## Object: list and export ## 

        listobjects = ioctx.list_objects()

        for object in listobjects:


            ## Get object statistics and parse timestamp 

            object_stats = object.stat()
            mtime = object_stats[1]
            object_mtime = datetime.datetime(
                mtime.tm_year,
                mtime.tm_mon, 
                mtime.tm_mday,
                mtime.tm_hour, 
                mtime.tm_min, 
                mtime.tm_sec,
            )

            
            ## Xattrs: list and jsonify x-attributes ## 

            xattrlist = object.get_xattrs()
            object_xattributes = [(str(key), str(value)) for (key, value) in xattrlist]
            object_xattributes = json.dumps(object_xattributes)

            object_data = dict(
                pool_name = pool_name,
                key = object.key,
                namespace = object.nspace,
                size = object_stats[0],
                mtime = object_mtime.timestamp(),
                mtime_weekday = mtime.tm_wday,
                mtime_yearday = mtime.tm_yday,
                mtime_is_dst = mtime.tm_isdst,
                offset = object.offset,
                state = object.state,
                xattr = object_xattributes,
            )


            ## Parse additional RBD data

            if object.key[:3] == 'rbd':
                splitted_key = object.key.split('.')

                # splitted_key[0]   rbd_object_map, rbd_info, rbd_header, rbd_data
                # splitted_key[1]   rbd id 
                # splitted_key[2]   rbd offset 

                # if splitted_key[1] in list_image_id:
                #     print(splitted_key[1])

                try: splitted_key[0]
                except IndexError: splitted_key.append(None)

                try: splitted_key[1]
                except IndexError: splitted_key.append(None)

                try: splitted_key[2]
                except IndexError: splitted_key.append(None)

                object_data['rbd'] = True
                object_data['rbd_type'] = splitted_key[0]
                object_data['rbd_id'] = splitted_key[1]
                object_data['rbd_offset'] = splitted_key[2]




            table_ceph_objects.insert(object_data)
        

if __name__ == "__main__":
    main()




