from fr.tagc.rainet.core.util import Constants
from fr.tagc.rainet.core.data import DataConstants

#===============================================================================
# The list of available strageties
#===============================================================================
STRATEGIES_LIST = [ "Insertion", "InteractiveQuery", "Analysis", "DatabaseCheck"]

#===============================================================================
# The tags used to define the options
#===============================================================================
SHORT_TAG = "short"
LONG_TAG = "long"
ACTION_TAG = "action"
TYPE_TAG = "type"
DEST_TAG = "dest"
DEFAULT_TAG = "default"
HELP_TAG = "help"

#===============================================================================
# The name of the various options
#===============================================================================
# Common options
OPTION_DB_NAME = "databasePath"
OPTION_SPECIES = "species"
OPTION_VERBOSITY = "verbose"
# Insertion strategy options
OPTION_INSERTION_PROPERTIES_PATH = "insertionPropertiesPath"
OPTION_INSERTION_FORCE_OVERRIDE = "insertionForceOverride"
# InteractiveQuery Strategy options
OPTION_QUERY_FILE = "query_file"
# Analysis Strategy options
OPTION_MINIMUM_INTERACTION_SCORE = "interaction_score"
OPTION_TRANSCRIPT_BIOTYPE = "transcript_biotype"
OPTION_LNCRNA_BIOTYPES = "lncRNA_biotypes"
OPTION_GENCODE = "gencode_basic"

#===============================================================================
# Constants for analysis strategy
#===============================================================================

DEFAULT_BIOTYPE = "RNA"
DEFAULT_LNCRNA_BIOTYPES = "OFF"
DEFAULT_INTERACTION_SCORE = "OFF"
DEFAULT_GENCODE = 0

BIOTYPE_LNCRNA = "LncRNA"
BIOTYPE_MRNA = "MRNA"
BIOTYPE_OTHERRNA = "OtherRNA"
TRANSCRIPT_BIOTYPES = { DEFAULT_BIOTYPE, BIOTYPE_LNCRNA, BIOTYPE_MRNA, BIOTYPE_OTHERRNA }
LNCRNA_BIOTYPES = DataConstants.RNA_LNCRNA_BIOTYPE


#===============================================================================
# The definition of the options
#===============================================================================
OPTION_LIST = {  "Insertion": [
                    [ "-d", "--databasePath", "store", "string", OPTION_DB_NAME, None, "The path to the SQL database to use/create."],
                    [ "-s", "--species", "store", "string", OPTION_SPECIES, None, "The species used in the database."],
                    [ "-v", "--verbose", "store", "string", OPTION_VERBOSITY, Constants.MODE_INFO, "The level of verbosity. Must be one of : " + str( Constants.VERBOSITY_LEVELS)],
                    [ "-i", "--insertionPropertiesPath", "store", "string", OPTION_INSERTION_PROPERTIES_PATH, None, "The path to the properties file containing the list of files to use for DB insertion."],
                    [ "-f", "--forceOverride", "store_true", None, OPTION_INSERTION_FORCE_OVERRIDE, None, "Indicates if the whole database must be dropped and re-inserted or not."],
                ], 
                 "InteractiveQuery":[
                    [ "-d", "--databasePath", "store", "string", OPTION_DB_NAME, None, "The path to the SQL database to use/create."],
                    [ "-s", "--species", "store", "string", OPTION_SPECIES, None, "The species used in the database."],
                    [ "-q", "--queryFilePath", "store", "string", OPTION_QUERY_FILE, None, "The path to the file containing the query definition."],                 
                ],               
                "Analysis" : [
                    [ "-d", "--databasePath", "store", "string", OPTION_DB_NAME, None, "The path to the SQL database to use/create."],
                    [ "-s", "--species", "store", "string", OPTION_SPECIES, None, "The species used in the database."],
                    [ "-v", "--verbose", "store", "string", OPTION_VERBOSITY, Constants.MODE_INFO, "The level of verbosity. Must be one of : " + str( Constants.VERBOSITY_LEVELS)],
                    [ "-m", "--minimumInteractionScore", "store", "string", OPTION_MINIMUM_INTERACTION_SCORE, DEFAULT_INTERACTION_SCORE, "Protein-RNA interactions with interaction score below given value will be excluded from analysis. Default: OFF"],
                    [ "-b", "--transcriptBiotype", "store", "string", OPTION_TRANSCRIPT_BIOTYPE, DEFAULT_BIOTYPE, "General transcript biotype to be INCLUDED in analysis. Default = RNA (i.e. any type of RNA). Can be one of :"+ str(TRANSCRIPT_BIOTYPES)],
                    [ "-l", "--lncRNABiotype", "store", "string", OPTION_LNCRNA_BIOTYPES, DEFAULT_LNCRNA_BIOTYPES, "Comma-separated list of lncRNA subtypes to be INCLUDED in analysis. Default: OFF (i.e. all subtypes are considered). Can one or several of :"+ str(LNCRNA_BIOTYPES)],
                    [ "-g", "--gencodeBasicOnly", "store", "int", OPTION_GENCODE, DEFAULT_GENCODE, "If 1, include in analysis ONLY transcripts tagged as present in 'GENCODE basic'. Default: 0 (i.e. all RNAs are considered)."]
                ],
                "DatabaseCheck" : [
                    [ "-d", "--databasePath", "store", "string", OPTION_DB_NAME, None, "The path to the SQL database to use/create."],
                    [ "-v", "--verbose", "store", "string", OPTION_VERBOSITY, Constants.MODE_INFO, "The level of verbosity. Must be one of : " + str( Constants.VERBOSITY_LEVELS)]
                ]
               }
