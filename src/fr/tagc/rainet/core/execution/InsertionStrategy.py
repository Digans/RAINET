
import shutil
import os
from os.path import basename

from fr.tagc.rainet.core.data import DataConstants
from fr.tagc.rainet.core.data.TableStatus import TableStatus
from fr.tagc.rainet.core.execution.ExecutionStrategy import ExecutionStrategy
from fr.tagc.rainet.core.util import Constants
from fr.tagc.rainet.core.util.exception.RainetException import RainetException
from fr.tagc.rainet.core.util.log.Logger import Logger
from fr.tagc.rainet.core.util.option import OptionConstants
from fr.tagc.rainet.core.util.option.OptionManager import OptionManager
from fr.tagc.rainet.core.util.parser.FastaParser import FastaParser
from fr.tagc.rainet.core.util.parser.NetworkModuleAnnotationParser import NetworkModuleAnnotationParser
from fr.tagc.rainet.core.util.parser.NetworkModuleParser import NetworkModuleParser
from fr.tagc.rainet.core.util.parser.OboParser import OboParser
from fr.tagc.rainet.core.util.parser.TSVParser import TSVParser
from fr.tagc.rainet.core.util.sql.SQLManager import SQLManager
from fr.tagc.rainet.core.util.sql.SQLUtil import SQLUtil
from fr.tagc.rainet.core.util.time.Timer import Timer
from fr.tagc.rainet.core.util.property.PropertyManager import PropertyManager
from fr.tagc.rainet.core.util.data.DataManager import DataManager

from fr.tagc.rainet.core.data.PPINetwork import PPINetwork
from fr.tagc.rainet.core.data.PPINetworkInteraction import PPINetworkInteraction

from fr.tagc.rainet.core.data.RNA import RNA
from fr.tagc.rainet.core.data.RNACrossReference import RNACrossReference
from fr.tagc.rainet.core.data.MRNA import MRNA
from fr.tagc.rainet.core.data.LncRNA import LncRNA
from fr.tagc.rainet.core.data.OtherRNA import OtherRNA
from fr.tagc.rainet.core.data.ProteinRNAInteractionCatRAPID import ProteinRNAInteractionCatRAPID
from fr.tagc.rainet.core.data.ProteinCrossReference import ProteinCrossReference
from fr.tagc.rainet.core.data.RNATissueExpression import RNATissueExpression
from fr.tagc.rainet.core.data.Tissue import Tissue
from fr.tagc.rainet.core.data.InteractingRNA import InteractingRNA
from fr.tagc.rainet.core.data.InteractingProtein import InteractingProtein
from fr.tagc.rainet.core.data.BioplexCluster import BioplexCluster
from fr.tagc.rainet.core.data.ProteinBioplexAnnotation import ProteinBioplexAnnotation
from fr.tagc.rainet.core.data.WanCluster import WanCluster
from fr.tagc.rainet.core.data.ProteinWanAnnotation import ProteinWanAnnotation
from fr.tagc.rainet.core.data.CorumCluster import CorumCluster
from fr.tagc.rainet.core.data.ProteinCorumAnnotation import ProteinCorumAnnotation
from fr.tagc.rainet.core.data.CustomCluster import CustomCluster
from fr.tagc.rainet.core.data.ProteinCustomAnnotation import ProteinCustomAnnotation


# #
# This class define the Strategy executing insertion of the various data in database
class InsertionStrategy( ExecutionStrategy ):
    

    # #
    # The Strategy execution method
    def execute( self ):
        
        self.DBPath = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_NAME )
        self.forceOverride = OptionManager.get_instance().get_option( OptionConstants.OPTION_INSERTION_FORCE_OVERRIDE )
        self.insert_data()

    
    # #
    # Insert the various data to the Database using file defined in the configuration file
    #
    def insert_data( self):
        
        # Create Logger instance by using the first log action.
        Logger.get_instance().info( "InsertionStrategy.insert_data: Starting..." )
        
