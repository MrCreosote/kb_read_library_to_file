package kb_read_library_to_file::kb_read_library_to_fileClient;

use JSON::RPC::Client;
use POSIX;
use strict;
use Data::Dumper;
use URI;
use Bio::KBase::Exceptions;
my $get_time = sub { time, 0 };
eval {
    require Time::HiRes;
    $get_time = sub { Time::HiRes::gettimeofday() };
};

use Bio::KBase::AuthToken;

# Client version should match Impl version
# This is a Semantic Version number,
# http://semver.org
our $VERSION = "0.1.0";

=head1 NAME

kb_read_library_to_file::kb_read_library_to_fileClient

=head1 DESCRIPTION


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


=cut

sub new
{
    my($class, $url, @args) = @_;
    

    my $self = {
	client => kb_read_library_to_file::kb_read_library_to_fileClient::RpcClient->new,
	url => $url,
	headers => [],
    };

    chomp($self->{hostname} = `hostname`);
    $self->{hostname} ||= 'unknown-host';

    #
    # Set up for propagating KBRPC_TAG and KBRPC_METADATA environment variables through
    # to invoked services. If these values are not set, we create a new tag
    # and a metadata field with basic information about the invoking script.
    #
    if ($ENV{KBRPC_TAG})
    {
	$self->{kbrpc_tag} = $ENV{KBRPC_TAG};
    }
    else
    {
	my ($t, $us) = &$get_time();
	$us = sprintf("%06d", $us);
	my $ts = strftime("%Y-%m-%dT%H:%M:%S.${us}Z", gmtime $t);
	$self->{kbrpc_tag} = "C:$0:$self->{hostname}:$$:$ts";
    }
    push(@{$self->{headers}}, 'Kbrpc-Tag', $self->{kbrpc_tag});

    if ($ENV{KBRPC_METADATA})
    {
	$self->{kbrpc_metadata} = $ENV{KBRPC_METADATA};
	push(@{$self->{headers}}, 'Kbrpc-Metadata', $self->{kbrpc_metadata});
    }

    if ($ENV{KBRPC_ERROR_DEST})
    {
	$self->{kbrpc_error_dest} = $ENV{KBRPC_ERROR_DEST};
	push(@{$self->{headers}}, 'Kbrpc-Errordest', $self->{kbrpc_error_dest});
    }

    #
    # This module requires authentication.
    #
    # We create an auth token, passing through the arguments that we were (hopefully) given.

    {
	my $token = Bio::KBase::AuthToken->new(@args);
	
	if (!$token->error_message)
	{
	    $self->{token} = $token->token;
	    $self->{client}->{token} = $token->token;
	}
        else
        {
	    #
	    # All methods in this module require authentication. In this case, if we
	    # don't have a token, we can't continue.
	    #
	    die "Authentication failed: " . $token->error_message;
	}
    }

    my $ua = $self->{client}->ua;	 
    my $timeout = $ENV{CDMI_TIMEOUT} || (30 * 60);	 
    $ua->timeout($timeout);
    bless $self, $class;
    #    $self->_validate_version();
    return $self;
}




