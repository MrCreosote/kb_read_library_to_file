#include <KBaseCommon.spec>
/*
A KBase module: kb_read_library_to_file

Takes a KBaseFile or KBaseAssembly PairedEndLibrary workspace object ID as
input and produces a FASTQ file along with file metadata.

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
    
    /* The workspace object name of a PairedEndLibrary file, whether of the
       KBaseAssembly or KBaseFile type.
    */
    typedef string paired_end_lib;
    
    /* An output file name prefix. The suffix will be determined by the
        converter:
        If the file is interleaved, the first portion of the suffix will be
            .int. Otherwise it will be .fwd. for the forward / left reads and
            .rev. for the reverse / right reads.
        The next portion of the suffix will be .fastq.
        If a file is in gzip format, the file will end with .gz.
     */
    typedef string file_prefix;
    
    /* Input parameters for converting libraries to files.
        string workspace_name - the name of the workspace from which to take
           input.
        mapping<paired_end_lib, file_prefix> read_libraries - PairedEndLibrary
            objects to convert and the prefix of the file(s) in which the FASTQ
            files will be saved.
        bool gzip - if true, gzip the files if they are not already zipped. If
            false or missing, unzip any zipped files.
        bool interleaved - if true, provide the files in interleaved format if
            they are not already. If false or missing, provide forward and 
            reverse reads files.
    */
    typedef structure {
        string workspace_name;
        mapping<paired_end_lib, file_prefix> read_libraries;
        bool gzip;
        bool interlaced;
    } ConvertPairedEndLibraryParams;
    
    /* Information about each set of reads.
        The reads file locations:
        string fwd - the path to the forward / left reads.
        string rev - the path to the reverse / right reads.
        string inter - the path to the interleaved reads.
        Only the appropriate fields will be present in the structure.

        Other fields:
        tern single_genome - whether the reads are from a single genome or a
        metagenome.
        tern read_orientation_outward - whether the read orientation is outward
            from the set of primers.
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
    } ConvertPairedEndLibraryOutput;

    /* Convert PairedEndLibraries to files */
    funcdef convert_paired_end_library_to_file(
            ConvertPairedEndLibraryParams params)
        returns(ConvertPairedEndLibraryOutput output) authentication required;
};