#         # Backup the database file
#         try:
#             Logger.get_instance().info( "InsertionStrategy.insert_data:   Backuping DB file..." )
#             shutil.copyfile(self.DBPath, self.DBPath + ".back")
#         except IOError as ioe:
#             Logger.get_instance().info( " warning : Unable to backup database file : " + self.DBPath + " : " + str( ioe))
        
        # Create database sqlite file at the provided path
        SQLManager.get_instance().build_database( self.DBPath, self.forceOverride )
        
        self.check_database_tables()
        
        # Retrieve the inertion properties
        PropertyManager.get_instance().read_properties( OptionManager.get_instance().get_option( OptionConstants.OPTION_INSERTION_PROPERTIES_PATH, True))
        
        # Start chrono
        Timer.get_instance().start_chrono()
        
        # Indicate insertion mode
        if self.forceOverride:
            Logger.get_instance().info( " -- MODE FORCE OVERRIDE -- " )
        else:
            Logger.get_instance().info( " -- MODE RESUME -- " )
        
        #=======================================================================
        # INSERTION OF DATA
        #=======================================================================
        try:
 
            #===================================================================
            # PROTEIN DEFINITION
            #===================================================================
               
            # Parse the protein file
            input_file = PropertyManager.get_instance().get_property( DataConstants.PROTEIN_UNIPROT_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, True, DataConstants.PROTEIN_HEADERS, DataConstants.PROTEIN_CLASS, DataConstants.PROTEIN_PARAMS, None, DataConstants.PROTEIN_COMMENT_CHAR )
    
            # Parse the protein cross references file
            input_file = PropertyManager.get_instance().get_property( DataConstants.PROTEIN_CROSSREFERENCES_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.PROTEIN_CROSS_REFERENCE_HEADERS, DataConstants.PROTEIN_CROSS_REFERENCE_CLASS, DataConstants.PROTEIN_CROSS_REFERENCE_PARAMS, None, DataConstants.PROTEIN_CROSS_REFERENCE_COMMENT_CHAR )
    
            # Parse the protein isoform file
            input_file = PropertyManager.get_instance().get_property( DataConstants.PROTEIN_ISOFORMS_PROPERTY, True)
            self.launch_insertion_Fasta( input_file, DataConstants.ISOFORM_CLASS, DataConstants.ISOFORM_REGULAR_EXPRESSION, DataConstants.ISOFORM_GROUPS, DataConstants.ISOFORM_PARAMS, DataConstants.ISOFORM_PARAMS_VALUE_ALTERNATIVE, DataConstants.ISOFORM_COMMENT_CHAR )
                
            # Parse the protein domain file of SMART DB
            input_file = PropertyManager.get_instance().get_property( DataConstants.PROTEIN_DOMAIN_SMART_PROPERTY, True)
            self.launch_insertion_TSV( input_file, True, DataConstants.PROTEIN_DOMAIN_HEADERS_SMART, DataConstants.PROTEIN_DOMAIN_CLASS, DataConstants.PROTEIN_DOMAIN_PARAM_SMART, DataConstants.PROTEIN_DOMAIN_VALUE_SMART, DataConstants.PROTEIN_DOMAIN_COMMENT_CHAR, "SMART" , False)
                
            # Parse the protein domain file of PFAM DB
            input_file = PropertyManager.get_instance().get_property( DataConstants.PROTEIN_DOMAIN_PFAM_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.PROTEIN_DOMAIN_HEADERS_PFAM, DataConstants.PROTEIN_DOMAIN_CLASS, DataConstants.PROTEIN_DOMAIN_PARAM_PFAM, DataConstants.PROTEIN_DOMAIN_VALUE_PFAM, DataConstants.PROTEIN_DOMAIN_COMMENT_CHAR, "PFAM", False )
    
            #===================================================================
            # FUNCTION AND PATHWAY ANNOTATIONS
            #===================================================================
    
            # Parse the Gene Ontology file
            input_file = PropertyManager.get_instance().get_property( DataConstants.GENE_ONTOLOGY_DEFINITION_PROPERTY, True)
            self.launch_insertion_Obo( input_file, DataConstants.GENE_ONTOLOGY_CLASS, DataConstants.GENE_ONTOLOGY_ID_TAG, DataConstants.GENE_ONTOLOGY_NAME_TAG, DataConstants.GENE_ONTOLOGY_NAMESPACE_TAG )
                
            # Parse the Protein Gene Ontology annotation file
            input_file = PropertyManager.get_instance().get_property( DataConstants.GENE_ONTOLOGY_ANNOTATION_PROPERTY, True)    
            self.launch_insertion_TSV( input_file, False, DataConstants.PROTEIN_GO_ANNOTATION_HEADERS, DataConstants.PROTEIN_GO_ANNOTATION_CLASS, DataConstants.PROTEIN_GO_ANNOTATION_PARAMS, None, DataConstants.PROTEIN_GO_ANNOTATION_COMMENT_CHAR )
    
            # Parse the KEGG pathway file
            input_file = PropertyManager.get_instance().get_property( DataConstants.KEGG_PATHWAY_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, True, DataConstants.KEGG_PATHWAY_HEADERS, DataConstants.KEGG_PATHWAY_CLASS, DataConstants.KEGG_PATHWAY_PARAMS, None, DataConstants.KEGG_PATHWAY_COMMENT_CHAR )
                
            # Parse the Protein KEGG Pathway annotation file
            input_file = PropertyManager.get_instance().get_property( DataConstants.KEGG_PATHWAY_ANNOTATION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, True, DataConstants.KEGG_PATHWAY_ANNOTATION_HEADERS, DataConstants.KEGG_PATHWAY_ANNOTATION_CLASS, DataConstants.KEGG_PATHWAY_ANNOTATION_PARAMS, None, DataConstants.KEGG_PATHWAY_ANNOTATION_COMMENT_CHAR )
                
            #===================================================================
            # REACTOME
            #===================================================================
    
            # Parse the Reactome pathway file
            input_file = PropertyManager.get_instance().get_property( DataConstants.REACTOME_PATHWAY_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.REACTOME_PATHWAY_HEADERS, DataConstants.REACTOME_PATHWAY_CLASS, DataConstants.REACTOME_PATHWAY_PARAMS, None, DataConstants.REACTOME_PATHWAY_COMMENT_CHAR )
                
            # Parse the Protein Reactome Pathway annotation file
            input_file = PropertyManager.get_instance().get_property( DataConstants.REACTOME_PATHWAY_ANNOTATION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.REACTOME_PATHWAY_ANNOTATION_HEADERS, DataConstants.REACTOME_PATHWAY_ANNOTATION_CLASS, DataConstants.REACTOME_PATHWAY_ANNOTATION_PARAMS, None, DataConstants.REACTOME_PATHWAY_ANNOTATION_COMMENT_CHAR )
    
            #===================================================================
            # BIOPLEX
            #===================================================================   
    
            # Parse the file listing Bioplex clusters
            input_file = PropertyManager.get_instance().get_property( DataConstants.BIOPLEX_CLUSTER_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.BIOPLEX_CLUSTER_HEADERS,
                                       DataConstants.BIOPLEX_CLUSTER_CLASS, DataConstants.BIOPLEX_CLUSTER_PARAMS,
                                        None, DataConstants.BIOPLEX_CLUSTER_COMMENT_CHAR )

            # Parse the file with Bioplex annotations
            input_file = PropertyManager.get_instance().get_property( DataConstants.BIOPLEX_ANNOTATION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.BIOPLEX_ANNOTATION_HEADERS,
                                       DataConstants.BIOPLEX_ANNOTATION_CLASS, DataConstants.BIOPLEX_ANNOTATION_PARAMS,
                                        None, DataConstants.BIOPLEX_ANNOTATION_COMMENT_CHAR )

            #===================================================================
            # WAN CLUSTERS
            #===================================================================   
    
            # Parse the file listing Wan clusters
            input_file = PropertyManager.get_instance().get_property( DataConstants.WAN_CLUSTER_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.WAN_CLUSTER_HEADERS,
                                       DataConstants.WAN_CLUSTER_CLASS, DataConstants.WAN_CLUSTER_PARAMS,
                                        None, DataConstants.WAN_CLUSTER_COMMENT_CHAR )

            # Parse the file with Wan annotations
            input_file = PropertyManager.get_instance().get_property( DataConstants.WAN_ANNOTATION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.WAN_ANNOTATION_HEADERS,
                                       DataConstants.WAN_ANNOTATION_CLASS, DataConstants.WAN_ANNOTATION_PARAMS,
                                        None, DataConstants.WAN_ANNOTATION_COMMENT_CHAR )


            #===================================================================
            # CORUM CLUSTERS
            #===================================================================   
    
            # Parse the file listing Corum clusters
            input_file = PropertyManager.get_instance().get_property( DataConstants.CORUM_CLUSTER_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.CORUM_CLUSTER_HEADERS,
                                       DataConstants.CORUM_CLUSTER_CLASS, DataConstants.CORUM_CLUSTER_PARAMS,
                                        None, DataConstants.CORUM_CLUSTER_COMMENT_CHAR )

            # Parse the file with Corum annotations
            input_file = PropertyManager.get_instance().get_property( DataConstants.CORUM_ANNOTATION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.CORUM_ANNOTATION_HEADERS,
                                       DataConstants.CORUM_ANNOTATION_CLASS, DataConstants.CORUM_ANNOTATION_PARAMS,
                                        None, DataConstants.CORUM_ANNOTATION_COMMENT_CHAR )

            #===================================================================
            # CUSTOM CLUSTERS
            #===================================================================   
            
            # Parse the file listing Custom clusters
            input_file = PropertyManager.get_instance().get_property( DataConstants.CUSTOM_CLUSTER_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.CUSTOM_CLUSTER_HEADERS,
                                       DataConstants.CUSTOM_CLUSTER_CLASS, DataConstants.CUSTOM_CLUSTER_PARAMS,
                                        None, DataConstants.CUSTOM_CLUSTER_COMMENT_CHAR )
            
            # Parse the file with Custom annotations
            input_file = PropertyManager.get_instance().get_property( DataConstants.CUSTOM_ANNOTATION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.CUSTOM_ANNOTATION_HEADERS,
                                       DataConstants.CUSTOM_ANNOTATION_CLASS, DataConstants.CUSTOM_ANNOTATION_PARAMS,
                                        None, DataConstants.CUSTOM_ANNOTATION_COMMENT_CHAR )
    
    
            #===================================================================
            # INTERACTOME
            #===================================================================
                
            # Parse the protein interaction file
            input_file = PropertyManager.get_instance().get_property( DataConstants.INTERACTOME_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.INTERACTOME_HEADER, DataConstants.INTERACTOME_CLASS, DataConstants.INTERACTOME_PARAMS, None, DataConstants.INTERACTOME_COMMENT_CHAR )
                
            # Parse the protein interaction network file
            input_file = PropertyManager.get_instance().get_property( DataConstants.INTERACTOME_NETWORK_DEFINITION_PROPERTY, True)
            ppi_default_values = [None, None, os.path.basename( input_file)]
            self.launch_insertion_TSV( input_file, False, DataConstants.INTERACTOME_NETWORK_HEADER, DataConstants.INTERACTOME_NETWORK_CLASS, DataConstants.INTERACTOME_NETWORK_PARAMS, ppi_default_values, DataConstants.INTERACTOME_NETWORK_COMMENT_CHAR )
                
            # Parse the Network Module file            
            input_file = PropertyManager.get_instance().get_property( DataConstants.INTERACTOME_NETWORK_PARTITION_DEFINITION_PROPERTY, True)
            self.launch_insertion_NetworkModule( input_file, DataConstants.INTERACTOME_NETWORK_PARTITION_CLASS, DataConstants.INTERACTOME_NETWORK_PARTITION_CLASS_TAG, DataConstants.INTERACTOME_NETWORK_PARTITION_COMMENT_CHAR )
                
            # Parse the Network Module Annotation file  
            input_file = PropertyManager.get_instance().get_property( DataConstants.INTERACTOME_NETWORK_PARTITION_ANNOTATION_PROPERTY, True)
            self.launch_insertion_NetworkModuleAnnotation( input_file, DataConstants.INTERACTOME_NETWORK_PARTITION_ANNOTATION_CLASS, DataConstants.INTERACTOME_NETWORK_PARTITION_ANNOTATION_CLASS_TAG, DataConstants.INTERACTOME_NETWORK_PARTITION_ANNOTATION_CLASS_REGEX, DataConstants.INTERACTOME_NETWORK_PARTITION_ANNOTATION_PROTEIN_TAG, DataConstants.INTERACTOME_NETWORK_PARTITION_ANNOTATION_ANNOTATION_TAG, DataConstants.INTERACTOME_NETWORK_PARTITION_COMMENT_CHAR )
                
            # Parse the protein redundancy file
            input_file = PropertyManager.get_instance().get_property( DataConstants.INTERACTOME_NETWORK_REDUNDANCY_DEFINITION_PROPERTY, True)
            interactome_network_redundancy_definition_value = [None, basename( input_file), None]
            self.launch_insertion_TSV( input_file, False, DataConstants.INTERACTOME_NETWORK_REDUNDANCY_DEFINITION_HEADERS, DataConstants.INTERACTOME_NETWORK_REDUNDANCY_DEFINITION_CLASS, DataConstants.INTERACTOME_NETWORK_REDUNDANCY_DEFINITION_PARAMS, interactome_network_redundancy_definition_value, DataConstants.INTERACTOME_NETWORK_REDUNDANCY_DEFINITION_COMMENT_CHAR, "Redundancy", False )
            
            #===================================================================
            # RNA DEFINITION
            #===================================================================

            # Make query of specific type of protein cross references to speed up insertion
            DataManager.get_instance().perform_query( DataConstants.PROTEIN_ENSP_XREF_KW,
                                                     "query( ProteinCrossReference.protein_id,ProteinCrossReference.crossReferenceID ).filter(ProteinCrossReference.sourceDB == DataConstants.PROTEIN_ENSP_XREF_DB).all()") 
            # Convert query into a dictionary
            DataManager.get_instance().query_to_dict( DataConstants.PROTEIN_ENSP_XREF_KW, 1, 0)
  
            # Parse the RNA file
            input_file = PropertyManager.get_instance().get_property( DataConstants.RNA_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, True, DataConstants.RNA_HEADERS, DataConstants.RNA_CLASS, DataConstants.RNA_PARAMS, None, DataConstants.RNA_COMMENT_CHAR )
    
            # Parse the RNA cross references file
            input_file = PropertyManager.get_instance().get_property( DataConstants.RNA_CROSS_REFERENCE_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.RNA_CROSS_REFERENCE_HEADERS, DataConstants.RNA_CROSS_REFERENCE_CLASS, DataConstants.RNA_CROSS_REFERENCE_PARAMS, None, DataConstants.RNA_CROSS_REFERENCE_COMMENT_CHAR )

            #===================================================================
            # RNA TISSUE EXPRESSION
            #===================================================================
  
            # Make query of all RNA IDs to speed up insertion
            DataManager.get_instance().perform_query( DataConstants.RNA_ALL_KW, "query( RNA ).all()") 
            # Format query into dict data structure
            DataManager.get_instance().query_to_object_dict( DataConstants.RNA_ALL_KW, "transcriptID")
 
            # Make query of all Protein IDs (uniprotAC) to speed up insertion
            DataManager.get_instance().perform_query( DataConstants.PROT_ALL_KW, "query( Protein ).all()") 
            # Format query into dict data structure
            DataManager.get_instance().query_to_object_dict( DataConstants.PROT_ALL_KW, "uniprotAC")

            # Parse the RNA tissue expression file
            input_file = PropertyManager.get_instance().get_property( DataConstants.RNA_TISSUE_EXPRESSION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, True, DataConstants.RNA_TISSUE_EXPRESSION_HEADERS, DataConstants.RNA_TISSUE_EXPRESSION_CLASS,
                                        DataConstants.RNA_TISSUE_EXPRESSION_PARAMS, DataConstants.RNA_TISSUE_EXPRESSION_VALUE,
                                        DataConstants.RNA_TISSUE_EXPRESSION_COMMENT_CHAR ) 


            #===================================================================
            # PROTEIN RNA INTERACTION
            #===================================================================

            self.forceOverride = 1
  
            # Parse the file listing RNA with catRAPID data
            input_file = PropertyManager.get_instance().get_property( DataConstants.INTERACTING_RNA_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, True, DataConstants.INTERACTING_RNA_DEFINITION_HEADERS,
                                       DataConstants.INTERACTING_RNA_DEFINITION_CLASS, DataConstants.INTERACTING_RNA_DEFINITION_PARAMS,
                                        None, DataConstants.INTERACTING_RNA_DEFINITION_COMMENT_CHAR )
   
    
   
            # Parse the file listing Proteins with catRAPID data
            input_file = PropertyManager.get_instance().get_property( DataConstants.INTERACTING_PROTEIN_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, True, DataConstants.INTERACTING_PROTEIN_DEFINITION_HEADERS,
                                       DataConstants.INTERACTING_PROTEIN_DEFINITION_CLASS, DataConstants.INTERACTING_PROTEIN_DEFINITION_PARAMS,
                                        None, DataConstants.INTERACTING_PROTEIN_DEFINITION_COMMENT_CHAR )
    
            # Initialize data items to store missing interactions
            if DataConstants.PROTEIN_RNA_INTERACTION_CATRAPID_MISSING_RNA_KW not in DataManager.get_instance().data:
                DataManager.get_instance().store_data(DataConstants.PROTEIN_RNA_INTERACTION_CATRAPID_MISSING_RNA_KW,[])
            if DataConstants.PROTEIN_RNA_INTERACTION_CATRAPID_MISSING_PROT_KW not in DataManager.get_instance().data:
                DataManager.get_instance().store_data(DataConstants.PROTEIN_RNA_INTERACTION_CATRAPID_MISSING_PROT_KW,[])
               
            # Parse the ProteinRNAInteractionCatRAPID file
            input_file = PropertyManager.get_instance().get_property( DataConstants.PROTEIN_RNA_INTERACTION_CATRAPID_DEFINITION_PROPERTY, True)
            self.launch_insertion_TSV( input_file, False, DataConstants.PROTEIN_RNA_INTERACTION_CATRAPID_HEADERS,
                                       DataConstants.PROTEIN_RNA_INTERACTION_CATRAPID_CLASS, DataConstants.PROTEIN_RNA_INTERACTION_CATRAPID_PARAMS,
                                        None, DataConstants.PROTEIN_RNA_INTERACTION_CATRAPID_COMMENT_CHAR )
   
            self.forceOverride = 0
  
              
            # Remove data that will no longer be used to reduce memory usage 
            DataManager.get_instance().delete_data(DataConstants.PROTEIN_ENSP_XREF_KW)
            DataManager.get_instance().delete_data(DataConstants.RNA_ALL_KW)
            DataManager.get_instance().delete_data(DataConstants.PROT_ALL_KW)
           
            
        except RainetException as re:
            Logger.get_instance().error( re.to_string() )
            Timer.get_instance().stop_chrono( "ERROR : Data insertion FAILED" )
            return

        # # Report on potential missing data
        # self.check_missing_data()

        
        # Stop the chrono      
        Timer.get_instance().stop_chrono( "Data insertion finished" )
    

    # #
    # Insert data linked to a TSV (tab separated) file
    #
    # @param file_path : string - The path to the data file
    # @param has_headers : boolean - Indicates if the file has a header line as first line
    # @param headers : list<string> - the list of headers name
    # @param class_name : string - The name of the class to be used to instantiate objects from data
    # @param params : list<string> - The list of parameters (header names) to use to instantiate objects from data
    # @param default_values : list<string> - the list of default values of the parameters
    # @param comment_char : string - the character used to declare comment lines in the data file
    # @param table_extension : string (optional) - Extension to add to the class name to declare a particular sub-case in some classes
    # @param clean_table : boolean  - The information indicating if the related db table must be cleaned before insertion or not 
    #
    def launch_insertion_TSV( self, file_path, has_headers, headers, class_name, params, default_values, comment_char, table_extension = "", clean_table = True ):
        
        composite_table_name = class_name + table_extension
        
        try:
            # Start timing
            Timer.get_instance().step( "Inserting " + composite_table_name + ":" )
            # Check if the insertion is required not not, depending on the fact the data
            # were already inserted and theforceOverride option
            if SQLUtil.insert_data_required( class_name, self.forceOverride, table_extension ) :
                Logger.get_instance().info( "|--Starting insertion..." )
                status = TSVParser.parse_file( file_path, has_headers, headers, class_name, params, default_values, comment_char, clean_table )
            else:
                Logger.get_instance().info( "|--Data already inserted: insertion bypassed." )
                status = None
        # If an exception is raised by controlled code, status of insertion is set to "Rainet Error"
        except RainetException as re:
            Logger.get_instance().error( re.to_string())
            status = Constants.STATUS_RAINET_ERROR
            raise re
        # If an exception is raised by uncontrolled code, status of insertion is set to "Error"
        except Exception as e:
            Logger.get_instance().error( e.message )
            status = Constants.STATUS_ERROR
            raise RainetException( "Abnormal Exception during insertion of " + class_name, e )
        # In all case insert or update the status of the insertion to TableStatus table in DB
        finally:
            if status != None:
                sql_session = SQLManager.get_instance().get_session()
                db_status_list = sql_session.query( TableStatus ).filter( TableStatus.tableName == composite_table_name ).all()
                if db_status_list == None or len( db_status_list) == 0:
                    sql_session.add( TableStatus( composite_table_name, status, file_path ) )
                else:
                    db_status = db_status_list[0]
                    db_status.tableStatus = status
                    sql_session.add( db_status )
                SQLManager.get_instance().commit()
    
    # # Insert data linked to a network module (.clas) file
    #
    # @param file_path : string - The path to the data file
    # @param class_name : string - The name of the class to be used to instantiate objects from data
    # @param class_tag : string - The tag used in file to declare a new network module
    # @param comment_char : string - the character used to declare comment lines in the data file
    # @param clean_table : boolean  - The information indicating if the related db table must be cleaned before insertion or not
    def launch_insertion_NetworkModule( self, file_path, class_name, class_tag, comment_char, clean_table = True ):
        
        try:
            Timer.get_instance().step( "Inserting " + class_name + ":" )
            if SQLUtil.insert_data_required( class_name, self.forceOverride ) :
                Logger.get_instance().info( "|--Starting insertion..." )
                status = NetworkModuleParser.parse_file( file_path, class_tag, comment_char, clean_table )
            else:
                Logger.get_instance().info( "|--Data already inserted: insertion bypassed." )
                status = None
        except RainetException as re:
            Logger.get_instance().error( re.to_string() )
            status = Constants.STATUS_RAINET_ERROR
            raise re
        except Exception as e:
            Logger.get_instance().error( e.message )
            status = Constants.STATUS_ERROR
            raise RainetException( "Abnormal Exception during insertion of " + class_name, e )
        finally:
            if status != None:
                sql_session = SQLManager.get_instance().get_session()
                db_status_list = sql_session.query( TableStatus ).filter( TableStatus.tableName == class_name ).all()
                if db_status_list == None or len( db_status_list) == 0:
                    sql_session.add( TableStatus( class_name, status, file_path ) )
                else:
                    db_status = db_status_list[0]
                    db_status.tableStatus = status
                    sql_session.add( db_status )
                SQLManager.get_instance().commit()
                
    # # Insert data linked to a network module annotation file
    #
    # @param file_path : string - The path to the data file
    # @param class_name : string - The name of the class to be used to instantiate objects from data
    # @param class_tag : string - The tag used in file to declare a new network module
    # @param protein_tag : string - The tag used in file to declare a protein list line
    # @param annotation_tag : string - The tag used in file to declare an annotation list line
    # @param comment_char : string - the character used to declare comment lines in the data file
    # @param clean_table : boolean  - The information indicating if the related db table must be cleaned before insertion or not
    def launch_insertion_NetworkModuleAnnotation( self, file_path, class_name, class_tag, class_regex, protein_tag, annotation_tag, comment_char, clean_table = True ):
        
        try:
            Timer.get_instance().step( "Inserting " + class_name + ":" )
            if SQLUtil.insert_data_required( class_name, self.forceOverride ) :
                Logger.get_instance().info( "|--Starting insertion..." )
                status = NetworkModuleAnnotationParser.parse_file( file_path, class_tag, class_regex, protein_tag, annotation_tag, comment_char, clean_table )
            else:
                Logger.get_instance().info( "|--Data already inserted: insertion bypassed." )
                status = None
        except RainetException as re:
            Logger.get_instance().error( re.to_string() )
            status = Constants.STATUS_RAINET_ERROR
            raise re
        except Exception as e:
            Logger.get_instance().error( e.message )
            status = Constants.STATUS_ERROR
            raise RainetException( "Abnormal Exception during insertion of " + class_name, e )
        finally:
            if status != None:
                sql_session = SQLManager.get_instance().get_session()
                db_status_list = sql_session.query( TableStatus ).filter( TableStatus.tableName == class_name ).all()
                if db_status_list == None or len( db_status_list) == 0:
                    sql_session.add( TableStatus( class_name, status, file_path ) )
                else:
                    db_status = db_status_list[0]
                    db_status.tableStatus = status
                    sql_session.add( db_status )
                SQLManager.get_instance().commit()
        
        
    # Insert data linked to an OBO file
    #
    # @param file_path : string - The path to the data file
    # @param class_name : string - The name of the class to be used to instantiate objects from data
    # @param id_tag : string - The tag used in file to declare a GOterm ID
    # @param name_tag : string - The tag used in file to declare a GOterm Name
    # @param namespace_tag : string - The tag used in file to declare a GOterm namespace
    # @param clean_table : boolean  - The information indicating if the related db table must be cleaned before insertion or not
    def launch_insertion_Obo( self, file_path, class_name, id_tag, name_tag, namespace_tag, clean_table = True ):
        
        try:
            Timer.get_instance().step( "Inserting " + class_name + ":" )
            if SQLUtil.insert_data_required( class_name, self.forceOverride ) :
                Logger.get_instance().info( "|--Starting insertion..." )
                status = OboParser.parse_file( file_path, id_tag, name_tag, namespace_tag, clean_table )
            else:
                Logger.get_instance().info( "|--Data already inserted: insertion bypassed." )
                status = None
        except RainetException as re:
            Logger.get_instance().error( re.to_string() )
            status = Constants.STATUS_RAINET_ERROR
            raise re
        except Exception as e:
            Logger.get_instance().error( e.message )
            status = Constants.STATUS_ERROR
            raise RainetException( "Abnormal Exception during insertion of " + class_name, e )
        finally:
            if status != None:
                sql_session = SQLManager.get_instance().get_session()
                db_status_list = sql_session.query( TableStatus ).filter( TableStatus.tableName == class_name ).all()
                if db_status_list == None or len( db_status_list) == 0:
                    sql_session.add( TableStatus( class_name, status, file_path ) )
                else:
                    db_status = db_status_list[0]
                    db_status.tableStatus = status
                    sql_session.add( db_status )
                SQLManager.get_instance().commit()
        
    # #
    # Insert data linked to a FASTA file
    #
    # @param file_path : string - The path to the data file
    # @param class_name : string - The name of the class to be used to instantiate objects from data
    # @param regex : string - The regular expression used to locate groups in sequence definition
    # @param groups : string - The groups to use in the regular expression
    # @param params : list<string> - The list of parameters (header names) to use to instantiate objects from data
    # @param params_values : list<string> - the list of default values of the parameters
    # @param comment_char : string - the character used to declare comment lines in the data file
    # @param clean_table : boolean  - The information indicating if the related db table must be cleaned before insertion or not 
    def launch_insertion_Fasta( self, file_path, class_name, regex, groups, params, params_values, comment_char, clean_table = True ):
        
        try:
            Timer.get_instance().step( "Inserting " + class_name + ":" )
            if SQLUtil.insert_data_required( class_name, self.forceOverride ) :
                Logger.get_instance().info( "|--Starting insertion..." )
                status = FastaParser.parse_file( file_path, class_name, regex, groups, params, params_values, comment_char, clean_table )
            else:
                Logger.get_instance().info( "|--Data already inserted: insertion bypassed." )
                status = None
        except RainetException as re:
            Logger.get_instance().error( re.to_string() )
            status = Constants.STATUS_RAINET_ERROR
            raise re
        except Exception as e:
            Logger.get_instance().error( e.message )
            status = Constants.STATUS_ERROR
            raise RainetException( "Abnormal Exception during insertion of " + class_name, e )
        finally:
            if status != None:
                sql_session = SQLManager.get_instance().get_session()
                db_status_list = sql_session.query( TableStatus ).filter( TableStatus.tableName == class_name ).all()
                if db_status_list == None or len( db_status_list) == 0:
                    sql_session.add( TableStatus( class_name, status, file_path ) )
                else:
                    db_status = db_status_list[0]
                    db_status.tableStatus = status
                    sql_session.add( db_status )
                SQLManager.get_instance().commit()

