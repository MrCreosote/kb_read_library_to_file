
package us.kbase.kbreadlibrarytofile;

import java.util.HashMap;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;
import us.kbase.kbasecommon.SourceInfo;
import us.kbase.kbasecommon.StrainInfo;


/**
 * <p>Original spec-file type: ConvertedReadLibrary</p>
 * <pre>
 * Information about each set of reads.
 * The reads file locations:
 * string fwd - the path to the forward / left reads.
 * string rev - the path to the reverse / right reads.
 * string inter - the path to the interleaved reads.
 * string sing - the path to the single end reads.
 * Only the appropriate fields will be present in the structure.
 * Other fields:
 * string ref - the workspace reference of the reads file, e.g
 *     workspace_id/object_id/version.
 * tern single_genome - whether the reads are from a single genome or a
 * metagenome.
 * tern read_orientation_outward - whether the read orientation is outward
 *     from the set of primers. Always false for singled ended reads.
 * string sequencing_tech - the sequencing technology used to produce the
 *     reads. null if unknown.
 * KBaseCommon.StrainInfo strain - information about the organism strain
 *     that was sequenced. null if unavailable.
 * KBaseCommon.SourceInfo source - information about the organism source.
 *     null if unavailable.
 * float insert_size_mean - the mean size of the genetic fragments. null
 *     if unavailable.
 * float insert_size_std_dev - the standard deviation of the size of the
 *     genetic fragments. null if unavailable.
 * int read_count - the number of reads in the this dataset. null if
 *     unavailable.
 * int read_size - the total size of the reads, in bases. null if
 *     unavailable.
 * float gc_content - the GC content of the reads. null if
 *     unavailable.
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "fwd",
    "rev",
    "inter",
    "sing",
    "ref",
    "single_genome",
    "read_orientation_outward",
    "sequencing_tech",
    "strain",
    "source",
    "insert_size_mean",
    "insert_size_std_dev",
    "read_count",
    "read_size",
    "gc_content"
})
public class ConvertedReadLibrary {

    @JsonProperty("fwd")
    private String fwd;
    @JsonProperty("rev")
    private String rev;
    @JsonProperty("inter")
    private String inter;
    @JsonProperty("sing")
    private String sing;
    @JsonProperty("ref")
    private String ref;
    @JsonProperty("single_genome")
    private String singleGenome;
    @JsonProperty("read_orientation_outward")
    private String readOrientationOutward;
    @JsonProperty("sequencing_tech")
    private String sequencingTech;
    /**
     * <p>Original spec-file type: StrainInfo</p>
     * <pre>
     * Information about a strain.
     * genetic_code - the genetic code of the strain.
     *     See http://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi?mode=c
     * genus - the genus of the strain
     * species - the species of the strain
     * strain - the identifier for the strain
     * source - information about the source of the strain
     * organelle - the organelle of interest for the related data (e.g.
     *     mitochondria)
     * ncbi_taxid - the NCBI taxonomy ID of the strain
     * location - the location from which the strain was collected
     * @optional genetic_code source ncbi_taxid organelle location
     * </pre>
     * 
     */
    @JsonProperty("strain")
    private StrainInfo strain;
    /**
     * <p>Original spec-file type: SourceInfo</p>
     * <pre>
     * Information about the source of a piece of data.
     * source - the name of the source (e.g. NCBI, JGI, Swiss-Prot)
     * source_id - the ID of the data at the source
     * project_id - the ID of a project encompassing the data at the source
     * @optional source source_id project_id
     * </pre>
     * 
     */
    @JsonProperty("source")
    private SourceInfo source;
    @JsonProperty("insert_size_mean")
    private Double insertSizeMean;
    @JsonProperty("insert_size_std_dev")
    private Double insertSizeStdDev;
    @JsonProperty("read_count")
    private Long readCount;
    @JsonProperty("read_size")
    private Long readSize;
    @JsonProperty("gc_content")
    private Double gcContent;
    private Map<String, Object> additionalProperties = new HashMap<String, Object>();

    @JsonProperty("fwd")
    public String getFwd() {
        return fwd;
    }

    @JsonProperty("fwd")
    public void setFwd(String fwd) {
        this.fwd = fwd;
    }

    public ConvertedReadLibrary withFwd(String fwd) {
        this.fwd = fwd;
        return this;
    }

    @JsonProperty("rev")
    public String getRev() {
        return rev;
    }

    @JsonProperty("rev")
    public void setRev(String rev) {
        this.rev = rev;
    }

    public ConvertedReadLibrary withRev(String rev) {
        this.rev = rev;
        return this;
    }

    @JsonProperty("inter")
    public String getInter() {
        return inter;
    }

    @JsonProperty("inter")
    public void setInter(String inter) {
        this.inter = inter;
    }

    public ConvertedReadLibrary withInter(String inter) {
        this.inter = inter;
        return this;
    }

    @JsonProperty("sing")
    public String getSing() {
        return sing;
    }

    @JsonProperty("sing")
    public void setSing(String sing) {
        this.sing = sing;
    }

    public ConvertedReadLibrary withSing(String sing) {
        this.sing = sing;
        return this;
    }

    @JsonProperty("ref")
    public String getRef() {
        return ref;
    }

    @JsonProperty("ref")
    public void setRef(String ref) {
        this.ref = ref;
    }

    public ConvertedReadLibrary withRef(String ref) {
        this.ref = ref;
        return this;
    }

    @JsonProperty("single_genome")
    public String getSingleGenome() {
        return singleGenome;
    }

    @JsonProperty("single_genome")
    public void setSingleGenome(String singleGenome) {
        this.singleGenome = singleGenome;
    }

    public ConvertedReadLibrary withSingleGenome(String singleGenome) {
        this.singleGenome = singleGenome;
        return this;
    }

    @JsonProperty("read_orientation_outward")
    public String getReadOrientationOutward() {
        return readOrientationOutward;
    }

    @JsonProperty("read_orientation_outward")
    public void setReadOrientationOutward(String readOrientationOutward) {
        this.readOrientationOutward = readOrientationOutward;
    }

    public ConvertedReadLibrary withReadOrientationOutward(String readOrientationOutward) {
        this.readOrientationOutward = readOrientationOutward;
        return this;
    }

    @JsonProperty("sequencing_tech")
    public String getSequencingTech() {
        return sequencingTech;
    }

    @JsonProperty("sequencing_tech")
    public void setSequencingTech(String sequencingTech) {
        this.sequencingTech = sequencingTech;
    }

    public ConvertedReadLibrary withSequencingTech(String sequencingTech) {
        this.sequencingTech = sequencingTech;
        return this;
    }

    /**
     * <p>Original spec-file type: StrainInfo</p>
     * <pre>
     * Information about a strain.
     * genetic_code - the genetic code of the strain.
     *     See http://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi?mode=c
     * genus - the genus of the strain
     * species - the species of the strain
     * strain - the identifier for the strain
     * source - information about the source of the strain
     * organelle - the organelle of interest for the related data (e.g.
     *     mitochondria)
     * ncbi_taxid - the NCBI taxonomy ID of the strain
     * location - the location from which the strain was collected
     * @optional genetic_code source ncbi_taxid organelle location
     * </pre>
     * 
     */
    @JsonProperty("strain")
    public StrainInfo getStrain() {
        return strain;
    }

    /**
     * <p>Original spec-file type: StrainInfo</p>
     * <pre>
     * Information about a strain.
     * genetic_code - the genetic code of the strain.
     *     See http://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi?mode=c
     * genus - the genus of the strain
     * species - the species of the strain
     * strain - the identifier for the strain
     * source - information about the source of the strain
     * organelle - the organelle of interest for the related data (e.g.
     *     mitochondria)
     * ncbi_taxid - the NCBI taxonomy ID of the strain
     * location - the location from which the strain was collected
     * @optional genetic_code source ncbi_taxid organelle location
     * </pre>
     * 
     */
    @JsonProperty("strain")
    public void setStrain(StrainInfo strain) {
        this.strain = strain;
    }

    public ConvertedReadLibrary withStrain(StrainInfo strain) {
        this.strain = strain;
        return this;
    }

    /**
     * <p>Original spec-file type: SourceInfo</p>
     * <pre>
     * Information about the source of a piece of data.
     * source - the name of the source (e.g. NCBI, JGI, Swiss-Prot)
     * source_id - the ID of the data at the source
     * project_id - the ID of a project encompassing the data at the source
     * @optional source source_id project_id
     * </pre>
     * 
     */
    @JsonProperty("source")
    public SourceInfo getSource() {
        return source;
    }

    /**
     * <p>Original spec-file type: SourceInfo</p>
     * <pre>
     * Information about the source of a piece of data.
     * source - the name of the source (e.g. NCBI, JGI, Swiss-Prot)
     * source_id - the ID of the data at the source
     * project_id - the ID of a project encompassing the data at the source
     * @optional source source_id project_id
     * </pre>
     * 
     */
    @JsonProperty("source")
    public void setSource(SourceInfo source) {
        this.source = source;
    }

    public ConvertedReadLibrary withSource(SourceInfo source) {
        this.source = source;
        return this;
    }

    @JsonProperty("insert_size_mean")
    public Double getInsertSizeMean() {
        return insertSizeMean;
    }

    @JsonProperty("insert_size_mean")
    public void setInsertSizeMean(Double insertSizeMean) {
        this.insertSizeMean = insertSizeMean;
    }

    public ConvertedReadLibrary withInsertSizeMean(Double insertSizeMean) {
        this.insertSizeMean = insertSizeMean;
        return this;
    }

    @JsonProperty("insert_size_std_dev")
    public Double getInsertSizeStdDev() {
        return insertSizeStdDev;
    }

    @JsonProperty("insert_size_std_dev")
    public void setInsertSizeStdDev(Double insertSizeStdDev) {
        this.insertSizeStdDev = insertSizeStdDev;
    }

    public ConvertedReadLibrary withInsertSizeStdDev(Double insertSizeStdDev) {
        this.insertSizeStdDev = insertSizeStdDev;
        return this;
    }

    @JsonProperty("read_count")
    public Long getReadCount() {
        return readCount;
    }

    @JsonProperty("read_count")
    public void setReadCount(Long readCount) {
        this.readCount = readCount;
    }

    public ConvertedReadLibrary withReadCount(Long readCount) {
        this.readCount = readCount;
        return this;
    }

    @JsonProperty("read_size")
    public Long getReadSize() {
        return readSize;
    }

    @JsonProperty("read_size")
    public void setReadSize(Long readSize) {
        this.readSize = readSize;
    }

    public ConvertedReadLibrary withReadSize(Long readSize) {
        this.readSize = readSize;
        return this;
    }

    @JsonProperty("gc_content")
    public Double getGcContent() {
        return gcContent;
    }

    @JsonProperty("gc_content")
    public void setGcContent(Double gcContent) {
        this.gcContent = gcContent;
    }

    public ConvertedReadLibrary withGcContent(Double gcContent) {
        this.gcContent = gcContent;
        return this;
    }

    @JsonAnyGetter
    public Map<String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public String toString() {
        return ((((((((((((((((((((((((((((((((("ConvertedReadLibrary"+" [fwd=")+ fwd)+", rev=")+ rev)+", inter=")+ inter)+", sing=")+ sing)+", ref=")+ ref)+", singleGenome=")+ singleGenome)+", readOrientationOutward=")+ readOrientationOutward)+", sequencingTech=")+ sequencingTech)+", strain=")+ strain)+", source=")+ source)+", insertSizeMean=")+ insertSizeMean)+", insertSizeStdDev=")+ insertSizeStdDev)+", readCount=")+ readCount)+", readSize=")+ readSize)+", gcContent=")+ gcContent)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
