"""Youku cloud Python Client

doc: http://cloud.youku.com/docs/doc?id=110
"""

import os
import requests
import json
import hashlib
import logging
import oss2
import time

from util import check_error, YoukuError


class YoukuUpload(object):

    """Youku Upload Client.

    Upload video file to Youku Video Cloud. Support resume upload if interrupted.
    Should use one instance of YoukuUpload for one upload file in one thread,
    since it has internal state of upload process.

    oss2: pip install oss2

    doc: http://cloud.youku.com/docs/doc?id=110
    """

    def __init__(self, client_id, access_token, file, logger=None):
        """
        Args:
            file: string, include path and filename for open(). filename
                must contain video file extension.
        """
        super(YoukuUpload, self).__init__()
        self.client_id = client_id
        self.access_token = access_token
        self.logger = logger or logging.getLogger(__name__)

        # file info
        self.file = file
        self.file_size = os.path.getsize(self.file)  # int
        self.file_dir, self.file_name = os.path.split(self.file)  # string
        if self.file_dir == '':
            self.file_dir = '.'
        self.file_ext = self.file_name.rsplit('.', 1)[1],  # file extension
        self.file_md5 = None  # string, do later

        # upload state
        self.upload_token = None  # string
        # oss params
        self.endpoint = None
        self.security_token = None
        self.oss_bucket = None
        self.oss_object = None
        self.temp_access_id = None
        self.temp_access_secret = None
        self.expire_time = None

        # resume upload state
        self._read_upload_state_from_file()

    def prepare_video_params(self, title=None, tags='Others', description='',
                             copyright_type='original', public_type='all',
                             category=None, watch_password=None,
                             latitude=None, longitude=None, shoot_time=None
                             ):
        """ util method for create video params to upload.

        Only need to provide a minimum of two essential parameters:
        title and tags, other video params are optional. All params spec
        see: http://cloud.youku.com/docs?id=110#create .

        Args:
            title: string, 2-50 characters.
            tags: string, 1-10 tags joind with comma.
            description: string, less than 2000 characters.
            copyright_type: string, 'original' or 'reproduced'
            public_type: string, 'all' or 'friend' or 'password'
            watch_password: string, if public_type is password.
            latitude: double.
            longitude: double.
            shoot_time: datetime.

        Returns:
            dict params that upload/create method need.
        """
        params = {}
        if title is None:
            title = self.file_name
        elif len(title) > 50:
            title = title[:50]
        params['title'] = title
        params['tags'] = tags
        params['description'] = description
        params['copyright_type'] = copyright_type
        params['public_type'] = public_type
        if category:
            params['category'] = category
        if watch_password:
            params['watch_password'] = watch_password
        if latitude:
            params['latitude'] = latitude
        if longitude:
            params['longitude'] = longitude
        if shoot_time:
            params['shoot_time'] = shoot_time

        return params

    def create(self, params):
        # prepare file info
        params['file_name'] = self.file_name
        params['file_size'] = self.file_size
        params['file_md5'] = self.file_md5 = self.checksum_md5file(self.file)
        self.logger.info('upload file %s, size: %d bytes' %
                         (self.file_name, self.file_size))
        self.logger.info('md5 of %s: %s' %
                         (self.file_name, self.file_md5))

        params['client_id'] = self.client_id
        params['access_token'] = self.access_token
        params['isnew'] = 1

        url = 'https://api.youku.com/uploads/create.json'
        r = requests.get(url, params=params)

        check_error(r, 201)
        result = r.json()

        self.upload_token = result['upload_token']
        self.logger.info('upload token of %s: %s' %
                         (self.file_name, self.upload_token))

        # init oss params
        self.endpoint = result['endpoint']
        self.security_token = result['security_token']
        self.oss_bucket = result['oss_bucket']
        self.oss_object = result['oss_object']
        self.temp_access_id = result['temp_access_id']
        self.temp_access_secret = result['temp_access_secret']
        self.expire_time = result['expire_time']
        
        self.logger.info('oss bucket{ endpoint:%s, oss_bucket:%s }' %
                         (self.endpoint, self.oss_bucket))

    def create_file(self):
        # save upload state to resume upload
        self._save_upload_state_to_file()

    def _save_upload_state_to_file(self):
        """if create and create_file has execute, save upload state
        to file for next resume upload if current upload process is
        interrupted.
        """
        if os.access(self.file_dir, os.W_OK | os.R_OK | os.X_OK):
            save_file = self.file + '.upload'
            data = {
                'upload_token': self.upload_token,
                'endpoint': self.endpoint,
                'security_token': self.security_token,
                'oss_bucket': self.oss_bucket,
                'oss_object': self.oss_object,
                'temp_access_id': self.temp_access_id,
                'temp_access_secret': self.temp_access_secret,
                'expire_time': self.expire_time
            }
            with open(save_file, 'w') as f:
                json.dump(data, f)

    def _read_upload_state_from_file(self):
        save_file = self.file + '.upload'
        try:
            with open(save_file) as f:
                data = json.load(f)
                # if data['expire_time'] check expired
                self.upload_token = data['upload_token']
                self.endpoint = data['endpoint']
                self.security_token = data['security_token']
                self.oss_bucket = data['oss_bucket']
                self.oss_object = data['oss_object']
                self.temp_access_id = data['temp_access_id']
                self.temp_access_secret = data['temp_access_secret']
                self.expire_time = data['expire_time']
        except:
            pass

    def _delete_upload_state_file(self):
        try:
            os.remove(self.file + '.upload')
        except:
            pass

    def _update_oss_bucket_info(self, result):
        self.endpoint = result['endpoint']
        self.security_token = result['security_token']
        self.temp_access_id = result['temp_access_id']
        self.temp_access_secret = result['temp_access_secret']
        self.expire_time = result['expire_time']

    def checksum_md5file(self, filename):
        md5 = hashlib.md5()
        with open(filename, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()

    def checksum_md5data(self, data):
        md5 = hashlib.md5()
        md5.update(data)
        return md5.hexdigest()

    def get_sts_info(self):
        params = {
            'upload_token': self.upload_token,
            'oss_bucket': self.oss_bucket,
            'oss_object': self.oss_object
        }
        params['client_id'] = self.client_id
        params['access_token'] = self.access_token
        print params
        url = 'https://api.youku.com/uploads/get_sts_inf.json'
        r = requests.get(url, params=params)
        print r
        check_error(r, 200)
        self._update_oss_bucket_info(r.json())

    def check(self): 
        d1 = time.strptime(self.expire_time, '%Y-%m-%dT%H:%M:%SZ')
        cur = time.localtime(time.time())
        if ( int(time.mktime(d1)) + 3600*8 < int(time.mktime(cur)) ):
            self.get_sts_info()

    def commit(self):
        # status = self.check()
        # if status['status'] == 4:
        #     raise ValueError('upload has not complete, should not commit')
        # while status['status'] != 1:  # status is 2 or 3
        #     time.sleep(10)
        #     status = self.check()

        params = {
            'access_token': self.access_token,
            'client_id': self.client_id,
            'upload_token': self.upload_token
        }
        url = 'https://api.youku.com/uploads/commit.json'
        r = requests.post(url, data=params)
        check_error(r, 200)
        self._delete_upload_state_file()
        return r.json()['video_id']

    def cancel(self):
        # status = self.check()
        params = {
            'access_token': self.access_token,
            'client_id': self.client_id,
            'upload_token': self.upload_token,
        }
        url = 'https://api.youku.com/uploads/cancel.json'
        r = requests.get(url, params=params)
        check_error(r, 200)
        self._delete_upload_state_file()
        return r.json()['upload_token']

    def spec(self):
        url = 'https://api.youku.com/schemas/upload/spec.json'
        r = requests.get(url)
        check_error(r, 200)
        return r.json()

    def upload(self, params={}):
        """start uploading the file until upload is complete or error.
           This is the main method to used, If you do not care about
           state of process.

           Args:
                params: a dict object describe video info, eg title,
                tags, description, category.
                all video params see the doc of prepare_video_params.

           Returns:
                return video_id if upload successfully
        """
        if self.upload_token is not None:
            # resume upload
            self.check()
        else:
            # new upload
            self.create(self.prepare_video_params(**params))
            self.create_file()

        # create Bucket object
        bucket = oss2.Bucket(oss2.StsAuth(self.temp_access_id, self.temp_access_secret, self.security_token), self.endpoint, self.oss_bucket)
        #  start upload
        result = oss2.resumable_upload(bucket, self.oss_object, self.file, multipart_threshold=100 * 1024)
        self.logger.info("Upload success, add rusult: {0}".format(result))
        if result.status == 200:
            self.commit()