=head2 convert_read_library_to_file

  $output = $obj->convert_read_library_to_file($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a kb_read_library_to_file.ConvertReadLibraryParams
$output is a kb_read_library_to_file.ConvertReadLibraryOutput
ConvertReadLibraryParams is a reference to a hash where the following keys are defined:
	workspace_name has a value which is a string
	read_libraries has a value which is a reference to a hash where the key is a kb_read_library_to_file.read_lib and the value is a kb_read_library_to_file.file_path_prefix
	gzip has a value which is a kb_read_library_to_file.tern
	interlaced has a value which is a kb_read_library_to_file.tern
read_lib is a string
file_path_prefix is a string
tern is a string
ConvertReadLibraryOutput is a reference to a hash where the following keys are defined:
	files has a value which is a reference to a hash where the key is a kb_read_library_to_file.read_lib and the value is a kb_read_library_to_file.ConvertedReadLibrary
ConvertedReadLibrary is a reference to a hash where the following keys are defined:
	fwd has a value which is a string
	rev has a value which is a string
	inter has a value which is a string
	sing has a value which is a string
	ref has a value which is a string
	single_genome has a value which is a kb_read_library_to_file.tern
	read_orientation_outward has a value which is a kb_read_library_to_file.tern
	sequencing_tech has a value which is a string
	strain has a value which is a KBaseCommon.StrainInfo
	source has a value which is a KBaseCommon.SourceInfo
	insert_size_mean has a value which is a float
	insert_size_std_dev has a value which is a float
	read_count has a value which is an int
	read_size has a value which is an int
	gc_content has a value which is a float
StrainInfo is a reference to a hash where the following keys are defined:
	genetic_code has a value which is an int
	genus has a value which is a string
	species has a value which is a string
	strain has a value which is a string
	organelle has a value which is a string
	source has a value which is a KBaseCommon.SourceInfo
	ncbi_taxid has a value which is an int
	location has a value which is a KBaseCommon.Location
SourceInfo is a reference to a hash where the following keys are defined:
	source has a value which is a string
	source_id has a value which is a KBaseCommon.source_id
	project_id has a value which is a KBaseCommon.project_id
source_id is a string
project_id is a string
Location is a reference to a hash where the following keys are defined:
	lat has a value which is a float
	lon has a value which is a float
	elevation has a value which is a float
	date has a value which is a string
	description has a value which is a string

</pre>

=end html

=begin text

$params is a kb_read_library_to_file.ConvertReadLibraryParams
$output is a kb_read_library_to_file.ConvertReadLibraryOutput
ConvertReadLibraryParams is a reference to a hash where the following keys are defined:
	workspace_name has a value which is a string
	read_libraries has a value which is a reference to a hash where the key is a kb_read_library_to_file.read_lib and the value is a kb_read_library_to_file.file_path_prefix
	gzip has a value which is a kb_read_library_to_file.tern
	interlaced has a value which is a kb_read_library_to_file.tern
read_lib is a string
file_path_prefix is a string
tern is a string
ConvertReadLibraryOutput is a reference to a hash where the following keys are defined:
	files has a value which is a reference to a hash where the key is a kb_read_library_to_file.read_lib and the value is a kb_read_library_to_file.ConvertedReadLibrary
ConvertedReadLibrary is a reference to a hash where the following keys are defined:
	fwd has a value which is a string
	rev has a value which is a string
	inter has a value which is a string
	sing has a value which is a string
	ref has a value which is a string
	single_genome has a value which is a kb_read_library_to_file.tern
	read_orientation_outward has a value which is a kb_read_library_to_file.tern
	sequencing_tech has a value which is a string
	strain has a value which is a KBaseCommon.StrainInfo
	source has a value which is a KBaseCommon.SourceInfo
	insert_size_mean has a value which is a float
	insert_size_std_dev has a value which is a float
	read_count has a value which is an int
	read_size has a value which is an int
	gc_content has a value which is a float
StrainInfo is a reference to a hash where the following keys are defined:
	genetic_code has a value which is an int
	genus has a value which is a string
	species has a value which is a string
	strain has a value which is a string
	organelle has a value which is a string
	source has a value which is a KBaseCommon.SourceInfo
	ncbi_taxid has a value which is an int
	location has a value which is a KBaseCommon.Location
SourceInfo is a reference to a hash where the following keys are defined:
	source has a value which is a string
	source_id has a value which is a KBaseCommon.source_id
	project_id has a value which is a KBaseCommon.project_id
source_id is a string
project_id is a string
Location is a reference to a hash where the following keys are defined:
	lat has a value which is a float
	lon has a value which is a float
	elevation has a value which is a float
	date has a value which is a string
	description has a value which is a string


=end text

=item Description

Convert read libraries to files

=back

=cut

 sub convert_read_library_to_file
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function convert_read_library_to_file (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to convert_read_library_to_file:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'convert_read_library_to_file');
	}
    }

    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
	method => "kb_read_library_to_file.convert_read_library_to_file",
	params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'convert_read_library_to_file',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method convert_read_library_to_file",
					    status_line => $self->{client}->status_line,
					    method_name => 'convert_read_library_to_file',
				       );
    }
}
 
  