#     #
#     # Report on data that failed to be inserted in the database
#     def check_missing_data(self):
#   
#         Logger.get_instance().info("\nReport on number of input entries that failed to be inserted:")
#  
#         # Report on failed insertions during Protein-RNA interaction insertion
#         Logger.get_instance().info("During ProteinRNAInteractionCatRAPID insertion: Number of protein IDs that failed to be found in database: " + 
#                     str(len(DataManager.get_instance().get_data(DataConstants.PROTEIN_RNA_INTERACTION_CATRAPID_MISSING_PROT_KW) ) ) )
#         Logger.get_instance().info("During ProteinRNAInteractionCatRAPID insertion: Number of transcript IDs that failed to be found in database: " + 
#                     str(len(DataManager.get_instance().get_data(DataConstants.PROTEIN_RNA_INTERACTION_CATRAPID_MISSING_RNA_KW) ) ) )


    def check_database_tables(self):
        
        db_engine = SQLManager.get_instance().get_engine()
        
        # Check if the required DB table are present
        # If not create them
        if not db_engine.dialect.has_table(db_engine.connect(), PPINetwork.__tablename__):
            PPINetwork.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), PPINetworkInteraction.__tablename__):
            PPINetworkInteraction.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), RNA.__tablename__):
            RNA.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), RNACrossReference.__tablename__):
            RNACrossReference.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), MRNA.__tablename__):
            MRNA.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), LncRNA.__tablename__):
            LncRNA.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), OtherRNA.__tablename__):
            OtherRNA.__table__.create(bind = db_engine)
