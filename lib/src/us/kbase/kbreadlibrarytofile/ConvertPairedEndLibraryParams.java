
package us.kbase.kbreadlibrarytofile;

import java.util.HashMap;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


/**
 * <p>Original spec-file type: ConvertPairedEndLibraryParams</p>
 * <pre>
 * Input parameters for converting libraries to files.
 * string workspace_name - the name of the workspace from which to take
 *    input.
 * mapping<paired_end_lib, out_file> read_libraries - PairedEndLibrary
 *     objects to convert and the prefix of the file in which the FASTQ
 *     files will be saved.
 * bool gzip - if true, gzip the files if they are not already zipped. If
 *     false or missing, unzip any zipped files.
 * bool interleaved - if true, provide the files in interleaved format if
 *     they are not already. If false or missing, provide forward and 
 *     reverse reads files.
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "workspace_name",
    "read_libraries",
    "gzip",
    "interlaced"
})
public class ConvertPairedEndLibraryParams {

    @JsonProperty("workspace_name")
    private java.lang.String workspaceName;
    @JsonProperty("read_libraries")
    private Map<String, String> readLibraries;
    @JsonProperty("gzip")
    private java.lang.String gzip;
    @JsonProperty("interlaced")
    private java.lang.String interlaced;
    private Map<java.lang.String, Object> additionalProperties = new HashMap<java.lang.String, Object>();

    @JsonProperty("workspace_name")
    public java.lang.String getWorkspaceName() {
        return workspaceName;
    }

    @JsonProperty("workspace_name")
    public void setWorkspaceName(java.lang.String workspaceName) {
        this.workspaceName = workspaceName;
    }

    public ConvertPairedEndLibraryParams withWorkspaceName(java.lang.String workspaceName) {
        this.workspaceName = workspaceName;
        return this;
    }

    @JsonProperty("read_libraries")
    public Map<String, String> getReadLibraries() {
        return readLibraries;
    }

    @JsonProperty("read_libraries")
    public void setReadLibraries(Map<String, String> readLibraries) {
        this.readLibraries = readLibraries;
    }

    public ConvertPairedEndLibraryParams withReadLibraries(Map<String, String> readLibraries) {
        this.readLibraries = readLibraries;
        return this;
    }

    @JsonProperty("gzip")
    public java.lang.String getGzip() {
        return gzip;
    }

    @JsonProperty("gzip")
    public void setGzip(java.lang.String gzip) {
        this.gzip = gzip;
    }

    public ConvertPairedEndLibraryParams withGzip(java.lang.String gzip) {
        this.gzip = gzip;
        return this;
    }

    @JsonProperty("interlaced")
    public java.lang.String getInterlaced() {
        return interlaced;
    }

    @JsonProperty("interlaced")
    public void setInterlaced(java.lang.String interlaced) {
        this.interlaced = interlaced;
    }

    public ConvertPairedEndLibraryParams withInterlaced(java.lang.String interlaced) {
        this.interlaced = interlaced;
        return this;
    }

    @JsonAnyGetter
    public Map<java.lang.String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(java.lang.String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public java.lang.String toString() {
        return ((((((((((("ConvertPairedEndLibraryParams"+" [workspaceName=")+ workspaceName)+", readLibraries=")+ readLibraries)+", gzip=")+ gzip)+", interlaced=")+ interlaced)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