sub version {
    my ($self) = @_;
    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
        method => "kb_read_library_to_file.version",
        params => [],
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(
                error => $result->error_message,
                code => $result->content->{code},
                method_name => 'convert_read_library_to_file',
            );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(
            error => "Error invoking method convert_read_library_to_file",
            status_line => $self->{client}->status_line,
            method_name => 'convert_read_library_to_file',
        );
    }
}

sub _validate_version {
    my ($self) = @_;
    my $svr_version = $self->version();
    my $client_version = $VERSION;
    my ($cMajor, $cMinor) = split(/\./, $client_version);
    my ($sMajor, $sMinor) = split(/\./, $svr_version);
    if ($sMajor != $cMajor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Major version numbers differ.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor < $cMinor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Client minor version greater than Server minor version.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor > $cMinor) {
        warn "New client version available for kb_read_library_to_file::kb_read_library_to_fileClient\n";
    }
    if ($sMajor == 0) {
        warn "kb_read_library_to_file::kb_read_library_to_fileClient version is $svr_version. API subject to change.\n";
    }
}

=head1 TYPES



=head2 tern

=over 4



=item Description

A ternary. Allowed values are 'false', 'true', or null. Any other
value is invalid.


=item Definition

=begin html

<pre>
a string
</pre>

=end html

=begin text

a string

=end text

=back



=head2 read_lib

=over 4



=item Description

The workspace object name of a read library, whether of the
KBaseAssembly or KBaseFile type.


=item Definition

=begin html

<pre>
a string
</pre>

=end html

=begin text

a string

=end text

=back



=head2 file_path_prefix

=over 4



=item Description

An absolute output file path prefix. The location given by the path must
be writable. The suffix of the file will be determined by the
converter:
If the file is interleaved, the first portion of the suffix will be
    .int. Otherwise it will be .fwd. for the forward / left reads,
    .rev. for the reverse / right reads, or .sing. for single ended
    reads.
The next portion of the suffix will be .fastq.
If a file is in gzip format, the file will end with .gz.


=item Definition

=begin html

<pre>
a string
</pre>

=end html

=begin text

a string

=end text

=back



=head2 ConvertReadLibraryParams

=over 4



=item Description

Input parameters for converting libraries to files.
string workspace_name - the name of the workspace from which to take
   input.
mapping<read_lib, file_path_prefix> read_libraries - read library
    objects to convert and the prefix of the file(s) in which the FASTQ
    files will be saved. The set of file_prefixes must be unique.
tern gzip - if true, gzip any unzipped files. If false, gunzip any
    zipped files. If null or missing, leave files as is unless
    unzipping is required for interleaving or deinterleaving, in which
    case the files will be left unzipped.
tern interleaved - if true, provide the files in interleaved format if
    they are not already. If false, provide forward and reverse reads
    files. If null or missing, leave files as is.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
workspace_name has a value which is a string
read_libraries has a value which is a reference to a hash where the key is a kb_read_library_to_file.read_lib and the value is a kb_read_library_to_file.file_path_prefix
gzip has a value which is a kb_read_library_to_file.tern
interlaced has a value which is a kb_read_library_to_file.tern

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
workspace_name has a value which is a string
read_libraries has a value which is a reference to a hash where the key is a kb_read_library_to_file.read_lib and the value is a kb_read_library_to_file.file_path_prefix
gzip has a value which is a kb_read_library_to_file.tern
interlaced has a value which is a kb_read_library_to_file.tern


=end text

=back



=head2 ConvertedReadLibrary

=over 4



=item Description

Information about each set of reads.
The reads file locations:
string fwd - the path to the forward / left reads.
string rev - the path to the reverse / right reads.
string inter - the path to the interleaved reads.
string sing - the path to the single end reads.
Only the appropriate fields will be present in the structure.

Other fields:
string ref - the workspace reference of the reads file, e.g
    workspace_id/object_id/version.
tern single_genome - whether the reads are from a single genome or a
    metagenome. null if unknown.
tern read_orientation_outward - whether the read orientation is outward
    from the set of primers. Always false for singled ended reads. null
    if unknown.
string sequencing_tech - the sequencing technology used to produce the
    reads. null if unknown.
KBaseCommon.StrainInfo strain - information about the organism strain
    that was sequenced. null if unavailable.