#         if not db_engine.dialect.has_table(db_engine.connect(), ProteinRNAInteractionCatRAPID.__tablename__):
#             ProteinRNAInteractionCatRAPID.__table__.create(bind = db_engine)
#         if not db_engine.dialect.has_table(db_engine.connect(), RNATissueExpression.__tablename__):
#            RNATissueExpression.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), Tissue.__tablename__):
            Tissue.__table__.create(bind = db_engine)
#         if not db_engine.dialect.has_table(db_engine.connect(), InteractingRNA.__tablename__):
#             InteractingRNA.__table__.create(bind = db_engine)
#         if not db_engine.dialect.has_table(db_engine.connect(), InteractingProtein.__tablename__):
#             InteractingProtein.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), BioplexCluster.__tablename__):
            BioplexCluster.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), ProteinBioplexAnnotation.__tablename__):
            ProteinBioplexAnnotation.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), WanCluster.__tablename__):
            WanCluster.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), ProteinWanAnnotation.__tablename__):
            ProteinWanAnnotation.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), CorumCluster.__tablename__):
            CorumCluster.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), ProteinCorumAnnotation.__tablename__):
            ProteinCorumAnnotation.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), CustomCluster.__tablename__):
            CustomCluster.__table__.create(bind = db_engine)
        if not db_engine.dialect.has_table(db_engine.connect(), ProteinCustomAnnotation.__tablename__):
            ProteinCustomAnnotation.__table__.create(bind = db_engine)

