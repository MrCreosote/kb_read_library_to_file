import unittest
import os
import time

from os import environ
from ConfigParser import ConfigParser
from pprint import pprint

from biokbase.workspace.client import Workspace as workspaceService  # @UnresolvedImport @IgnorePep8
from kb_read_library_to_file.kb_read_library_to_fileImpl import kb_read_library_to_file  # @IgnorePep8
from biokbase.AbstractHandle.Client import AbstractHandle as HandleService  # @UnresolvedImport @IgnorePep8
from kb_read_library_to_file.kb_read_library_to_fileImpl import ShockError
from biokbase.workspace.client import ServerError as WorkspaceError  # @UnresolvedImport @IgnorePep8
import shutil
import requests
import inspect
import hashlib
import subprocess


class TestError(Exception):
    pass


class kb_read_library_to_fileTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.token = environ.get('KB_AUTH_TOKEN', None)
        cls.ctx = {'token': cls.token,
                   'authenticated': 1
                   }
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_read_library_to_file'):
            cls.cfg[nameval[0]] = nameval[1]
        cls.wsURL = cls.cfg['workspace-url']
        cls.shockURL = cls.cfg['shock-url']
        cls.hs = HandleService(url=cls.cfg['handle-service-url'],
                               token=cls.token)
        cls.wsClient = workspaceService(cls.wsURL, token=cls.token)
        wssuffix = int(time.time() * 1000)
        wsName = "test_gaprice_SPAdes_" + str(wssuffix)
        cls.wsinfo = cls.wsClient.create_workspace({'workspace': wsName})
        print('created workspace ' + cls.getWsName())
        cls.serviceImpl = kb_read_library_to_file(cls.cfg)
        cls.staged = {}
        cls.nodes_to_delete = []
        cls.handles_to_delete = []
        cls.setupTestData()
        print('\n\n=============== Starting tests ==================')

    @classmethod
    def tearDownClass(cls):

        print('\n\n=============== Cleaning up ==================')

        if hasattr(cls, 'wsinfo'):
            cls.wsClient.delete_workspace({'workspace': cls.getWsName()})
            print('Test workspace was deleted: ' + cls.getWsName())
        if hasattr(cls, 'nodes_to_delete'):
            for node in cls.nodes_to_delete:
                cls.delete_shock_node(node)
        if hasattr(cls, 'handles_to_delete'):
            cls.hs.delete_handles(cls.hs.ids_to_handles(cls.handles_to_delete))
            print('Deleted handles ' + str(cls.handles_to_delete))

    @classmethod
    def getWsName(cls):
        return cls.wsinfo[1]

    def getImpl(self):
        return self.serviceImpl

    @classmethod
    def delete_shock_node(cls, node_id):
        header = {'Authorization': 'Oauth {0}'.format(cls.token)}
        requests.delete(cls.shockURL + '/node/' + node_id, headers=header,
                        allow_redirects=True)
        print('Deleted shock node ' + node_id)

    # Helper script borrowed from the transform service, logger removed
    @classmethod
    def upload_file_to_shock(cls, file_path):
        """
        Use HTTP multi-part POST to save a file to a SHOCK instance.
        """

        header = dict()
        header["Authorization"] = "Oauth {0}".format(cls.token)

        if file_path is None:
            raise Exception("No file given for upload to SHOCK!")

        with open(os.path.abspath(file_path), 'rb') as dataFile:
            files = {'upload': dataFile}
            print('POSTing data')
            response = requests.post(
                cls.shockURL + '/node', headers=header, files=files,
                stream=True, allow_redirects=True)
            print('got response')

        if not response.ok:
            response.raise_for_status()

        result = response.json()

        if result['error']:
            raise Exception(result['error'][0])
        else:
            return result["data"]

    @classmethod
    def upload_file_to_shock_and_get_handle(cls, test_file):
        '''
        Uploads the file in test_file to shock and returns the node and a
        handle to the node.
        '''
        print('loading file to shock: ' + test_file)
        node = cls.upload_file_to_shock(test_file)
        pprint(node)
        cls.nodes_to_delete.append(node['id'])

        print('creating handle for shock id ' + node['id'])
        handle_id = cls.hs.persist_handle({'id': node['id'],
                                           'type': 'shock',
                                           'url': cls.shockURL
                                           })
        cls.handles_to_delete.append(handle_id)

        md5 = node['file']['checksum']['md5']
        return node['id'], handle_id, md5, node['file']['size']

    @classmethod
    def upload_assembly(cls, wsobjname, object_body, fwd_reads,
                        rev_reads=None, kbase_assy=False, single_end=False):
        if single_end and rev_reads:
            raise ValueError('u r supr dum')

        print('\n===============staging data for object ' + wsobjname +
              '================')
        print('uploading forward reads file ' + fwd_reads['file'])
        fwd_id, fwd_handle_id, fwd_md5, fwd_size = \
            cls.upload_file_to_shock_and_get_handle(fwd_reads['file'])
        fwd_handle = {
                      'hid': fwd_handle_id,
                      'file_name': fwd_reads['name'],
                      'id': fwd_id,
                      'url': cls.shockURL,
                      'type': 'shock',
                      'remote_md5': fwd_md5
                      }

        ob = dict(object_body)  # copy
        ob['sequencing_tech'] = 'fake data'
        if kbase_assy:
            if single_end:
                wstype = 'KBaseAssembly.SingleEndLibrary'
                ob['handle'] = fwd_handle
            else:
                wstype = 'KBaseAssembly.PairedEndLibrary'
                ob['handle_1'] = fwd_handle
        else:
            if single_end:
                wstype = 'KBaseFile.SingleEndLibrary'
                obkey = 'lib'
            else:
                wstype = 'KBaseFile.PairedEndLibrary'
                obkey = 'lib1'
            ob[obkey] = \
                {'file': fwd_handle,
                 'encoding': 'UTF8',
                 'type': fwd_reads['type'],
                 'size': fwd_size
                 }

        rev_id = None
        if rev_reads:
            print('uploading reverse reads file ' + rev_reads['file'])
            rev_id, rev_handle_id, rev_md5, rev_size = \
                cls.upload_file_to_shock_and_get_handle(rev_reads['file'])
            rev_handle = {
                          'hid': rev_handle_id,
                          'file_name': rev_reads['name'],
                          'id': rev_id,
                          'url': cls.shockURL,
                          'type': 'shock',
                          'remote_md5': rev_md5
                          }
            if kbase_assy:
                ob['handle_2'] = rev_handle
            else:
                ob['lib2'] = \
                    {'file': rev_handle,
                     'encoding': 'UTF8',
                     'type': rev_reads['type'],
                     'size': rev_size
                     }

        print('Saving object data')
        objdata = cls.wsClient.save_objects({
            'workspace': cls.getWsName(),
            'objects': [
                        {
                         'type': wstype,
                         'data': ob,
                         'name': wsobjname
                         }]
            })[0]
        print('Saved object: ')
        pprint(objdata)
        pprint(ob)
        cls.staged[wsobjname] = {'info': objdata,
                                 'ref': cls.make_ref(objdata),
                                 'fwd_node_id': fwd_id,
                                 'rev_node_id': rev_id
                                 }

    @classmethod
    def upload_empty_data(cls):
        cls.wsClient.save_objects({
            'workspace': cls.getWsName(),
            'objects': [{'type': 'Empty.AType',
                         'data': {},
                         'name': 'empty'
                         }]
            })

    @classmethod
    def setupTestData(cls):
        print('Shock url ' + cls.shockURL)
        print('WS url ' + cls.wsClient.url)
        print('Handle service url ' + cls.hs.url)
        print('staging data')
        # get file type from type
        fwd_reads = {'file': 'data/small.forward.fq',
                     'name': 'test_fwd.fastq',
                     'type': 'fastq'}
        # get file type from handle file name
        rev_reads = {'file': 'data/small.reverse.fq',
                     'name': 'test_rev.FQ',
                     'type': ''}
        # get file type from shock node file name
        int_reads = {'file': 'data/interleaved.fq',
                     'name': '',
                     'type': ''}
        cls.upload_assembly('frbasic', {}, fwd_reads, rev_reads=rev_reads)
        cls.upload_assembly('intbasic', {'single_genome': 1}, int_reads)
        cls.upload_assembly('meta', {'single_genome': 0}, int_reads)
        cls.upload_assembly('reads_out', {'read_orientation_outward': 1},
                            int_reads)
        cls.upload_assembly('frbasic_kbassy', {}, fwd_reads,
                            rev_reads=rev_reads, kbase_assy=True)
        cls.upload_assembly('intbasic_kbassy', {}, int_reads, kbase_assy=True)
        cls.upload_assembly('single_end', {}, fwd_reads, single_end=True)
        shutil.copy2('data/small.forward.fq', 'data/small.forward.bad')
        bad_fn_reads = {'file': 'data/small.forward.bad',
                        'name': '',
                        'type': ''}
        cls.upload_assembly('bad_shk_name', {}, bad_fn_reads)
        bad_fn_reads['file'] = 'data/small.forward.fq'
        bad_fn_reads['name'] = 'file.terrible'
        cls.upload_assembly('bad_file_name', {}, bad_fn_reads)
        bad_fn_reads['name'] = 'small.forward.fastq'
        bad_fn_reads['type'] = 'xls'
        cls.upload_assembly('bad_file_type', {}, bad_fn_reads)
        cls.upload_assembly('bad_node', {}, fwd_reads)
        cls.delete_shock_node(cls.nodes_to_delete.pop())
        cls.upload_empty_data()
        print('Data staged.')

    @classmethod
    def make_ref(cls, object_info):
        return str(object_info[6]) + '/' + str(object_info[0]) + \
            '/' + str(object_info[4])

    def md5(self, filename):
        with open(filename, 'rb') as file_:
            hash_md5 = hashlib.md5()
            buf = file_.read(65536)
            while len(buf) > 0:
                hash_md5.update(buf)
                buf = file_.read(65536)
            return hash_md5.hexdigest()

    def dictmerge(self, x, y):
        z = x.copy()
        z.update(y)
        return z

    # MD5s not repeatable if the same file is gzipped again
    MD5_SM_F = 'e7dcea3e40d73ca0f71d11b044f30ded'
    MD5_SM_R = '2cf41e49cd6b9fdcf1e511b083bb42b5'
    MD5_SM_I = '6271cd02987c9d1c4bdc1733878fe9cf'
    MD5_FR_TO_I = '1c58d7d59c656db39cedcb431376514b'
    MD5_I_TO_F = '4a5f4c05aae26dcb288c0faec6583946'
    MD5_I_TO_R = '2be8de9afa4bcd1f437f35891363800a'

    STD_OBJ = {'gc_content': None,
               'insert_size_mean': None,
               'insert_size_std_dev': None,
               'read_count': None,
               'read_orientation_outward': 'false',
               'read_size': None,
               'sequencing_tech': u'fake data',
               'single_genome': 'true',
               'source': None,
               'strain': None
               }

    def test_basic(self):
        self.run_success(
            {'frbasic': {
                'md5': {'fwd': self.MD5_SM_F, 'rev': self.MD5_SM_R},
                'gzp': {'fwd': False, 'rev': False},
                'obj': self.dictmerge(self.STD_OBJ,
                    {'files': {'fwd_gz': 'false',
                               'rev_gz': 'false'
                               },
                     'ref': self.staged['frbasic']['ref']
                     })
                }
             }
        )

    def test_interleaved(self):
        self.run_success(
            {'intbasic': {
                'md5': {'int': self.MD5_SM_I},
                'gzp': {'int': False},
                'obj': self.dictmerge(self.STD_OBJ,
                    {'files': {'int_gz': 'false',
                               },
                     'ref': self.staged['intbasic']['ref']
                     })
                }
             }
        )

    def test_multiple(self):
        self.run_success(
            {'frbasic': {
                'md5': {'fwd': self.MD5_SM_F, 'rev': self.MD5_SM_R},
                'gzp': {'fwd': False, 'rev': False},
                'obj': self.dictmerge(self.STD_OBJ,
                    {'files': {'fwd_gz': 'false',
                               'rev_gz': 'false'
                               },
                     'ref': self.staged['frbasic']['ref']
                     })
                },
             'intbasic': {
                'md5': {'int': self.MD5_SM_I},
                'gzp': {'int': False},
                'obj': self.dictmerge(self.STD_OBJ,
                    {'files': {'int_gz': 'false',
                               },
                     'ref': self.staged['intbasic']['ref']
                     })
                }
             }
        )

    def test_gzip(self):
        self.run_success(
            {'frbasic': {
                'md5': {'fwd': self.MD5_SM_F, 'rev': self.MD5_SM_R},
                'gzp': {'fwd': True, 'rev': True},
                'obj': self.dictmerge(self.STD_OBJ,
                    {'files': {'fwd_gz': 'true',
                               'rev_gz': 'true'
                               },
                     'ref': self.staged['frbasic']['ref']
                     })
                }
             }, gzip='true', interleave='none'
        )

    def test_fr_to_interleave(self):
        self.run_success(
            {'frbasic': {
                'md5': {'int': self.MD5_FR_TO_I},
                'gzp': {'int': False},
                'obj': self.dictmerge(self.STD_OBJ,
                    {'files': {'int_gz': 'false',
                               },
                     'ref': self.staged['frbasic']['ref']
                     })
                }
             }, interleave='true'
        )

    def test_deinterleave(self):
        self.run_success(
            {'intbasic': {
                'md5': {'fwd': self.MD5_I_TO_F, 'rev': self.MD5_I_TO_R},
                'gzp': {'fwd': False, 'rev': False},
                'obj': self.dictmerge(self.STD_OBJ,
                    {'files': {'fwd_gz': 'false',
                               'rev_gz': 'false'
                               },
                     'ref': self.staged['intbasic']['ref']
                     })
                }
             }, interleave='false'
        )

    def test_deinterleave_and_gzip(self):
        self.run_success(
            {'intbasic': {
                'md5': {'fwd': self.MD5_I_TO_F, 'rev': self.MD5_I_TO_R},
                'gzp': {'fwd': True, 'rev': True},
                'obj': self.dictmerge(self.STD_OBJ,
                    {'files': {'fwd_gz': 'true',
                               'rev_gz': 'true'
                               },
                     'ref': self.staged['intbasic']['ref']
                     })
                }
             }, interleave='false', gzip='true'
        )

    def run_success(self, testspecs, gzip=None, interleave=None):
        test_name = inspect.stack()[1][3]
        print('\n==== starting expected success test: ' + test_name + ' ===\n')

        params = {'workspace_name': self.getWsName(),
                  'read_libraries': [f for f in testspecs]
                  }
        if gzip != 'none':
            params['gzip'] = gzip
        if interleave != 'none':
            params['interleaved'] = interleave

        print('Running test with params:')
        pprint(params)

        ret = self.getImpl().convert_read_library_to_file(self.ctx, params)[0]
        print('converter returned:')
        pprint(ret)
        retmap = ret['files']
        self.assertEqual(len(retmap), len(testspecs))
        for f in testspecs:
            for dirc in testspecs[f]['md5']:
                gz = testspecs[f]['gzp'][dirc]
                expectedmd5 = testspecs[f]['md5'][dirc]
                file_ = retmap[f]['files'][dirc]
                if gz:
                    if not file_.endswith('.' + dirc + '.fastq.gz'):
                        raise TestError(
                            'Expected file {} to end with .{}.fastq.gz'
                            .format(file_, dirc))
                    if subprocess.call(['gunzip', '-f', file_]):
                        raise TestError(
                            'Error unzipping file {}'.format(file_))
                    file_ = file_[: -3]
                elif not file_.endswith('.' + dirc + '.fastq'):
                    raise TestError('Expected file {} to end with .{}.fastq'
                                    .format(file_, dirc))
                self.assertEqual(expectedmd5, self.md5(file_))
                del retmap[f]['files'][dirc]
            self.assertDictEqual(testspecs[f]['obj'], retmap[f])
