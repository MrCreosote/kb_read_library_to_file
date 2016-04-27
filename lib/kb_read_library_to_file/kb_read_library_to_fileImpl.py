#BEGIN_HEADER
# The header block is where all import statements should live
import os
import re
import json
import requests
import time
from pprint import pformat
from biokbase.workspace.client import Workspace as workspaceService  # @UnresolvedImport @IgnorePep8
from biokbase.workspace.client import ServerError as WorkspaceException  # @UnresolvedImport @IgnorePep8
import errno
import shutil
import gzip


class ShockError(Exception):
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

Operational notes:
- All reads files must be in fastq format, and thus provided types or filenames
  must have a case-insensitive .fq or .fastq suffix.
- Reads files are optionally gzipped, and as if so have a case-insensitive .gz
  suffix after the fastq suffix.
- The file type and suffixes are determined from, in order of precedence:
  - the lib?/type field in KBaseFile types
  - the lib?/file/filename or handle?/filename field
  - the shock filename
- If the file types / suffixes do not match the previous rules, the converter
  raises an error.
- If a file has a .gz suffix, it is assumed to be gzipped.
- Files are assumed to be in correct fastq format.
    '''

    ######## WARNING FOR GEVENT USERS #######
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    #########################################
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/mrcreosote/kb_read_library_to_file"
    GIT_COMMIT_HASH = "b322aa7bf1947921283dfa5134848006424a30ed"
    
    #BEGIN_CLASS_HEADER
    # Class variables and functions can be defined in this block
    SINGLE_END_TYPE = 'SingleEndLibrary'
    PAIRED_END_TYPE = 'PairedEndLibrary'
    # one of these should be deprecated
    KBASE_FILE = 'KBaseFile'
    KBASE_ASSEMBLY = 'KBaseAssembly'
    MODULE_NAMES = [KBASE_FILE, KBASE_ASSEMBLY]
    TYPE_NAMES = [SINGLE_END_TYPE, PAIRED_END_TYPE]

    PARAM_IN_WS = 'workspace_name'
    PARAM_IN_LIB = 'read_libraries'
    PARAM_IN_GZIP = 'gzip'
    PARAM_IN_INTERLEAVED = 'interleaved'

    GZIP = '.gz'

    TRUE = 'true'
    FALSE = 'false'
    UNKNOWN = 'unknown'

    INVALID_WS_OBJ_NAME_RE = re.compile('[^\\w\\|._-]')
    INVALID_WS_NAME_RE = re.compile('[^\\w:._-]')

    URL_WS = 'workspace-url'
    URL_SHOCK = 'shock-url'

    SUPPORTED_FILES = ['.fq',
                       '.fastq',
                       # '.bam',
                       # '.fa',
                       # '.fasta',
                       '.fq' + GZIP,
                       '.fastq' + GZIP,
                       # '.bam.gz',
                       # '.fa.gz',
                       # '.fasta.gz'
                       ]

    SHOCK_TEMP = 'shock_tmp'

    def log(self, message):
        print(message)

    def file_extension_ok(self, filename):
        # print('Checking extension for file name ' + filename)
        for ext in self.SUPPORTED_FILES:
            if filename.lower().endswith(ext):
                return True
        return False

    def check_shock_response(self, response):
        if not response.ok:
            try:
                err = json.loads(response.content)['error'][0]
            except:
                # this means shock is down or not responding.
                self.log("Couldn't parse response error content from Shock: " +
                         response.content)
                response.raise_for_status()
            raise ShockError(str(err))

    def shock_download(self, token, handle, file_type=None):
        # Could keep a record of files downloaded to prevent duplicate
        # downloads if 2 ws objects point to the same shock node, but that
        # seems rare enough that it's not worth the extra code complexity and
        # maintenance burden
        self.log('Downloading from shock via handle:')
        self.log(pformat(handle))
        file_name = handle['id']

        headers = {'Authorization': 'OAuth ' + token}
        node_url = handle['url'] + '/node/' + handle['id']
        r = requests.get(node_url, headers=headers)
        self.check_shock_response(r)

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
            raise ShockError(
                ('A valid filename could not be determined for the reads ' +
                 'file. In order of precedence:\n' +
                 'File type is: {}\n' +
                 'Handle file name is: {}\n' +
                 'Shock file name is: {}\n' +
                 'Acceptable extensions: {}').format(
                    file_type, handle_fn, node_fn,
                    ' '.join(self.SUPPORTED_FILES)))

        file_path = os.path.join(self.shock_temp, file_name)
        with open(file_path, 'w') as fhandle:
            self.log('downloading reads file: ' + str(file_path))
            r = requests.get(node_url + '?download', stream=True,
                             headers=headers)
            self.check_shock_response(r)
            for chunk in r.iter_content(1024):
                if not chunk:
                    break
                fhandle.write(chunk)
        self.log('done')
        return file_path, file_path.lower().endswith(self.GZIP)

    def make_ref(self, object_info):
        return str(object_info[6]) + '/' + str(object_info[0]) + \
            '/' + str(object_info[4])

    def check_reads(self, reads):
        info = reads['info']
        obj_ref = self.make_ref(info)
        obj_name = info[1]

        # Might need to do version checking here.
        module_name, type_name = info[2].split('-')[0].split('.')
        if (module_name not in self.MODULE_NAMES or
                type_name not in self.TYPE_NAMES):
            types = []
            for mod in self.MODULE_NAMES:
                for type_ in self.TYPE_NAMES:
                    types.append(mod + '.' + type_)
            raise ValueError(('Invalid type for object {} ({}). Supported ' +
                              'types: {}').format(obj_ref, obj_name,
                                                  ','.join(types)))
        return (type_name == self.SINGLE_END_TYPE,
                module_name == self.KBASE_FILE)

    def copy_field(self, source, field, target):
        if field in source:
            target[field] = source[field]
        else:
            target[field] = None

    # this assumes that the FASTQ file is properly formatted, which it should
    # be if it's in kbase. Credit:
    # https://www.biostars.org/p/19446/#117160
    def deinterleave(self, filepath, fwdpath, revpath):
        print('Deinterleaving file {} to files {} and {}'.format(
              filepath, fwdpath, revpath))
        with open(filepath, 'r') as s:
            with open(fwdpath, 'w') as f, open(revpath, 'w') as r:
                for i, line in enumerate(s):
                    if i % 8 < 4:
                        f.write(line)
                    else:
                        r.write(line)

    # this assumes that the FASTQ files are properly formatted and matched,
    # which they should be if they're in kbase. Credit:
    # https://sourceforge.net/p/denovoassembler/ray-testsuite/ci/master/tree/scripts/interleave-fastq.py
    def interleave(self, fwdpath, revpath, targetpath):
        print('Interleaving files {} and {} to {}'.format(
              fwdpath, revpath, targetpath))
        with open(targetpath, '2') as t:
            with open(fwdpath, 'r') as f, open(revpath, 'r') as r:
                while True:
                    line = f.readline()
                    # since FASTQ cannot contain blank lines
                    if not line or not line.strip():
                        break
                    t.write(line.strip())

                    for _ in xrange(3):
                        t.write(f.readline().strip())

                    for _ in xrange(4):
                        t.write(r.readline().strip())

    def set_up_reads_return(self, single, kbasefile, reads):
        data = reads['data']
        info = reads['info']

        ret = {}
        ret['ref'] = self.make_ref(info)

        sg = 'single_genome'
        if kbasefile:
            if sg not in data or data[sg]:
                ret[sg] = self.TRUE
            else:
                ret[sg] = self.FALSE
        else:
            ret[sg] = self.UNKNOWN

        roo = 'read_orientation_outward'
        if single:
            ret[roo] = self.FALSE
        elif roo in data:
            if data[roo]:
                ret[roo] = self.TRUE
            else:
                ret[roo] = self.FALSE
        else:
            if kbasefile:
                ret[roo] = self.FALSE
            else:
                ret[roo] = self.UNKNOWN

        # these fields are only possible in KBaseFile/Assy paired end, but the
        # logic is still fine for single end, will just force a null
        self.copy_field(data, 'insert_size_mean', ret)
        self.copy_field(data, 'insert_size_std_dev', ret)
        # these fields are in KBaseFile single end and paired end only
        self.copy_field(data, 'source', ret)
        self.copy_field(data, 'strain', ret)
        self.copy_field(data, 'sequencing_tech', ret)
        self.copy_field(data, 'read_count', ret)
        self.copy_field(data, 'read_size', ret)
        self.copy_field(data, 'gc_content', ret)

        return ret

    # there's got to be better way to do this than these processing methods.
    # make some input classes for starters to fix these gross method sigs

    def process_interleaved(self, source_obj_ref, source_obj_name, token,
                            handle, prefix, retobj, gzip, interleave,
                            file_type=None):
        try:
            shockfile, isgz = self.shock_download(token, handle, file_type)
        except ShockError, e:
            e.message = ('Error downloading reads for object {} ({}) from ' +
                         'shock node {}: {}').format(
                            source_obj_ref, source_obj_name, handle['id'],
                            e.message)
            raise

        if interleave is not False:  # e.g. True or None
            retobj['int'] = self.handle_gzip(shockfile, gzip, isgz,
                                             prefix + '.int.fasta')
        else:
            if isgz:
                # we expect the job runner to clean up for us
                shockfile = self.gunzip(shockfile)
            fwdpath = os.path.join(self.scratch, prefix + '.fwd.fasta')
            revpath = os.path.join(self.scratch, prefix + '.rev.fasta')
            self.deinterleave(shockfile, fwdpath, revpath)
            if gzip:
                fwdpath = self.gzip(fwdpath)
                revpath = self.gzip(revpath)
            retobj['fwd'] = fwdpath
            retobj['rev'] = revpath

    def process_paired(self, source_obj_ref, source_obj_name, token,
                       fwdhandle, revhandle, prefix, retobj, gzip, interleave,
                       fwd_file_type=None, rev_file_type=None):
        try:
            fwdshock, fwdisgz = self.shock_download(token, fwdhandle,
                                                    fwd_file_type)
        except ShockError, e:
            e.message = ('Error downloading reads for object {} ({}) from ' +
                         'shock node {}: {}').format(
                            source_obj_ref, source_obj_name, fwdhandle['id'],
                            e.message)
            raise
        try:
            revshock, revisgz = self.shock_download(token, revhandle,
                                                    rev_file_type)
        except ShockError, e:
            e.message = ('Error downloading reads for object {} ({}) from ' +
                         'shock node {}: {}').format(
                            source_obj_ref, source_obj_name, fwdhandle['id'],
                            e.message)
            raise
        if interleave:
            # we expect the job runner to clean up for us
            if fwdisgz:
                fwdshock = self.gunzip(fwdshock)
            if revisgz:
                revshock = self.gunzip(revshock)
            intpath = os.path.join(self.scratch, prefix + '.int.fasta')
            self.interleave(fwdshock, revshock, intpath)
            if gzip:
                intpath = self.gzip(intpath)
            retobj['int'] = intpath
        else:
            retobj['fwd'] = self.handle_gzip(fwdshock, gzip, fwdisgz,
                                             prefix + '.fwd.fasta')
            retobj['rev'] = self.handle_gzip(revshock, gzip, revisgz,
                                             prefix + '.rev.fasta')

    def process_single_end(self, source_obj_ref, source_obj_name, token,
                           handle, prefix, retobj, gzip, file_type=None):
        try:
            shockfile, isgz = self.shock_download(token, handle, file_type)
        except ShockError, e:
            e.message = ('Error downloading reads for object {} ({}) from ' +
                         'shock node {}: {}').format(
                            source_obj_ref, source_obj_name, handle['id'],
                            e.message)
            raise

        retobj['sing'] = self.handle_gzip(shockfile, gzip, isgz,
                                          prefix + '.sing.fasta')

    # there's almost certainly a better way to do this
    def handle_gzip(self, oldfile, shouldzip, iszip, prefix):
        if shouldzip:
            prefix += self.GZIP
            if iszip:
                self.mv(oldfile, os.path.join(self.scratch, prefix))
            else:
                self.gzip(oldfile, os.path.join(self.scratch, prefix))
        elif shouldzip is None:
            if iszip:
                prefix += self.GZIP
            self.mv(oldfile, os.path.join(self.scratch, prefix))
        else:
            if iszip:
                self.gunzip(oldfile, os.path.join(self.scratch, prefix))
            else:
                self.mv(oldfile, os.path.join(self.scratch, prefix))
        return prefix

    def mv(self, oldfile, newfile):
        shutil.move(oldfile, newfile)

    def gzip(self, oldfile, newfile=None):
        if oldfile.lower().endswith(self.GZIP):
            raise ValueError('File {} is already gzipped'.format(oldfile))
        if not newfile:
            newfile = oldfile + self.GZIP
        with open(oldfile, 'rb') as s, gzip.open(newfile, 'wb') as t:
            shutil.copyfileobj(s, t)
        return newfile

    def gunzip(self, oldfile, newfile=None):
        if not oldfile.lower().endswith(self.GZIP):
            raise ValueError('File {} is not gzipped'.format(oldfile))
        if not newfile:
            newfile = oldfile + self.GZIP
        with gzip.open(oldfile, 'rb') as s, open(newfile, 'wb') as t:
            shutil.copyfileobj(s, t)
        return newfile

    def process_reads(self, reads, file_prefix, gzip, interleave, token):
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

        single, kbasefile = self.check_reads(reads)
        ret = self.set_up_reads_return(single, kbasefile, reads)
        obj_name = info[1]
        ref = ret['ref']

        # lib1 = KBaseFile, handle_1 = KBaseAssembly
        if kbasefile:
            if single:
                reads = data['lib']['file']
                type_ = data['lib']['type']
                ret['sing'] = self.process_single_end(
                    ref, obj_name, token, reads, file_prefix, ret, gzip, type_)
            else:
                fwd_reads = data['lib1']['file']
                fwd_type = data['lib1']['type']
                if 'lib2' in data:  # not interleaved
                    rev_reads = data['lib2']['file']
                    rev_type = data['lib2']['type']
                    self.process_paired(
                        ref, obj_name, token, fwd_reads, rev_reads,
                        file_prefix, ret, gzip, interleave, fwd_type, rev_type)
                else:
                    self.process_interleaved(
                        ref, obj_name, token, fwd_reads, file_prefix, ret,
                        gzip, interleave, fwd_type)
        else:  # KBaseAssembly
            if single:
                ret['sing'] = self.process_single_end(
                    ref, obj_name, token, data['handle'], file_prefix, ret,
                    gzip)
            else:
                if 'handle2' in data:  # not interleaved
                    self.process_paired(
                        ref, obj_name, token, data['handle1'], data['handle2'],
                        file_prefix, ret, gzip, interleave)
                else:
                    self.process_interleaved(
                        ref, obj_name, token, data['handle1'], file_prefix,
                        ret, gzip, interleave)

        return ret

    def process_ternary(self, params, boolname):
        if boolname not in params or params[boolname] is None:
            params[boolname] = None
        elif params[boolname] == 'true':
            params[boolname] = True
        elif params[boolname] == 'false':
            params[boolname] = False
        else:
            raise ValueError('Illegal value for ternary parameter {}: {}'
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
            reads[read_name] = os.path.join(self.scratch, reads[read_name])
        self.process_ternary(params, self.PARAM_IN_GZIP)
        self.process_ternary(params, self.PARAM_IN_INTERLEAVED)

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.workspaceURL = config[self.URL_WS]
        self.shockURL = config[self.URL_SHOCK]
        self.scratch = os.path.abspath(config['scratch'])
        self.mkdir_p(self.scratch)
        self.shock_temp = os.path.join(self.scratch, self.SHOCK_TEMP)
        self.mkdir_p(self.shock_temp)
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
        try:
            reads = ws.get_objects(ws_reads_ids)
        except WorkspaceException, e:
            print('Logging stacktrace from workspace exception at epoch {}:'
                  .format(time.time()))
            print(e.data)
            raise

        output = {}
        for read_name, read in zip(params[self.PARAM_IN_LIB], reads):
            output[read_name] = self.process_reads(
                read, params[self.PARAM_IN_LIB][read_name],
                params[self.PARAM_IN_INTERLEAVED],
                params[self.PARAM_IN_GZIP], token)
        output = {'files': output}
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
