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
import uuid


class ShockError(Exception):
    pass


class InvalidFileError(Exception):
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
- The file type and suffixes for the reads files are determined from, in order
    of precedence:
  - the lib?/type field in KBaseFile types
  - the lib?/file/filename or handle?/filename field
  - the shock filename
- All reads files must be in fastq format, and thus the file suffix must have a
  case-insensitive .fq or .fastq suffix.
- Reads files are optionally gzipped, and if so must have a case-insensitive
  .gz suffix after the fastq suffix.
- If the file types / suffixes do not match the previous rules, the converter
  raises an error.
- If a file downloaded from Shock has a .gz suffix, it is assumed to be
  gzipped.
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
    GIT_COMMIT_HASH = "e50362f53b37497e099002c035883280f3387271"
    
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

    def log(self, message, prefix_newline=False):
        print(('\n' if prefix_newline else '') +
              str(time.time()) + ': ' + message)

    def file_extension_ok(self, filename):
        for okext in self.SUPPORTED_FILES:
            if filename.lower().endswith(okext):
                if okext.endswith(self.GZIP):
                    return okext, True
                return okext, False
        return None, None

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
        self.log('Downloading from shock via handle:\n' + pformat(handle))

        headers = {'Authorization': 'OAuth ' + token}
        node_url = handle['url'] + '/node/' + handle['id']
        r = requests.get(node_url, headers=headers)
        self.check_shock_response(r)

        node_fn = r.json()['data']['file']['name']

        handle_fn = handle['file_name'] if 'file_name' in handle else None

        if file_type:
            file_type = ('' if file_type.startswith('.') else '.') + file_type
        fileok = None
        for txt, fn in zip(['file type', 'handle filename', 'shock filename'],
                           [file_type, handle_fn, node_fn]):
            if fn:
                fileok, gzipped = self.file_extension_ok(fn)
                if fileok:
                    self.log(('Found acceptable file extension in {}: {}. ' +
                             'File {} gzipped.').format(
                        txt, fn, 'is' if gzipped else 'is not'))
                break
            else:
                self.log('File extension cannot be determined from {}: {}'
                         .format(txt, fn))
        if not fileok:
            raise InvalidFileError(
                ('A valid file extension could not be determined for the ' +
                 'reads file. In order of precedence:\n' +
                 'File type is: {}\n' +
                 'Handle file name is: {}\n' +
                 'Shock file name is: {}\n' +
                 'Acceptable extensions: {}').format(
                    file_type, handle_fn, node_fn,
                    ' '.join(self.SUPPORTED_FILES)))

        file_path = os.path.join(self.shock_temp, handle['id'] +
                                 (self.GZIP if gzipped else ''))
        with open(file_path, 'w') as fhandle:
            self.log('downloading reads file: ' + str(file_path))
            r = requests.get(node_url + '?download', stream=True,
                             headers=headers)
            self.check_shock_response(r)
            for chunk in r.iter_content(1024):
                if not chunk:
                    break
                fhandle.write(chunk)
        return file_path, gzipped

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
                                                  ' '.join(types)))
        return (type_name == self.SINGLE_END_TYPE,
                module_name == self.KBASE_FILE)

    def copy_field(self, source, field, target):
        target[field] = source.get(field)

    # this assumes that the FASTQ file is properly formatted, which it should
    # be if it's in KBase. Credit:
    # https://www.biostars.org/p/19446/#117160
    def deinterleave(self, filepath, fwdpath, revpath):
        self.log('Deinterleaving file {} to files {} and {}'.format(
            filepath, fwdpath, revpath))
        with open(filepath, 'r') as s:
            with open(fwdpath, 'w') as f, open(revpath, 'w') as r:
                for i, line in enumerate(s):
                    if i % 8 < 4:
                        f.write(line)
                    else:
                        r.write(line)

    # this assumes that the FASTQ files are properly formatted and matched,
    # which they should be if they're in KBase. Credit:
    # https://sourceforge.net/p/denovoassembler/ray-testsuite/ci/master/tree/scripts/interleave-fastq.py
    def interleave(self, fwdpath, revpath, targetpath):
        self.log('Interleaving files {} and {} to {}'.format(
            fwdpath, revpath, targetpath))
        with open(targetpath, 'w') as t:
            with open(fwdpath, 'r') as f, open(revpath, 'r') as r:
                while True:
                    line = f.readline()
                    # since FASTQ cannot contain blank lines
                    if not line or not line.strip():
                        break
                    t.write(line.strip() + '\n')

                    for _ in xrange(3):
                        t.write(f.readline().strip() + '\n')

                    for _ in xrange(4):
                        t.write(r.readline().strip() + '\n')

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
            ret[sg] = None

        roo = 'read_orientation_outward'
        if single:
            ret[roo] = None
        elif roo in data:
            ret[roo] = self.TRUE if data[roo] else self.FALSE
        else:
            ret[roo] = self.FALSE if kbasefile else None

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

    def bool_outgoing(self, boolean):
        return self.TRUE if boolean else self.FALSE

    def get_file_prefix(self):
        return os.path.join(self.scratch, str(uuid.uuid4()))

    def get_shock_data_and_handle_errors(
            self, source_obj_ref, source_obj_name, token, handle, file_type):
        try:
            return self.shock_download(token, handle, file_type)
        except (ShockError, InvalidFileError) as e:
            msg = ('Error downloading reads for object {} ({}) from ' +
                   'Shock node {}: ').format(
                   source_obj_ref, source_obj_name, handle['id'])
            e.args = (msg + e.args[0],) + e.args[1:]
            # py 3 exceptions have no message field
            if hasattr(e, 'message'):  # changing args doesn't change message
                e.message = msg + e.message
            raise

    # there's got to be better way to do this than these processing methods.
    # make some input classes for starters to fix these gross method sigs

    def process_interleaved(self, source_obj_ref, source_obj_name, token,
                            handle, gzip, interleave, file_type=None):

        shockfile, isgz = self.get_shock_data_and_handle_errors(
            source_obj_ref, source_obj_name, token, handle, file_type)

        ret = {}
        if interleave is not False:  # e.g. True or None
            ret['inter'], ret['inter_gz'] = self.handle_gzip(
                shockfile, gzip, isgz, self.get_file_prefix() + '.inter.fastq')
        else:
            if isgz:
                # we expect the job runner to clean up for us
                shockfile = self.gunzip(shockfile)
            fwdpath = os.path.join(self.scratch, self.get_file_prefix() +
                                   '.fwd.fastq')
            revpath = os.path.join(self.scratch, self.get_file_prefix() +
                                   '.rev.fastq')
            self.deinterleave(shockfile, fwdpath, revpath)
            if gzip:
                fwdpath = self.gzip(fwdpath)
                revpath = self.gzip(revpath)
            gzip = self.bool_outgoing(gzip)
            ret['fwd'] = fwdpath
            ret['fwd_gz'] = gzip
            ret['rev'] = revpath
            ret['rev_gz'] = gzip
        return ret

    def process_paired(self, source_obj_ref, source_obj_name, token,
                       fwdhandle, revhandle, gzip, interleave,
                       fwd_file_type=None, rev_file_type=None):

        fwdshock, fwdisgz = self.get_shock_data_and_handle_errors(
            source_obj_ref, source_obj_name, token, fwdhandle, fwd_file_type)
        revshock, revisgz = self.get_shock_data_and_handle_errors(
            source_obj_ref, source_obj_name, token, revhandle, rev_file_type)

        ret = {}
        if interleave:
            # we expect the job runner to clean up for us
            if fwdisgz:
                fwdshock = self.gunzip(fwdshock)
            if revisgz:
                revshock = self.gunzip(revshock)
            intpath = os.path.join(self.scratch, self.get_file_prefix() +
                                   '.inter.fastq')
            self.interleave(fwdshock, revshock, intpath)
            if gzip:
                intpath = self.gzip(intpath)
            ret['inter'] = intpath
            ret['inter_gz'] = self.bool_outgoing(gzip)
        else:
            ret['fwd'], ret['fwd_gz'] = self.handle_gzip(
                fwdshock, gzip, fwdisgz, self.get_file_prefix() + '.fwd.fastq')

            ret['rev'], ret['rev_gz'] = self.handle_gzip(
                revshock, gzip, revisgz, self.get_file_prefix() + '.rev.fastq')
        return ret

    def process_single_end(self, source_obj_ref, source_obj_name, token,
                           handle, gzip, file_type=None):

        shockfile, isgz = self.get_shock_data_and_handle_errors(
            source_obj_ref, source_obj_name, token, handle, file_type)
        f, iszip = self.handle_gzip(shockfile, gzip, isgz,
                                    self.get_file_prefix() + '.sing.fastq')
        return {'sing': f, 'sing_gz': iszip}

    # there's almost certainly a better way to do this
    def handle_gzip(self, oldfile, shouldzip, iszip, prefix):
        zipped = False
        if shouldzip:
            prefix += self.GZIP
            zipped = True
            if iszip:
                self.mv(oldfile, os.path.join(self.scratch, prefix))
            else:
                self.gzip(oldfile, os.path.join(self.scratch, prefix))
        elif shouldzip is None:
            if iszip:
                prefix += self.GZIP
                zipped = True
            self.mv(oldfile, os.path.join(self.scratch, prefix))
        else:
            if iszip:
                self.gunzip(oldfile, os.path.join(self.scratch, prefix))
            else:
                self.mv(oldfile, os.path.join(self.scratch, prefix))
        return prefix, self.bool_outgoing(zipped)

    def mv(self, oldfile, newfile):
        self.log('Moving {} to {}'.format(oldfile, newfile))
        shutil.move(oldfile, newfile)

    def gzip(self, oldfile, newfile=None):
        if oldfile.lower().endswith(self.GZIP):
            raise ValueError('File {} is already gzipped'.format(oldfile))
        if not newfile:
            newfile = oldfile + self.GZIP
        self.log('gzipping {} to {}'.format(oldfile, newfile))
        with open(oldfile, 'rb') as s, gzip.open(newfile, 'wb') as t:
            shutil.copyfileobj(s, t)
        return newfile

    def gunzip(self, oldfile, newfile=None):
        if not oldfile.lower().endswith(self.GZIP):
            raise ValueError('File {} is not gzipped'.format(oldfile))
        if not newfile:
            newfile = oldfile[: -len(self.GZIP)]
        self.log('gunzipping {} to {}'.format(oldfile, newfile))
        with gzip.open(oldfile, 'rb') as s, open(newfile, 'wb') as t:
            shutil.copyfileobj(s, t)
        return newfile

    def process_reads(self, reads, gzip, interleave, token):
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
        self.log('Type: ' + info[2])

        # lib1 = KBaseFile, handle_1 = KBaseAssembly
        if kbasefile:
            if single:
                reads = data['lib']['file']
                type_ = data['lib']['type']
                ret['files'] = self.process_single_end(
                    ref, obj_name, token, reads, gzip, type_)
            else:
                fwd_reads = data['lib1']['file']
                fwd_type = data['lib1']['type']
                if 'lib2' in data:  # not interleaved
                    rev_reads = data['lib2']['file']
                    rev_type = data['lib2']['type']
                    ret['files'] = self.process_paired(
                        ref, obj_name, token, fwd_reads, rev_reads, gzip,
                        interleave, fwd_type, rev_type)
                else:
                    ret['files'] = self.process_interleaved(
                        ref, obj_name, token, fwd_reads, gzip, interleave,
                        fwd_type)
        else:  # KBaseAssembly
            if single:
                ret['files'] = self.process_single_end(
                    ref, obj_name, token, data['handle'], gzip)
            else:
                if 'handle_2' in data:  # not interleaved
                    ret['files'] = self.process_paired(
                        ref, obj_name, token, data['handle_1'],
                        data['handle_2'], gzip, interleave)
                else:
                    ret['files'] = self.process_interleaved(
                        ref, obj_name, token, data['handle_1'], gzip,
                        interleave)

        return ret

    def process_ternary(self, params, boolname):
        if boolname not in params or params[boolname] is None:
            params[boolname] = None
        elif params[boolname] == 'true':
            params[boolname] = True
        elif params[boolname] == 'false':
            params[boolname] = False
        else:
            raise ValueError(('Illegal value for ternary parameter {}: {}. ' +
                              'Allowed values are "true", "false", and null.')
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
        if type(reads) != list:
            raise ValueError(self.PARAM_IN_LIB + ' must be a list')
        if not reads:
            raise ValueError('At least one reads library must be provided')
        reads = list(set(reads))
        for read_name in reads:
            if not read_name or self.INVALID_WS_OBJ_NAME_RE.search(read_name):
                raise ValueError('Invalid workspace object name ' + read_name)
        params[self.PARAM_IN_LIB] = reads

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
                there's nothing better to do. If so, each process/thread needs
                its own shock_tmp folder.
            Add user specified failure conditions - e.g. fail if is/is not
                metagenome, outwards reads, etc.
        '''

        self.log('Running convert_read_library_to_file with params:\n' +
                 pformat(params))

        token = ctx['token']

        self.process_params(params)
#         self.log('\n' + pformat(params))

        # Get the reads library
        ws = workspaceService(self.workspaceURL, token=token)
        ws_reads_ids = []
        for read_name in params[self.PARAM_IN_LIB]:
            ws_reads_ids.append({'ref': params[self.PARAM_IN_WS] + '/' +
                                 read_name})
        try:
            reads = ws.get_objects(ws_reads_ids)
        except WorkspaceException as e:
            self.log('Logging stacktrace from workspace exception:\n' + e.data)
            raise

        output = {}
        for read_name, read in zip(params[self.PARAM_IN_LIB], reads):
            self.log('=== processing read library ' + read_name + '===\n',
                     prefix_newline=True)
            output[read_name] = self.process_reads(
                read, params[self.PARAM_IN_GZIP],
                params[self.PARAM_IN_INTERLEAVED], token)
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
