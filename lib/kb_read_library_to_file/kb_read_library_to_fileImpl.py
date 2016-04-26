#BEGIN_HEADER
# The header block is where all import statements should live
import os
import re
import json
import requests
from pprint import pformat
from biokbase.workspace.client import Workspace as workspaceService  # @UnresolvedImport @IgnorePep8


class ShockException(Exception):
    pass
#END_HEADER


class kb_read_library_to_file:
    '''
    Module Name:
    kb_read_library_to_file

    Module Description:
    A KBase module: kb_read_library_to_file

Takes KBaseFile/KBaseAssembly PairedEndLibrary/SingleEndLibrary reads library
workspace object IDs as input and produces a FASTQ files along with file
metadata.
    '''

    ######## WARNING FOR GEVENT USERS #######
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    #########################################
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/mrcreosote/kb_read_library_to_file"
    GIT_COMMIT_HASH = "b17a11c191200ea9a3be4e3def68496530978d78"

    #BEGIN_CLASS_HEADER
    # Class variables and functions can be defined in this block
    SINGLE_END_TYPE = 'SingleEndLibrary'
    PAIRED_END_TYPE = 'PairedEndLibrary'
    # one of these should be deprecated
    MODULE_NAMES = ['KBaseAssembly', 'KBaseFile']

    PARAM_IN_WS = 'workspace_name'
    PARAM_IN_LIB = 'read_libraries'
    PARAM_IN_GZIP = 'gzip'
    PARAM_IN_INTERLEAVED = 'interleaved'

    INVALID_WS_OBJ_NAME_RE = re.compile('[^\\w\\|._-]')
    INVALID_WS_NAME_RE = re.compile('[^\\w:._-]')

    URL_WS = 'workspace-url'
    URL_SHOCK = 'shock-url'

    SUPPORTED_FILES = ['.fq',
                       '.fastq',
                       # '.bam',
                       # '.fa',
                       # '.fasta',
                       '.fq.gz',
                       '.fastq.gz',
                       # '.bam.gz',
                       # '.fa.gz',
                       # '.fasta.gz'
                       ]

    def log(self, message):
        print(message)

    def file_extension_ok(self, filename):
        # print('Checking extension for file name ' + filename)
        for ext in self.SUPPORTED_FILES:
            if filename.lower().endswith(ext):
                return True
        return False

    def check_shock_response(self, response, errtxt):
        if not response.ok:
            try:
                err = json.loads(response.content)['error'][0]
            except:
                # this means shock is down or not responding.
                self.log("Couldn't parse response error content from Shock: " +
                         response.content)
                response.raise_for_status()
            raise ShockException(errtxt + str(err))

    def shock_download(self, source_obj_ref, source_obj_name, token, handle,
                       file_type):
        self.log('Downloading from shock via handle:')
        self.log(pformat(handle))
        file_name = handle['id']

        headers = {'Authorization': 'OAuth ' + token}
        node_url = handle['url'] + '/node/' + handle['id']
        r = requests.get(node_url, headers=headers)
        errtxt = ('Error downloading reads for object {} ({}) from shock ' +
                  'node {}: ').format(source_obj_ref, source_obj_name,
                                      handle['id'])
        self.check_shock_response(r, errtxt)

        node_fn = r.json()['data']['file']['name']

        handle_fn = handle['file_name'] if 'file_name' in handle else None

        print('File type: ' + str(file_type))
        print('Handle fn: ' + str(handle_fn))
        print('Shock fn: ' + str(node_fn))

        if file_type:
            if not file_type.startswith('.'):
                file_type = '.' + file_type
            file_name += file_type
            print('using file name via type: ' + file_name)
        elif handle_fn:
            file_name += '_' + handle_fn
            print('using file name from handle: ' + file_name)
        else:
            file_name += '_' + node_fn
            print('using file name from node: ' + file_name)

        if not self.file_extension_ok(file_name):
            raise ValueError(
                ('Reads object {} ({}) contains a reads file stored in ' +
                 'Shock node {} for which a valid filename could not ' +
                 'be determined. In order of precedence:\n' +
                 'File type is: {}\n' +
                 'Handle file name is: {}\n' +
                 'Shock file name is: {}\n' +
                 'Acceptable extensions: {}').format(
                    source_obj_ref, source_obj_name, handle['id'], file_type,
                    handle_fn, node_fn, ' '.join(self.SUPPORTED_FILES)))

        file_path = os.path.join(self.scratch, file_name)
        with open(file_path, 'w') as fhandle:
            self.log('downloading reads file: ' + str(file_path))
            r = requests.get(node_url + '?download', stream=True,
                             headers=headers)
            self.check_shock_response(r, errtxt)
            for chunk in r.iter_content(1024):
                if not chunk:
                    break
                fhandle.write(chunk)
        self.log('done')
        return file_path

    def make_ref(self, object_info):
        return str(object_info[6]) + '/' + str(object_info[0]) + \
            '/' + str(object_info[4])

    def check_reads(self, params, reads):
        data = reads['data']
        info = reads['info']
        obj_ref = self.make_ref(info)
        obj_name = info[1]

        # Might need to do version checking here.
        module_name, type_name = info[2].split('-')[0].split('.')
        if (module_name not in self.MODULE_NAMES or
                type_name != self.PAIRED_END_TYPE):
            raise ValueError(
                'Only the types ' +
                self.MODULE_NAMES[0] + '.' + self.PAIRED_END_TYPE + ' and ' +
                self.MODULE_NAMES[1] + '.' + self.PAIRED_END_TYPE +
                ' are supported')

    def process_reads(self, reads, params, token):
        data = reads['data']
        info = reads['info']
        # Object Info Contents
        # 0 - obj_id objid
        # 1 - obj_name name
        # 2 - type_string type
        # 3 - timestamp save_date
        # 4 - int version
        # 5 - username saved_by
        # 6 - ws_id wsid
        # 7 - ws_name workspace
        # 8 - string chsum
        # 9 - int size
        # 10 - usermeta meta

        ret = {}
        obj_ref = self.make_ref(info)
        ret['in_lib_ref'] = obj_ref
        obj_name = info[1]

        self.check_reads(params, reads)
        # lib1 = KBaseFile, handle_1 = KBaseAssembly
        fwd_type = None
        rev_type = None
        if 'lib1' in data:
            forward_reads = data['lib1']['file']
            fwd_type = data['lib1']['type']
        elif 'handle_1' in data:
            forward_reads = data['handle_1']
        if 'lib2' in data:
            reverse_reads = data['lib2']['file']
            rev_type = data['lib1']['type']
        elif 'handle_2' in data:
            reverse_reads = data['handle_2']
        else:
            reverse_reads = False

        ret['fwd_file'] = self.shock_download(
            obj_ref, obj_name, token, forward_reads, fwd_type)
        ret['rev_file'] = None
        if (reverse_reads):
            ret['rev_file'] = self.shock_download(
                obj_ref, obj_name, token, reverse_reads, rev_type)
        return ret

    def process_boolean(self, params, boolname):
        if boolname not in params or params[boolname] == 'false':
            params[boolname] = False
        elif params[boolname] == 'true':
            params[boolname] = True
        else:
            raise ValueError('Illegal value for boolean parameter {}: {}'
                             .format(boolname, params[boolname]))

    def process_params(self, params):
        if (self.PARAM_IN_WS not in params or not params[self.PARAM_IN_WS]):
            raise ValueError(self.PARAM_IN_WS + ' parameter is required')
        if self.INVALID_WS_NAME_RE.search(params[self.PARAM_IN_WS]):
            raise ValueError('Invalid workspace name ' +
                             params[self.PARAM_IN_WS])
        if self.PARAM_IN_LIB not in params:
            raise ValueError(self.PARAM_IN_LIB + ' parameter is required')
        reads = params[self.PARAM_IN_LIB]
        if type(reads) != dict:
            raise ValueError(self.PARAM_IN_LIB + ' must be a map')
        if not reads:
            raise ValueError('At least one reads library must be provided')
        fileprefixes = set()
        for read_name in reads:
            if not read_name or self.INVALID_WS_OBJ_NAME_RE.search(read_name):
                raise ValueError('Invalid workspace object name ' + read_name)
            if not reads[read_name]:
                raise ValueError('No file prefix provided for read library ' +
                                 read_name)
            if reads[read_name] in fileprefixes:
                raise ValueError('File prefix specified twice: ' +
                                 reads[read_name])
                fileprefixes.add(reads[read_name])
        self.process_boolean(params, self.PARAM_IN_GZIP)
        self.procces_boolean(params, self.PARAM_IN_INTERLEAVED)

    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.workspaceURL = config[self.URL_WS]
        self.shockURL = config[self.URL_SHOCK]
        self.scratch = os.path.abspath(config['scratch'])
        if not os.path.exists(self.scratch):
            os.makedirs(self.scratch)
        #END_CONSTRUCTOR
        pass

    def convert_read_library_to_file(self, ctx, params):
        # ctx is the context object
        # return variables are: output
        #BEGIN convert_read_library_to_file
        ''' potential improvements:
            Add continue_on_failure mode that reports errors for each failed
                conversion rather than failing completely. This would need
                a similar boolean to ignore failures in the workspace
                get_objects method, or it'd require getting the reads objects
                one by one. Yuck.
                Alternatively - call get_object_info_new and then only process
                the reads files that return. Race conditions possible though.
                Probably better to add flag to get_objects.
            Parallelize - probably not worth it, this is all IO bound. Try if
                there's nothing better to do.
        '''

        # TODO tests - run through all logic
        self.log('Running convert_read_library_to_file with params:')
        self.log(pformat(params))

        token = ctx['token']

        self.process_params(params)

        # Get the reads library
        ws = workspaceService(self.workspaceURL, token=token)
        ws_reads_ids = []
        for read_name in params[self.PARAM_IN_LIB]:
            ws_reads_ids.append({'ref': params[self.PARAM_IN_WS] + '/' +
                                 read_name})
        reads = ws.get_objects(ws_reads_ids)

        output = {}
        for read_name, read in zip(params[self.PARAM_IN_LIB], reads):
            output[read_name] = self.process_reads(read, params, token)
        #END convert_read_library_to_file

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method convert_read_library_to_file return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': 'OK',
                     'message': '',
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        ctx['token']  # shut up pep8
        #END_STATUS
        return [returnVal]
