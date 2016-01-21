
# MAKE DATASET 

# DATASET

DATASET_INPUT_PATH_PROPERTY = "DATASET_INPUT_PATH" 
DATASET_1_FILE_PROPERTY = "DATASET_1_FILE"
DATASET_2_FILE_PROPERTY = "DATASET_2_FILE"
DATASET_1_INDEX_COL_PROPERTY = "DATASET_1_INDEX_COL"
DATASET_2_INDEX_COL_PROPERTY = "DATASET_2_INDEX_COL"
DATASET_OUTPUT_PROPERTY = "DATASET_OUTPUT"
DATASET_1_LENGTH_PROPERTY = "DATASET_1_LENGTH"
DATASET_2_LENGTH_PROPERTY  = "DATASET_2_LENGTH"


# PREPARATION OF LIST TO GIVE TO ENSEMBL


LIST_FILE_GENE_DATASET_1_PROPERTY = "LIST_FILE_GENE_DATASET_1"
LIST_FILE_PROTEIN_DATASET_1_PROPERTY = "LIST_FILE_PROTEIN_DATASET_1"
LIST_GENE_INDEX_COL_PROPERTY = "LIST_GENE_INDEX_COL"
LIST_PROTEIN_INDEX_COL_PROPERTY = "LIST_PROTEIN_INDEX_COL"



# ACCESS TO ENSEMBL
ENSEMBL_OUTPUT_PATH_SEQUENCE_PROPERTY = "ENSEMBL_OUTPUT_PATH_SEQUENCE"
ENSEMBL_TYPE_QUERY_DATASET_1_PROPERTY = "ENSEMBL_TYPE_QUERY_DATASET_1"
ENSEMBL_TYPE_QUERY_DATASET_2_PROPERTY = "ENSEMBL_TYPE_QUERY_DATASET_2"
ENSEMBL_FILE_SEQUENCES_1_PROPERTY = "ENSEMBL_FILE_SEQUENCES_1"
ENSEMBL_FILE_SEQUENCES_2_PROPERTY = "ENSEMBL_FILE_SEQUENCES_2"




# DICTIONARY 
DICTIONARY_PATH_OUTPUT_PROPERTY = "DICTIONARY_PATH_OUTPUT"
DICTIONARY_NAME_FILE_PROPERTY = "DICTIONARY_NAME_FILE"




# SELECTION OF LONGEST PROTEIN

LONGEST_PROT_FILE_SEQUENCES_2_PROPERTY = "LONGEST_PROT_FILE_SEQUENCES_2"
LONGEST_PATH_SEQUENCE_PROPERTY = "LONGEST_PATH_SEQUENCE"
LONGEST_PATH_DICTIONARY_PROPERTY = "LONGEST_PATH_DICTIONARY"
LONGEST_DICTIONARY_NAME_FILE_PROPERTY = "LONGEST_DICTIONARY_NAME_FILE"
LONGEST_PATH_OUTPUT_PROPERTY = "LONGEST_PATH_OUTPUT"
LONGEST_FILE_PROPERTY = "LONGEST_FILE"
ISOFORM_FILE_PROPERTY = "ISOFORM_FILE"

# RANDOM SELECTION ISOFORM

RANDOM_ISOFORM_SEQ_PROPERTY = "RANDOM_ISOFORM_SEQ"


# FILE FUSION

FUSION_PATH_INPUT_PROPERTY = "FUSION_PATH_INPUT"
LONGEST_FILE_PROPERTY = "LONGEST_FILE"
SELECTED_ISOFORM_FILE_PROPERTY = "SELECTED_ISOFORM_FILE"
FUSION_FILE_SEQ_DATASET_2_PROPERTY = "FUSION_FILE_SEQ_DATASET_2"
FUSION_PATH_INPUT_DATASET_1_PROPERTY = "FUSION_PATH_INPUT_DATASET_1"
FUSION_FILE_DATASET_1_PROPERTY = "FUSION_FILE_DATASET_1"
FUSION_PATH_OUTPUT_PROPERTY = "FUSION_PATH_OUTPUT"
FUSION_DATASET_12_PROPERTY = "FUSION_DATASET_12"
FUSION_FILE_SEQ_DATASET_1_TEST_PROPERTY = "FUSION_FILE_SEQ_DATASET_1_TEST"



# DELETION FILE

DEL_ENSEMBL_PATH_PROPERTY = "DEL_ENSEMBL_PATH"
DEL_ENSEMBL_FILE1_PROPERTY = "DEL_ENSEMBL_FILE1"
DEL_ENSEMBL_FILE2_PROPERTY = "DEL_ENSEMBL_FILE2"


DEL_LONGEST_PATH_PROPERTY = "DEL_LONGEST_PATH"
DEL_LONGEST_FILE_PROPERTY = "DEL_LONGEST_FILE" 
DEL_ISOFORM_FILE_PROPERTY = "DEL_ISOFORM_FILE"
DEL_RANDOM_ISOFORM_FILE_PROPERTY = "DEL_RANDOM_ISOFORM_FILE"

