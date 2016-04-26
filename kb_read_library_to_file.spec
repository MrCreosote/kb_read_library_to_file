#include <KBaseCommon.spec>
/*
A KBase module: kb_read_library_to_file

Takes KBaseFile/KBaseAssembly PairedEndLibrary/SingleEndLibrary reads library
workspace object IDs as input and produces a FASTQ files along with file
metadata.

*/

module kb_read_library_to_file {

    /* A boolean. Allowed values are 'false' or 'true'. Any other value is
        invalid.
     */
    typedef string bool;
    
    /* A ternary. Allowed values are 'false', 'true', or 'unknown'. Any other
        value is invalid.
     */
     typedef string tern;
    
    /* The workspace object name of a read library, whether of the
       KBaseAssembly or KBaseFile type.
    */
    typedef string read_lib;
    
    /* An output file name prefix. The suffix will be determined by the
        converter:
        If the file is interleaved, the first portion of the suffix will be
            .int. Otherwise it will be .fwd. for the forward / left reads,
            .rev. for the reverse / right reads, or .sing. for single ended
            reads.
        The next portion of the suffix will be .fastq.
        If a file is in gzip format, the file will end with .gz.
     */
    typedef string file_prefix;
    
    /* Input parameters for converting libraries to files.
        string workspace_name - the name of the workspace from which to take
           input.
        mapping<read_lib, file_prefix> read_libraries - read library
            objects to convert and the prefix of the file(s) in which the FASTQ
            files will be saved. The set of file_prefixes must be unique.
        bool gzip - if true, gzip the files if they are not already zipped. If
            false or missing, unzip any zipped files.
        bool interleaved - if true, provide the files in interleaved format if
            they are not already. If false or missing, provide forward and 
            reverse reads files.
    */
    typedef structure {
        string workspace_name;
        mapping<read_lib, file_prefix> read_libraries;
        bool gzip;
        bool interlaced;
    } ConvertReadLibraryParams;
    
    /* Information about each set of reads.
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
        metagenome.
        tern read_orientation_outward - whether the read orientation is outward
            from the set of primers. Always false for singled ended reads.
        string sequencing_tech - the sequencing technology used to produce the
            reads. null if unknown.
        KBaseCommon.StrainInfo strain - information about the organism strain
            that was sequenced. null if unavailable.
        KBaseCommon.SourceInfo source - information about the organism source.
            null if unavailable.
        float insert_size_mean - the mean size of the genetic fragments. null
            if unavailable.
        float insert_size_std_dev - the standard deviation of the size of the
            genetic fragments. null if unavailable.
        int read_count - the number of reads in the this dataset. null if
            unavailable.
        int read_size - the total size of the reads, in bases. null if
            unavailable.
        float gc_content - the GC content of the reads. null if
            unavailable.
     */
    typedef structure {
        string fwd;
        string rev;
        string inter;
        string sing;
        string ref;
        tern single_genome;
        tern read_orientation_outward;
        string sequencing_tech;
        KBaseCommon.StrainInfo strain;
        KBaseCommon.SourceInfo source;
        float insert_size_mean;
        float insert_size_std_dev;
        int read_count;
        int read_size;
        float gc_content;
    } ConvertedReadLibrary;

    /* The output of the convert method.
        mapping<read_lib, ConvertedReadLibrary> files - a mapping
            of the read library workspace object names to information
            about the converted data for each library.
     */
    typedef structure {
        mapping<read_lib, ConvertedReadLibrary> files;
    } ConvertReadLibraryOutput;
   
    /* Convert read libraries to files */
    funcdef convert_read_library_to_file(ConvertReadLibraryParams params)
        returns(ConvertReadLibraryOutput output) authentication required;
};