KBaseCommon.SourceInfo source - information about the organism source.
    null if unavailable.
float insert_size_mean - the mean size of the genetic fragments. null
    if unavailable or single end read.
float insert_size_std_dev - the standard deviation of the size of the
    genetic fragments. null if unavailable or single end read.
int read_count - the number of reads in the this dataset. null if
    unavailable.
int read_size - the total size of the reads, in bases. null if
    unavailable.
float gc_content - the GC content of the reads. null if
    unavailable.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
fwd has a value which is a string
rev has a value which is a string
inter has a value which is a string
sing has a value which is a string
ref has a value which is a string
single_genome has a value which is a kb_read_library_to_file.tern
read_orientation_outward has a value which is a kb_read_library_to_file.tern
sequencing_tech has a value which is a string
strain has a value which is a KBaseCommon.StrainInfo
source has a value which is a KBaseCommon.SourceInfo
insert_size_mean has a value which is a float
insert_size_std_dev has a value which is a float
read_count has a value which is an int
read_size has a value which is an int
gc_content has a value which is a float

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
fwd has a value which is a string
rev has a value which is a string
inter has a value which is a string
sing has a value which is a string
ref has a value which is a string
single_genome has a value which is a kb_read_library_to_file.tern
read_orientation_outward has a value which is a kb_read_library_to_file.tern
sequencing_tech has a value which is a string
strain has a value which is a KBaseCommon.StrainInfo
source has a value which is a KBaseCommon.SourceInfo
insert_size_mean has a value which is a float
insert_size_std_dev has a value which is a float
read_count has a value which is an int
read_size has a value which is an int
gc_content has a value which is a float


=end text

=back



=head2 ConvertReadLibraryOutput

=over 4



=item Description

The output of the convert method.
mapping<read_lib, ConvertedReadLibrary> files - a mapping
    of the read library workspace object names to information
    about the converted data for each library.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
files has a value which is a reference to a hash where the key is a kb_read_library_to_file.read_lib and the value is a kb_read_library_to_file.ConvertedReadLibrary

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
files has a value which is a reference to a hash where the key is a kb_read_library_to_file.read_lib and the value is a kb_read_library_to_file.ConvertedReadLibrary


=end text

=back



=cut

package kb_read_library_to_file::kb_read_library_to_fileClient::RpcClient;
use base 'JSON::RPC::Client';
use POSIX;
use strict;

#
# Override JSON::RPC::Client::call because it doesn't handle error returns properly.
#

sub call {
    my ($self, $uri, $headers, $obj) = @_;
    my $result;


    {
	if ($uri =~ /\?/) {
	    $result = $self->_get($uri);
	}
	else {
	    Carp::croak "not hashref." unless (ref $obj eq 'HASH');
	    $result = $self->_post($uri, $headers, $obj);
	}

    }

    my $service = $obj->{method} =~ /^system\./ if ( $obj );

    $self->status_line($result->status_line);

    if ($result->is_success) {

        return unless($result->content); # notification?

        if ($service) {
            return JSON::RPC::ServiceObject->new($result, $self->json);
        }

        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    elsif ($result->content_type eq 'application/json')
    {
        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    else {
        return;
    }
}


sub _post {
    my ($self, $uri, $headers, $obj) = @_;
    my $json = $self->json;

    $obj->{version} ||= $self->{version} || '1.1';

    if ($obj->{version} eq '1.0') {
        delete $obj->{version};
        if (exists $obj->{id}) {
            $self->id($obj->{id}) if ($obj->{id}); # if undef, it is notification.
        }
        else {
            $obj->{id} = $self->id || ($self->id('JSON::RPC::Client'));
        }
    }
    else {
        # $obj->{id} = $self->id if (defined $self->id);
	# Assign a random number to the id if one hasn't been set
	$obj->{id} = (defined $self->id) ? $self->id : substr(rand(),2);
    }

    my $content = $json->encode($obj);

    $self->ua->post(
        $uri,
        Content_Type   => $self->{content_type},
        Content        => $content,
        Accept         => 'application/json',
	@$headers,
	($self->{token} ? (Authorization => $self->{token}) : ()),
    );
}



1;