DEL_FUSION_PATH_PROPERTY = "DEL_FUSION_PATH"
DEL_FUSION_DATASET_LONGEST_PROPERTY = "DEL_FUSION_DATASET_LONGEST"
DEL_FUSION_DATASET12_PROPERTY = "DEL_FUSION_DATASET12"


# END MAKEDATASET




# DISORDER ANALYSIS

# HEADER CHANGE

HEADER_INPUT_SEQ_PROPERTY = "HEADER_INPUT_SEQ" 
HEADER_FILE_SEQ_PROPERTY = "HEADER_FILE_SEQ"
HEADER_OUTPUT_SEQ_PROPERTY = "HEADER_OUTPUT_SEQ"
HEADER_FILE_OUTPUT_PROPERTY = "HEADER_FILE_OUTPUT"
HEADER_SOURCE_PROPERTY = "HEADER_SOURCE"
HEADER_TYPE_ID_PROPERTY = "HEADER_TYPE_ID"


# SPLIT IN MANY SEQUENCE FILE
SPLIT_PATH_INPUT_PROPERTY = "SPLIT_PATH_INPUT"
SPLIT_DATASET_PROPERTY = "SPLIT_DATASET"
SPLIT_PATH_OUTPUT_PROPERTY = "SPLIT_PATH_OUTPUT"
SPLIT_START_HEADER_PROPERTY = "SPLIT_START_HEADER"
SPLIT_END_HEADER_PROPERTY = "SPLIT_END_HEADER"


# TOOLS
# ANCHOR and IUPRED ANALYSIS
TOOL_PATH_INPUT_PROPERTY = "TOOL_PATH_INPUT"
ANCHOR_MOTIF_PATH_PROPERTY = "ANCHOR_MOTIF_PATH"
ANCHOR_PATH_OUTPUT_PROPERTY = "ANCHOR_PATH_OUTPUT"
IUPRED_PATH_OUTPUT_PROPERTY = "IUPRED_PATH_OUTPUT"


# ANALYSIS TOOLS
ANALYSIS_INPUT_PATH_IUPRED_PROPERTY =  "ANALYSIS_INPUT_PATH_IUPRED"
ANALYSIS_OUTPUT_PATH_TOOLS_PROPERTY =   "ANALYSIS_OUTPUT_PATH_TOOLS"
ANALYSIS_INPUT_PATH_ANCHOR_PROPERTY =  "ANALYSIS_INPUT_PATH_ANCHOR"
ANALYSIS_THRESHOLD_1_PROPERTY = "ANALYSIS_THRESHOLD_1"
ANALYSIS_THRESHOLD_2_PROPERTY = "ANALYSIS_THRESHOLD_2"
ANALYSIS_AMINOACID_NUMBER_IUPRED_PROPERTY = "ANALYSIS_AMINOACID_NUMBER_IUPRED"
ANALYSIS_AMINOACID_NUMBER_ANCHOR_PROPERTY = "ANALYSIS_AMINOACID_NUMBER_ANCHOR"
ANALYSIS_DATASET_TYPE_PROPERTY = "ANALYSIS_DATASET_TYPE"


# DISORDPBIND
DISO_INPUT_FILE_PROPERTY = "DISO_INPUT_FILE"
DISO_OUTPUT_FOLDER_PROPERTY = "DISO_OUTPUT_FOLDER"
DISO_BINDING_PARTNER_PROPERTY = "DISO_BINDING_PARTNER"
DISO_NUM_AA_PROPERTY = "DISO_NUM_AA"
DISO_DATASET_TYPE_PROPERTY = "DISO_DATASET_TYPE"


# SPECIFIC ANALYSIS TOOLS
SPECIFIC_INPUT_ANCHOR_FILE_PROPERTY = "SPECIFIC_INPUT_ANCHOR_FILE"
SPECIFIC_INPUT_IUPRED_FILE_PROPERTY = "SPECIFIC_INPUT_IUPRED_FILE"
SPECIFIC_INPUT_DISORDP_FILE_PROPERTY = "SPECIFIC_INPUT_DISORDP_FILE"
SPECIFIC_INPUT_DIR_FILE_PROPERTY =  "SPECIFIC_INPUT_DIR_FILE"
SPECIFIC_LIST_NAMEFILE_PROPERTY = "SPECIFIC_LIST_NAMEFILE"
SPECIFIC_OUTPUT_DIR_PROPERTY = "SPECIFIC_OUTPUT_DIR"
SPECIFIC_PROTEIN_LIST_COLUMN_PROPERTY = "SPECIFIC_PROTEIN_LIST_COLUMN"


# END DISORDER ANALYSIS


# DOWNLOAD ENSEMBL SEQ 

DOWNLOAD_ENSEMBL_FILE_INPUT_LIST_PROPERTY = "DOWNLOAD_ENSEMBL_FILE_INPUT_LIST"
DOWNLOAD_ENSEMBL_FILE_OUPUT_SEQ_PROPERTY = "DOWNLOAD_ENSEMBL_FILE_OUPUT_SEQ"
DOWNLOAD_ENSEMBL_TYPE_QUERY_PROPERTY = "DOWNLOAD_ENSEMBL_TYPE_QUERY"

DOWNLOAD_DICTIONARY_INPUT_FILE_PROPERTY = "DOWNLOAD_DICTIONARY_INPUT_FILE"
DOWNLOAD_DICTIONARY_OUTPUT_PATH_PROPERTY = "DOWNLOAD_DICTIONARY_OUTPUT_PATH"
DOWNLOAD_DICTIONARY_FILE_OUTPUT_PROPERTY = "DOWNLOAD_DICTIONARY_FILE_OUTPUT"


DOWNLOAD_LONGEST_SEQ_INPUT_FILE_PROPERTY = "DOWNLOAD_LONGEST_SEQ_INPUT_FILE"
DOWNLOAD_LONGEST_DICTIONARY_PROPERTY = "DOWNLOAD_LONGEST_DICTIONARY"
DOWNLOAD_LONGEST_SEQ_OUTPUT_PATH_PROPERTY = "DOWNLOAD_LONGEST_SEQ_OUTPUT_PATH"
DOWNLOAD_LONGEST_SEQ_FILE_PROPERTY = "DOWNLOAD_LONGEST_SEQ_FILE"
DOWNLOAD_LONGEST_ISOFORM_FILE = "DOWNLOAD_LONGEST_ISOFORM_FILE"


DOWNLOAD_ISOFORM_FILE_PATH_PROPERTY = "DOWNLOAD_ISOFORM_FILE_PATH"
DOWNLOAD_RANDOM_FILE_PATH_PROPERTY = "DOWNLOAD_RANDOM_FILE_PATH"

DOWNLOAD_FUSION_FILE_LONGEST_PROPERTY = "DOWNLOAD_FUSION_FILE_LONGEST"
DOWNLOAD_FUSION_FILE_RANDOM_PROPERTY = "DOWNLOAD_FUSION_FILE_RANDOM"
DOWNLOAD_FUSION_FINAL_DATASET_PROPERTY = "DOWNLOAD_FUSION_FINAL_DATASET"




# PUTATIVE RNA TARGET 
# JPROTEOMICS
PUTATIVERNA_JPROTEOMICS_SEQ_PROPERTY = "PUTATIVERNA_JPROTEOMICS_SEQ"
PUTATIVERNA_JPROTEOMICS_INFO_PROPERTY = "PUTATIVERNA_JPROTEOMICS_INFO"
PUTATIVE_MRNA_GENE_JPROTEOMICS_PROPERTY =  "PUTATIVE_MRNA_GENE_JPROTEOMICS"
PUTATIVE_RBPDB_GENE_JPROTEOMICS_PROPERTY = "PUTATIVE_RBPDB_GENE_JPROTEOMICS"

# NATREVGENTICS
PUTATIVERNA_NATREVGENETICS_SEQ_PROPERTY = "PUTATIVERNA_NATREVGENETICS_SEQ"
PUTATIVE_RNA_NATREVGENETICS_INFO_PROPERTY = "PUTATIVE_RNA_NATREVGENETICS_INFO"
PUTATIVE_RNA_OUTPUT_PROPERTY = "PUTATIVE_RNA_OUTPUT"
PUTATIVE_RNA_TARGET_DATASET_NAME_PROPERTY = "PUTATIVE_RNA_TARGET_DATASET_NAME"
PUTATIVE_ALL_RNA_TARGET_PROPERTY = "PUTATIVE_ALL_RNA_TARGET"

# domain

DOMAIN_LIST_FILE_PROPERTY = "DOMAIN_LIST_FILE"
DOMAIN_LIST_JPROTEOMICS_PROPERTY = "DOMAIN_LIST_JPROTEOMICS"
DOMAIN_FILE_PFAM_PROPERTY = "DOMAIN_FILE_PFAM"
DOMAIN_FINAL_TABLE_JPROT_PROPERTY = "DOMAIN_FINAL_TABLE_JPROT"
DOMAIN_LIST_NATREVGENETICS_PROPERTY = "DOMAIN_LIST_NATREVGENETICS"
DOMAIN_FINAL_TABLE_NATREVGENETICS = "DOMAIN_FINAL_TABLE_NATREVGENETICS"
DOMAIN_FILE_SEQ_PROPERTY = "DOMAIN_FILE_SEQ"
DOMAIN_FINALE_TABLE_RBP_DATASET_PROPERTY = "DOMAIN_FINALE_TABLE_RBP_DATASET"


