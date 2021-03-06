
import os
import shutil
import numpy
#import numpy as np
# import pandas as pd
# import cPickle as pickle
from scipy import stats

from sqlalchemy import or_, and_, distinct
from sqlalchemy.inspection import inspect    

from fr.tagc.rainet.core.execution.ExecutionStrategy import ExecutionStrategy
from fr.tagc.rainet.core.util.option.OptionManager import OptionManager
from fr.tagc.rainet.core.util.option import OptionConstants
from fr.tagc.rainet.core.util.file.FileUtils import FileUtils
from fr.tagc.rainet.core.util.exception.RainetException import RainetException
from fr.tagc.rainet.core.util.log.Logger import Logger
from fr.tagc.rainet.core.util.sql.SQLManager import SQLManager
from fr.tagc.rainet.core.util.data.DataManager import DataManager
from fr.tagc.rainet.core.util.time.Timer import Timer
from fr.tagc.rainet.core.util.subprocess.SubprocessUtil import SubprocessUtil

from fr.tagc.rainet.core.data.DBParameter import DBParameter
from fr.tagc.rainet.core.data.GeneOntology import GeneOntology
from fr.tagc.rainet.core.data.GeneSymbol import GeneSymbol
from fr.tagc.rainet.core.data.KEGGPathway import KEGGPathway
from fr.tagc.rainet.core.data.NetworkModuleAnnotation import NetworkModuleAnnotation
from fr.tagc.rainet.core.data.NetworkModule import NetworkModule
from fr.tagc.rainet.core.data.OCGPartitionAnalysis import OCGPartitionAnalysis
from fr.tagc.rainet.core.data.PartitionAnalysis import PartitionAnalysis
from fr.tagc.rainet.core.data.PPINetworkInteraction import PPINetworkInteraction
from fr.tagc.rainet.core.data.PPINetwork import PPINetwork
from fr.tagc.rainet.core.data.ProteinCrossReference import ProteinCrossReference
from fr.tagc.rainet.core.data.ProteinDomain import ProteinDomain
from fr.tagc.rainet.core.data.ProteinGOAnnotation import ProteinGOAnnotation
from fr.tagc.rainet.core.data.ProteinInteraction import ProteinInteraction
from fr.tagc.rainet.core.data.ProteinIsoform import ProteinIsoform
from fr.tagc.rainet.core.data.ProteinKEGGAnnotation import ProteinKEGGAnnotation
from fr.tagc.rainet.core.data.ProteinNetworkModule import ProteinNetworkModule
from fr.tagc.rainet.core.data.Protein import Protein
from fr.tagc.rainet.core.data.ProteinReactomeAnnotation import ProteinReactomeAnnotation
from fr.tagc.rainet.core.data.ReactomePathway import ReactomePathway
from fr.tagc.rainet.core.data.SynonymGeneSymbol import SynonymGeneSymbol
from fr.tagc.rainet.core.data.Gene import Gene
from fr.tagc.rainet.core.data.RNA import RNA
from fr.tagc.rainet.core.data.MRNA import MRNA
from fr.tagc.rainet.core.data.LncRNA import LncRNA
from fr.tagc.rainet.core.data.OtherRNA import OtherRNA
from fr.tagc.rainet.core.data.RNACrossReference import RNACrossReference
from fr.tagc.rainet.core.data.ProteinRNAInteractionCatRAPID import ProteinRNAInteractionCatRAPID
from fr.tagc.rainet.core.data.RNATissueExpression import RNATissueExpression
from fr.tagc.rainet.core.data.Tissue import Tissue
from fr.tagc.rainet.core.data.TableStatus import TableStatus
from fr.tagc.rainet.core.data.InteractingProtein import InteractingProtein
from fr.tagc.rainet.core.data.InteractingRNA import InteractingRNA

from fr.tagc.rainet.core.data import DataConstants
from fr.tagc.rainet.core.util import Constants


# #
# This class define the Strategy to produce analysis on the given database and parameters
class AnalysisStrategy(ExecutionStrategy):

    #===============================================================================
    #
    # Analysis strategy Constants
    #
    #===============================================================================

    #===================================================================
    # Data Manager object Keywords
    #===================================================================

    # all Protein / RNA in their respective tables
    RNA_ALL_KW = "allRNAs" # Stores all RNA table objects
    PROT_ALL_KW = "allProteins" # Stores all Protein table objects

    # Protein / RNA after their respective filters
    RNA_FILTER_KW = "selectedRNAs" # Stores list of RNA objects after RNA filter
    RNA_FILTER_KEY_KW = "selectedRNAsKey" # Stores dictionary of RNA objects with RNA ID as key
    PROT_FILTER_KW = "selectedProteins" # Stores list of Protein objects after Protein filter
    PROT_FILTER_KEY_KW = "selectedProteinsKey" # Stores dictionary of Protein objects with Protein ID as key

    # Protein / RNA with interaction data, before interaction filterings
    PRI_PROT_ALL_KW = "allProteinsInInteractionTable" # Stores all Protein IDs with interaction data (before cutoff)
    PRI_RNA_ALL_KW = "allRNAInInteractionTable" # Stores all RNA IDs with interaction data (before cutoff)

    # Interaction objects after filtering
    PRI_FILTER_KW = "selectedInteractions" # Stores Interaction objects after Interaction filter

    # Protein / RNA with interaction data, after interaction filterings
    PRI_PROT_FILTER_KW = "filteredInteractingProteins" # Stores all Protein Objects in interactions, after all filters
    PRI_RNA_FILTER_KW = "filteredInteractingRNAs" # Stores all RNA Objects in interactions, after all filters

    # Expression related
    PROT_TISSUES_KW = "proteinTissues" # Stores set of proteins expressed in each tissue
    RNA_TISSUES_KW = "rnaTissues" # Stores set of rna expressed in each tissue
    PRI_TISSUES_KW = "interactingTissues" # Stores custom dictionary containing tissues where interaction has been found after interaction filtering

    # Final RNA and Protein sets
    FINAL_PRO_KW = "finalProteins" # Stores Protein IDs for which report and analysis is done
    FINAL_RNA_KW = "finalRNAs" # Stores RNA IDs for which report and analysis is done


    #===================================================================
    # Report files constants       
    #===================================================================

    # R files
    R_WORKING_DIR = "/home/diogo/workspace/tagc-rainet-RNA/src/fr/tagc/rainet/core/execution/analysis/Rscripts/"
    R_MAIN_SCRIPT = "/home/diogo/workspace/tagc-rainet-RNA/src/fr/tagc/rainet/core/execution/analysis/Rscripts/analysis_strategy_report.R"
    R_SWEAVE_FILE = "/home/diogo/workspace/tagc-rainet-RNA/src/fr/tagc/rainet/core/execution/analysis/Rscripts/analysis_strategy_report.Rnw"
    
    # After filter report
    PARAMETERS_LOG = "parameters.log"
    REPORT_RNA_NUMBERS = "rna_numbers.tsv"
    REPORT_RNA_LIST_AFTER_RNA_FILTER = "list_RNAs_after_RNA_filter.tsv"
    REPORT_PROTEIN_LIST_AFTER_PROTEIN_FILTER = "list_proteins_after_protein_filter.tsv"

    REPORT_INTERACTION_NUMBERS = "interaction_numbers.tsv"

    # Expression report
    REPORT_RNA_EXPRESSION = "rna_expression.tsv"
    REPORT_RNA_EXPRESSION_DATA_PRESENCE = "rna_expression_data_presence.tsv"
    # TODO:     REPORT_PROT_EXPRESSION_DATA_PRESENCE = "prot_expression_data_presence.tsv"
    REPORT_TISSUES_WHERE_EXPRESSED = "interactions_tissues_where_expressed.tsv"
    REPORT_PROTEINS_EXPRESSED_PER_TISSUE = "proteins_expressed_per_tissue.tsv"
    REPORT_RNAS_EXPRESSED_PER_TISSUE = "rnas_expressed_per_tissue.tsv"

    # Interaction report
    REPORT_INTERACTION_SCORES_BIOTYPE = "interaction_scores_biotype.tsv"
    REPORT_INTERACTION_PARTNERS_BIOTYPE = "interaction_partners_biotype.tsv"
    REPORT_INTERACTIONS_SCORE_MATRIX = "interaction_score_matrix.tsv"

    # Dump expression filter
    DUMP_EXPRESSION_FILTER = "interactions_expression_filter.tsv"
    DUMP_EXPRESSION = "interactions_expression.tsv"
    DUMP_EXPRESSION_FILTER_BATCH_SIZE = 100

    def __init__(self):  
        
        # Switch for writing of external report file      
        self.writeReportFile = 0

    # #
    # The Strategy execution method
    def execute(self, run = 1):

        #===================================================================
        # Getting input arguments        
        #===================================================================
        
        self.DBPath = OptionManager.get_instance().get_option(OptionConstants.OPTION_DB_NAME)
        self.species = OptionManager.get_instance().get_option(OptionConstants.OPTION_SPECIES)
        self.outputFolder = OptionManager.get_instance().get_option(OptionConstants.OPTION_OUTPUT_FOLDER)
        self.minimumInteractionScore =  OptionManager.get_instance().get_option(OptionConstants.OPTION_MINIMUM_INTERACTION_SCORE)
        self.RNABiotypes = OptionManager.get_instance().get_option(OptionConstants.OPTION_RNA_BIOTYPES)
        self.gencode = OptionManager.get_instance().get_option(OptionConstants.OPTION_GENCODE)
        self.expressionValueCutoff = OptionManager.get_instance().get_option(OptionConstants.OPTION_EXPRESSION_VALUE_CUTOFF)
        self.expressionTissueCutoff = OptionManager.get_instance().get_option(OptionConstants.OPTION_EXPRESSION_TISSUE_CUTOFF)
        self.lowMemory = OptionManager.get_instance().get_option(OptionConstants.OPTION_LOW_MEMORY)

        # Variable that stores all arguments to appear in parameters log file
        self.arguments = {OptionConstants.OPTION_DB_NAME : self.DBPath,
                          OptionConstants.OPTION_SPECIES : self.species,
                          OptionConstants.OPTION_OUTPUT_FOLDER : self.outputFolder,
                          OptionConstants.OPTION_MINIMUM_INTERACTION_SCORE : self.minimumInteractionScore,
                          OptionConstants.OPTION_RNA_BIOTYPES : self.RNABiotypes,
                          OptionConstants.OPTION_GENCODE : self.gencode,
                          OptionConstants.OPTION_EXPRESSION_VALUE_CUTOFF : self.expressionValueCutoff,
                          OptionConstants.OPTION_EXPRESSION_TISSUE_CUTOFF : self.expressionTissueCutoff,
                          OptionConstants.OPTION_LOW_MEMORY : self.lowMemory
                        }

        #===================================================================
        # Check input argument validity      
        #===================================================================
        
        # Check if output folder path exists, create it if not
        if self.outputFolder != "" and len(self.outputFolder) > 0:
            FileUtils.initialise_output_folders(self.outputFolder)
            self.outputFolderReport = self.outputFolder+"/"+Constants.REPORT_FOLDER
        else:
            raise RainetException( "AnalysisStrategy.execute: Provided output folder is empty.")

        # Check if minimumInteractionScore is float or OFF
        if self.minimumInteractionScore != OptionConstants.DEFAULT_INTERACTION_SCORE:
            try:
                float(self.minimumInteractionScore)
            except TypeError:
                raise RainetException( "AnalysisStrategy.execute: Provided minimum interaction score is not a float.")

        # Process and check provided list of lncRNA subtypes
        if self.RNABiotypes != OptionConstants.DEFAULT_RNA_BIOTYPES:
            self.RNABiotypes = self.RNABiotypes.split(",")
            for subtype in self.RNABiotypes:
                if subtype not in OptionConstants.RNA_BIOTYPES:
                    raise RainetException( "AnalysisStrategy.execute: Provided RNA biotype is not allowed: "+str(subtype))              

        # Check if gencode argument is correct
        try:
            self.gencode = int(self.gencode)
        except TypeError:
            raise RainetException( "AnalysisStrategy.execute: Provided GencodeBasicOnly argument is not numeric.")
        if self.gencode != 1 and self.gencode != 0:
            raise RainetException( "AnalysisStrategy.execute: Provided GencodeBasicOnly argument must be either 0 or 1.")

        # Check if expressionValueCutoff is float or OFF
        if self.expressionValueCutoff != OptionConstants.DEFAULT_EXPRESSION_VALUE_CUTOFF:
            try:
                self.expressionValueCutoff = float(self.expressionValueCutoff)
            except TypeError:
                raise RainetException( "AnalysisStrategy.execute: Provided expression value cutoff is not a float.")

        # Check if expressionTissueCutoff is float
        if self.expressionTissueCutoff != OptionConstants.DEFAULT_EXPRESSION_TISSUE_CUTOFF:
            try:
                float(self.expressionTissueCutoff)
            except TypeError:
                raise RainetException( "AnalysisStrategy.execute: Provided expression tissue cutoff is not a float.")

        #===================================================================
        # Initialisation
        #===================================================================

        # Build a SQL session to DB
        SQLManager.get_instance().set_DBpath(self.DBPath)
        self.sql_session = SQLManager.get_instance().get_session()
        self.db_engine = SQLManager.get_instance().get_engine()

        #===================================================================
        # Run analysis
        #===================================================================
        
        if run:             
            self.analysis()
        
    # #
    # Central function to run analysis-related functions in order
    def analysis(self):

        Logger.get_instance().info( "AnalysisStrategy.analysis: Starting..." )

        Timer.get_instance().start_chrono()

        self.write_parameter_log()
        
        #===================================================================
        # Apply filterings
        #===================================================================

        Timer.get_instance().step( "Filtering RNAs.." )        

        self.filter_RNA()
 
        Timer.get_instance().step( "Filtering Proteins.." )        
         
        self.filter_protein()
       
        Timer.get_instance().step( "Filtering Interactions.." )        
             
        self.filter_PRI()
  
        Timer.get_instance().step( "Filtering Interactions by expression." )               
  
        self.dump_filter_PRI_expression()
               
        #===================================================================
        # Produce reports
        #===================================================================

        if self.lowMemory == 0:
   
            Timer.get_instance().step( "Producing filter report.." )        
        
            self.after_filter_report()
        
            Timer.get_instance().step( "Producing expression report.." )        
        
            self.expression_report()
        
            Timer.get_instance().step( "Producing interaction report.." )        
        
            self.interaction_report()
                  
            if self.writeReportFile:
                Timer.get_instance().step( "Writing report.." )
                self.write_report()
 
        Timer.get_instance().stop_chrono( "Analysis Finished!")

    # #
    # Filter RNA models
    #
    # Stores into DataManager: RNA_ALL_KW, RNA_FILTER_KW, RNA_FILTER_KEY_KW
    # Writes file with list of RNAs after filter.
    def filter_RNA(self):

        #Logger.get_instance().info("AnalysisStrategy.filter_RNA..")

        #===================================================================
        # Get all RNA objects
        #===================================================================
        allRNAs = self.sql_session.query(RNA).all()
        DataManager.get_instance().store_data(AnalysisStrategy.RNA_ALL_KW, allRNAs)

        #===================================================================              
        # Filter transcripts based on chosen biotypes
        #===================================================================
        queryResult = self.sql_session.query( RNA.transcriptID).filter( RNA.transcriptBiotype.in_( self.RNABiotypes)).all()

        filterRNA1 = {str(item.transcriptID) for item in queryResult}

        #===================================================================
        # Filter transcripts based on gencode_basic presence
        #===================================================================
        if self.gencode == 1:
            queryText = "query(RNA.transcriptID).filter(RNA.transcriptGencodeBasic == 1).all()"
        else:
            queryText = "query(RNA.transcriptID).all()"

        filterRNA2 = eval('self.sql_session.' +  queryText)
        filterRNA2 = {str(item.transcriptID) for item in filterRNA2}

        #===================================================================                               
        # Get intersection of the various filterings
        # Store into data manager
        #===================================================================
        selectedRNAs = []
        for rna in allRNAs:
            if rna.transcriptID in filterRNA1 and rna.transcriptID in filterRNA2:
                selectedRNAs.append(rna)

        DataManager.get_instance().store_data(AnalysisStrategy.RNA_FILTER_KW, selectedRNAs)

        # Store actual RNA objects into another dictionary
        DataManager.get_instance().store_data( AnalysisStrategy.RNA_FILTER_KEY_KW, selectedRNAs)
        # Convert format
        DataManager.get_instance().query_to_object_dict( AnalysisStrategy.RNA_FILTER_KEY_KW, "transcriptID")
        
        #===================================================================   
        # File with RNA list
        #===================================================================          
        
        outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_RNA_LIST_AFTER_RNA_FILTER )
        
        rnas = DataManager.get_instance().get_data( AnalysisStrategy.RNA_FILTER_KEY_KW)
        
        for rna in rnas:
            outHandler.write( "%s\n" % ( rna) )
        outHandler.close()

        Logger.get_instance().info( "filter_RNA : Finished RNA filter: " + str( len( selectedRNAs)) )


    # #
    # Filter protein models    
    #
    # Stores final list of proteins on DataManager 
    def filter_protein(self):

        #Logger.get_instance().info("AnalysisStrategy.filter_protein..")
        
        #===================================================================
        # Get all Protein objects
        #===================================================================        

        DataManager.get_instance().perform_query(AnalysisStrategy.PROT_FILTER_KW, "query( Protein ).all()") 

        selectedProts = DataManager.get_instance().get_data( AnalysisStrategy.PROT_FILTER_KW)

        # Store actual objects into another dictionary where key is Protein ID
        DataManager.get_instance().store_data( AnalysisStrategy.PROT_FILTER_KEY_KW, selectedProts)
        # Convert format
        DataManager.get_instance().query_to_object_dict( AnalysisStrategy.PROT_FILTER_KEY_KW, "uniprotAC")

        #===================================================================   
        # File with list of proteins
        #===================================================================          
        
        outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_PROTEIN_LIST_AFTER_PROTEIN_FILTER )
        
        prots = DataManager.get_instance().get_data( AnalysisStrategy.PROT_FILTER_KEY_KW)
        
        for prot in prots:
            outHandler.write( "%s\n" % ( prot) )
        outHandler.close()

        Logger.get_instance().info( "filter_protein : Finished Protein filter: " + str( len( selectedProts)) )


    # #
    # Filter protein-RNA interactions
    #
    # Stores final list of interactions on DataManager 
    def filter_PRI(self):

        #Logger.get_instance().info("AnalysisStrategy.filter_PRI..")

        #===================================================================
        # Retrieve selected RNAs and proteins
        #===================================================================                       
        selectedRNAs = { str( item.transcriptID) for item in DataManager.get_instance().get_data( AnalysisStrategy.RNA_FILTER_KW) }
        selectedProteins = { str( item.uniprotAC) for item in DataManager.get_instance().get_data( AnalysisStrategy.PROT_FILTER_KW) } 

        #===================================================================
        # Total number of distinct proteins and RNAs, regardless of interaction scores (needed for some calculations)
        #===================================================================    
        # Note: the ProteinRNAInteractionCatRAPID table only contains proteins and RNAs that exist in the Protein or RNA tables
        allProteinsWithInteractionData = self.sql_session.query( ProteinRNAInteractionCatRAPID.proteinID ).distinct().all()       
        allProteinsWithInteractionData = { str( protID[ 0]) for protID in allProteinsWithInteractionData}

        allTranscriptsWithInteractionData = self.sql_session.query( ProteinRNAInteractionCatRAPID.transcriptID ).distinct().all()       
        allTranscriptsWithInteractionData = { str( txID[ 0]) for txID in allTranscriptsWithInteractionData}

        DataManager.get_instance().store_data(AnalysisStrategy.PRI_PROT_ALL_KW, allProteinsWithInteractionData)
        DataManager.get_instance().store_data(AnalysisStrategy.PRI_RNA_ALL_KW, allTranscriptsWithInteractionData)

        #===================================================================         
        # Filter interactions based on minimumInteractionScore
        #===================================================================                 

        if self.minimumInteractionScore != OptionConstants.DEFAULT_INTERACTION_SCORE:
            queryText = "query( ProteinRNAInteractionCatRAPID.transcriptID, ProteinRNAInteractionCatRAPID.proteinID, ProteinRNAInteractionCatRAPID.interactionScore ).filter( ProteinRNAInteractionCatRAPID.interactionScore >= "+str( self.minimumInteractionScore)+")"    
        else:
            queryText = "query( ProteinRNAInteractionCatRAPID.transcriptID, ProteinRNAInteractionCatRAPID.proteinID, ProteinRNAInteractionCatRAPID.interactionScore )"
  
        interactions = eval('self.sql_session.' +  queryText + ".all()")

        Logger.get_instance().info( "filter_PRI : Finished minimum interaction score filter: " + str( len( interactions)) )

        # Note: due to memory usage constraints, the interaction objects are not stored but instead all they attributes are stored as a tuple

        #===================================================================          
        # Filter for interactions between selected RNAs and proteins
        #===================================================================         
        selectedInteractions = []
        for inter in interactions:
            if inter.transcriptID in selectedRNAs and inter.proteinID in selectedProteins:
                selectedInteractions.append(inter)

        Logger.get_instance().info( "filter_PRI : Finished interacting RNA / protein filter: " + str( len( selectedInteractions)) )

#        # 15-June-2016 # with new catRAPID files the peptideID was removed.
#         #===================================================================    
#         # Filter interactions based on peptide IDs corresponding to same protein
#         #=================================================================== 
#         # Reminder: original protein-RNA interaction file contains interactions on transcript-peptide level.
#         # We want to have interactions on transcript-protein level. A protein can have several peptide isoforms.
#         # Here we retain only one interaction per transcript-protein pair, the one with highest score or
#         # the peptide ID with smaller number in case of score equality.
# 
#         # build dictionary where key is transcript+protein IDs, and values the possible different isoforms
#         pairs = {}
#         for inter in selectedInteractions:
#             pair = str(inter.transcriptID) + "|" + str(inter.proteinID)
#             if pair not in pairs:
#                 pairs[ pair] = []
#             pairs[ pair].append( inter)
# 
#         # store only interaction between one transcript and protein, by selecting the peptide which had higher interaction score
#         nonRedundantInteractions = []
#         for pair in pairs:
# 
#             maxScore = float( "-inf")
#             maxPeptide = ""
# 
#             # sort by smaller number on peptide ID (second item on list), choose final peptide ID by score or smaller ID number
#             for peptide in sorted( pairs[ pair]):
#                                 
#                 score = float( peptide.interactionScore)
#                 
#                 if score > maxScore:
#                     maxScore = score
#                     maxPeptide = peptide
# 
#             if maxPeptide == "":
#                 raise RainetException( "AnalysisStrategy.filter_PRI : cannot determine maximum interaction score.")
#             
#             nonRedundantInteractions.append( peptide)
#             
#         del pairs
#         selectedInteractions = nonRedundantInteractions
# 
#         Logger.get_instance().info( "filter_PRI : Finished peptide redundancy filter: " + str( len( selectedInteractions )) )

        DataManager.get_instance().store_data(AnalysisStrategy.PRI_FILTER_KW, selectedInteractions)


#     # 15-June-2016: due to computational constraints, we decided to not insert all the catRAPID interaction data but instead insert it AFTER applying expression cutoff, therefore this function had to be modified
#     # #
#     # Filter protein-RNA interactions by member co-existence
#     #
#     # Stores final list of interactions on DataManager 
#     def filter_PRI_expression(self):
#  
#         # Get filtered interactions
#         selectedInteractions = DataManager.get_instance().get_data( AnalysisStrategy.PRI_FILTER_KW)
#  
#         #===================================================================    
#         # Filter interactions based on RNA and Protein (mRNA) expression
#         #=================================================================== 
#  
#         # List will contain expression-filtered set of interactions
#         expressedInteractions = []
#   
#         # Dictionary which will contain tissues where interaction was found to be present
#         expressedInteractionsTissues = {} # key -> transcriptID|proteinID (pair), value -> set of tissues
#   
#         # checking if filtering option is on or off
#         if self.expressionValueCutoff != OptionConstants.DEFAULT_EXPRESSION_VALUE_CUTOFF:
#            
#             # Get list of tissues for looking over their expression values on each transcript
#             tissues = [ str( tiss[0]) for tiss in self.sql_session.query( Tissue.tissueName ).all() ]
#  
#             # Map mRNA to protein ID
#             # Search mRNA that produces interacting protein
#             mRNAMap = self.sql_session.query( MRNA.transcriptID, MRNA.proteinID ).all()
#             mRNADict = {} # key -> protein ID, val -> list of mRNAs encoding protein
#             for items in mRNAMap:
#                 txID, protID = str( items[0]), str( items[1])
#                 if protID != "None":
#                     if protID not in mRNADict:
#                         mRNADict[ protID] = []
#                     mRNADict[ protID].append( txID)
#  
#             # Map expression per tissue to transcript ID           
#             expressionMap = self.sql_session.query( RNATissueExpression.transcriptID, RNATissueExpression.expressionValue, RNATissueExpression.tissueName).all()
#             expressionDict = {} # key -> transcript ID, value -> list of pairs of expression value and tissue name
#             for items in expressionMap:
#                 txID, expr, tissName = str( items[0]), float( items[1]), str( items[2])
#                 if txID not in expressionDict:
#                     expressionDict[ txID] = []
#                 expressionDict[ txID].append( (expr, tissName) )
#              
#             count = 0
#             # loop over the ongoing filtered interactions
#             for inter in selectedInteractions:
#                  
#                 count+= 1
#                 if count % 100000 == 0:
#                     Logger.get_instance().info( "filter_PRI_expression : Processed interactions.. " + str( count) )
#                      
#                 # skip transcripts with no expression
#                 if inter.transcriptID not in expressionDict:
#                     continue
#       
#                 # skip protein with no mRNAs in database
#                 if inter.proteinID not in mRNADict:
#                     continue
#  
#                 # Search mRNA that produces interacting protein
#                 mRNAs = mRNADict[ inter.proteinID]
#      
#                 # variable which stores set of tissues where both partners of pair are expressed 
#                 setOfInteractingTissues = set()
#      
#                 # Get RNA transcript expression for all tissues
#                 RNATissueExpressions = {}
#                 for tiss in expressionDict[ inter.transcriptID]:     
#                     txExpressionVal = float( tiss[0])
#                     tissueName = str( tiss[1])
#                     RNATissueExpressions[ tissueName] = txExpressionVal                   
#       
#                 # Get Protein expression for all tissues
#                 # there can be several mRNAs for the same protein ID, here we use them all to have set of interacting tissues
#                 # we only required that at least one of the mRNAs producing the protein is present with the other RNA (e.g. lncRNA)   
#                 for mRNAID in mRNAs:
#      
#                     # skip transcripts with no expression      
#                     if mRNAID not in expressionDict:
#                         continue
#      
#                     MRNATissueExpressions = {}
#                           
#                     # Get the Protein expression, using its mRNA
#                     for tiss in expressionDict[ mRNAID]:     
#                         txExpressionVal = float( tiss[0])
#                         tissueName = str( tiss[1])
#                         MRNATissueExpressions[ tissueName] = txExpressionVal                   
#      
#                     for tissue in tissues:
#                         txExpressionVal = RNATissueExpressions[ tissue]
#                         protExpressionVal = MRNATissueExpressions[ tissue]
#      
#                         if txExpressionVal >= self.expressionValueCutoff and protExpressionVal >= self.expressionValueCutoff:
#                             setOfInteractingTissues.add( tissue)
#      
#                 # For a protein-RNA pair, retain interaction only if protein-RNA are present in at least one tissue
#                 if len( setOfInteractingTissues) >= self.expressionTissueCutoff: # cutoff of minimum number of tissues
#                     expressedInteractions.append( inter)
#                     pair = inter.transcriptID + "|" + inter.proteinID
#                     expressedInteractionsTissues[ pair] = setOfInteractingTissues
#                      
#             selectedInteractions = expressedInteractions
#      
#             Logger.get_instance().info("filter_PRI_expression : Finished expression filter: " + str( len( selectedInteractions)) )    
#  
#         #===================================================================    
#         # Store datasets
#         #=================================================================== 
#  
#         # Store interaction information
#         DataManager.get_instance().store_data( AnalysisStrategy.PRI_TISSUES_KW, expressedInteractionsTissues)
#         DataManager.get_instance().store_data( AnalysisStrategy.PRI_FILTER_KW, selectedInteractions)
#         del expressedInteractions
#         del expressedInteractionsTissues
#  
#         # Store interacting RNA and protein object after all filters
#         interRNAIDs = { str( inter.transcriptID) for inter in selectedInteractions}
#         interProtIDs = { str( inter.proteinID) for inter in selectedInteractions}
#  
#         rnaObjects = DataManager.get_instance().get_data( AnalysisStrategy.RNA_FILTER_KEY_KW)
#         protObjects = DataManager.get_instance().get_data( AnalysisStrategy.PROT_FILTER_KEY_KW)
#    
#         interRNAObjects = { rnaID : rnaObjects[ rnaID] for rnaID in interRNAIDs }
#         interProtObjects = { protID : protObjects[ protID] for protID in interProtIDs }
#  
#         DataManager.get_instance().store_data( AnalysisStrategy.PRI_RNA_ALL_KW, interRNAObjects)
#         DataManager.get_instance().store_data( AnalysisStrategy.PRI_PROT_FILTER_KW, interProtObjects)


    # #
    # Filter protein-RNA interactions by member co-existence, after RNA and protein filters
    # Expression filtering output file is independent of PRI filtering (uses "InteractingRNA and InteractingProtein" tables).
    # Writes co-present interacting pairs to file.
    # Updates 'selectedInteractions' (PRI_FILTER_KW) with the filtering.
    def dump_filter_PRI_expression(self):

        # Get filtered interactions
        selectedInteractions = DataManager.get_instance().get_data( AnalysisStrategy.PRI_FILTER_KW)
        
        # Dictionary which will contain tissues where interaction was found to be present
        expressedInteractionsTissues = {} # key -> transcriptID|proteinID (pair), value -> set of tissues

        interactionsExpression = {} # key -> transcriptID|proteinID (pair), value -> expression of pair

        # Dictionary with list of tissues where protein/rna is present
        proteinExpressionTissues = {} # key -> tissue, value -> set of protein IDs
        rnaExpressionTissues = {} # key -> tissue, value -> set of tx IDs

        # checking if filtering option is on or off
        if self.expressionValueCutoff != OptionConstants.DEFAULT_EXPRESSION_VALUE_CUTOFF:

            #===================================================================             
            # Create 'virtual' interactions based on lists of interacting RNA and Protein
            #=================================================================== 

            # Retrieve previously filtered RNAs and proteins
            selectedRNAs = { str( item.transcriptID) for item in DataManager.get_instance().get_data( AnalysisStrategy.RNA_FILTER_KW) }
            selectedProteins = { str( item.uniprotAC) for item in DataManager.get_instance().get_data( AnalysisStrategy.PROT_FILTER_KW) } 

            # query interacting RNAs
            queryText = "query( InteractingRNA.transcriptID).all()"
            interactingRNAs = eval('self.sql_session.' +  queryText)
            interactingRNAs = { str( item.transcriptID) for item in interactingRNAs} # formatting

            # filter by previous RNA filter
            interactingRNAs = { rnaID for rnaID in interactingRNAs if rnaID in selectedRNAs}
            
            # query interacting proteins
            queryText = "query( InteractingProtein.uniprotAC ).all()"
            interactingProteins = eval('self.sql_session.' +  queryText)
            interactingProteins = { str( item.uniprotAC) for item in interactingProteins} # formatting
            
            # filter by previous Protein filter
            interactingProteins = { protID for protID in interactingProteins if protID in selectedProteins}
    
            totalItems = len( interactingProteins) * len( interactingRNAs)

            Logger.get_instance().info("dump_filter_PRI_expression : initialised interaction data. will measure %s interactions (%s RNAs vs %s proteins)." % ( totalItems, len( interactingRNAs), len( interactingProteins) ))

            #===================================================================    
            # Initialise required expression data
            #===================================================================   

            # Initialise the output files to be written in batches
            outHandlerExpFilt = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.DUMP_EXPRESSION_FILTER )
            outHandlerExp = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.DUMP_EXPRESSION )
            
            # Map mRNA to protein ID
            # Search mRNA that produces interacting protein
            mRNAMap = self.sql_session.query( MRNA.transcriptID, MRNA.proteinID ).all()
            self.mRNADict = {} # key -> protein ID, val -> list of mRNAs encoding protein
            for items in mRNAMap:
                txID, protID = str( items[0]), str( items[1])
                if protID != "None":
                    if protID not in self.mRNADict:
                        self.mRNADict[ protID] = []
                    self.mRNADict[ protID].append( txID)

            Logger.get_instance().info("dump_filter_PRI_expression : initialised mRNA-protein data. %s proteins with mRNAs." % len( self.mRNADict)  )    
   
            # Get list of tissues for looking over their expression values on each transcript
            tissues = [ str( tiss[0]) for tiss in self.sql_session.query( Tissue.tissueName ).all() ]
            
            # Map expression per tissue to transcript ID           
            expressionMap = self.sql_session.query( RNATissueExpression.transcriptID, RNATissueExpression.expressionValue, RNATissueExpression.tissueName).all()
            self.expressionDict = {} # key -> transcript ID, value -> list of pairs of expression value and tissue name
            for items in expressionMap:
                txID, expr, tissName = str( items[0]), float( items[1]), str( items[2])
                if txID not in self.expressionDict:
                    self.expressionDict[ txID] = []
                self.expressionDict[ txID].append( (expr, tissName) )

            Logger.get_instance().info("dump_filter_PRI_expression : loaded expression data. %s total RNAs with expression data." % len( self.expressionDict) )    

            #===================================================================    
            # Store all protein-related expression values into memory
            #===================================================================    
            self.ProtMRNATissueExpressions = {} # key -> prot ID, val -> dict. key -> mRNA ID, val -> expression profile per tissue
            for protID in interactingProteins:
                # skip protein with no mRNAs in database
                if protID not in self.mRNADict:
                    continue

                if protID not in self.ProtMRNATissueExpressions:
                    self.ProtMRNATissueExpressions[ protID] = {}

                # Search mRNA that produces interacting protein
                mRNAs = self.mRNADict[ protID]

                # Get Protein expression for all tissues
                # there can be several mRNAs for the same protein ID, here we use them all to have set of interacting tissues
                # we only required that at least one of the mRNAs producing the protein is present with the other RNA (e.g. lncRNA)   
                for mRNAID in mRNAs:
                
                    # skip transcripts with no expression      
                    if mRNAID not in self.expressionDict:
                        continue
                
                    MRNATissueExpressions = {} # key -> tissue, val -> expression val
                          
                    # Get the Protein expression, using its mRNA
                    for tiss in self.expressionDict[ mRNAID]:     
                        txExpressionVal = float( tiss[0])
                        tissueName = str( tiss[1])
                        MRNATissueExpressions[ tissueName] = txExpressionVal                   

                    # store expression information for each mRNA
                    if mRNAID not in self.ProtMRNATissueExpressions[ protID]:
                        self.ProtMRNATissueExpressions[ protID][ mRNAID] = {}
                    self.ProtMRNATissueExpressions[ protID][ mRNAID] = MRNATissueExpressions

            Logger.get_instance().info("dump_filter_PRI_expression : initialised expression data. %s proteins with expression data." % len( self.ProtMRNATissueExpressions) )    

            #===================================================================             
            # Loop virtual interactions and apply filter
            # Approach: first retrieve information for RNA, then loop it against each interacting protein. Batch for each RNA
            #=================================================================== 
            countRNA = 0
            #===================================================================             
            # Loop RNAs
            #===================================================================             
            for rnaID in interactingRNAs:

                countRNA += 1
                if countRNA % AnalysisStrategy.DUMP_EXPRESSION_FILTER_BATCH_SIZE == 0:
                    Logger.get_instance().info("dump_filter_PRI_expression : processed %s RNAs out of %s" % ( countRNA, len( interactingRNAs)) )   
                    
                    if self.lowMemory == 1:
                        Logger.get_instance().info("dump_filter_PRI_expression : writing expression filter output file. %s lines." % ( len( expressedInteractionsTissues)) )               
            
                        # write batch interactions to file
                        for pair in expressedInteractionsTissues:
                            transcriptID,proteinID = pair.split( "|")
                            text = "%s\t%s\n" % ( proteinID, transcriptID )
                            outHandlerExpFilt.write( text)
                        
                        # reset dictionary to save memory
                        expressedInteractionsTissues = {}

                        Logger.get_instance().info("dump_filter_PRI_expression : writing expression output file. %s lines." % ( len( interactionsExpression)) )               

                        # write batch interactions to file
                        for pair in interactionsExpression:
                            transcriptID,proteinID = pair.split( "|")
                            text = "%s\t%s\t%s\n" % ( proteinID, transcriptID, interactionsExpression[ pair] )
                            outHandlerExp.write( text)

                        # reset dictionary to save memory
                        interactionsExpression = {}
                
                # skip transcripts with no expression
                if rnaID not in self.expressionDict:
                    continue

                # Get RNA transcript expression for all tissues
                RNATissueExpressions = {}
                for tiss in self.expressionDict[ rnaID]:     
                    txExpressionVal = float( tiss[0])
                    tissueName = str( tiss[1])
                    RNATissueExpressions[ tissueName] = txExpressionVal                   

                    if self.lowMemory == 0:
                        # store data on RNA tissue expression
                        if txExpressionVal >= self.expressionValueCutoff:
                            if tissueName not in rnaExpressionTissues:
                                rnaExpressionTissues[ tissueName] = set()
                            rnaExpressionTissues[ tissueName].add( rnaID)                               

                #===================================================================             
                # Loop Proteins
                #===================================================================             
                # loop for each protein, with precalculated values. create list of 1 RNA vs all protein interaction
                for protID in self.ProtMRNATissueExpressions:
                    
                    pair = rnaID + "|" + protID

                    # storing the pair expression, defined as the minimum expression between the two partners, in any tissue
                    pairExpression = 0.0

                    # variable which stores set of tissues where both partners of pair are expressed 
                    setOfInteractingTissues = set()
                    
                    # check expression for each mRNA producing the protein
                    for mRNAID in self.ProtMRNATissueExpressions[ protID]:
                        
                        # compare expressions between RNA and protein for each tissue
                        for tissue in tissues:
                            txExpressionVal = RNATissueExpressions[ tissue]
                            protExpressionVal = self.ProtMRNATissueExpressions[ protID][ mRNAID][ tissue]
                                                                                                    
                            if txExpressionVal >= self.expressionValueCutoff and protExpressionVal >= self.expressionValueCutoff:
                                setOfInteractingTissues.add( tissue)

                            # calculate minimum pair expression, keep the maximum along tissue and among mRNAs of same protein
                            minExpr = min( txExpressionVal, protExpressionVal)
                            if minExpr > pairExpression:
                                pairExpression = minExpr

                            if self.lowMemory == 0:                                    
                                # store data on protein tissue expression
                                if protExpressionVal >= self.expressionValueCutoff:
                                    if tissue not in proteinExpressionTissues:
                                        proteinExpressionTissues[ tissue] = set()
                                    proteinExpressionTissues[ tissue].add( protID)

                    # For a protein-RNA pair, retain interaction only if protein-RNA are present in at least x tissues
                    if len( setOfInteractingTissues) >= self.expressionTissueCutoff: # cutoff of minimum number of tissues
                        expressedInteractionsTissues[ pair] = setOfInteractingTissues

                    # For a protein-RNA pair, regardless of passing or not cutoffs, store its expression value
                    interactionsExpression[ pair] = pairExpression


            ## write last batch if using low memory flag
            if self.lowMemory == 1:
                Logger.get_instance().info("dump_filter_PRI_expression : writing expression filter output file. %s lines." % ( len( expressedInteractionsTissues)) )               
    
                # write batch interactions to file
                for pair in expressedInteractionsTissues:
                    transcriptID,proteinID = pair.split( "|")
                    text = "%s\t%s\n" % ( proteinID, transcriptID )
                    outHandlerExpFilt.write( text)
                
                # reset dictionary to save memory
                expressedInteractionsTissues = {}

                Logger.get_instance().info("dump_filter_PRI_expression : writing expression output file. %s lines." % ( len( interactionsExpression)) )               

                # write batch interactions to file
                for pair in interactionsExpression:
                    transcriptID,proteinID = pair.split( "|")
                    text = "%s\t%s\t%s\n" % ( proteinID, transcriptID, interactionsExpression[ pair] )
                    outHandlerExp.write( text)

                # reset dictionary to save memory
                interactionsExpression = {}
            
            outHandlerExpFilt.close()
            outHandlerExp.close() 
            
            #===================================================================    
            # write passing interactions for all RNAs vs all proteins
            #===================================================================                    
            #===================================================================    
            # File with list of interactions passing RNA, protein and expression filters (not interaction cutoff)
            # E.g. proteinID\ttranscriptID\n
            #=================================================================== 

            if self.lowMemory == 0:
                Logger.get_instance().info("dump_filter_PRI_expression : writing output file. %s lines." % ( len( expressedInteractionsTissues)) )               
    
                outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.DUMP_EXPRESSION_FILTER )
   
                # write all interactions to file
                for pair in expressedInteractionsTissues:
                    transcriptID,proteinID = pair.split( "|")
                    text = "%s\t%s\n" % ( proteinID, transcriptID )
                    outHandler.write( text)
          
                outHandler.close()

            #===================================================================    
            # write interactions and their expression for all RNAs vs all proteins
            #===================================================================                    
            #===================================================================    
            # File with list of hypothetical interactions and their pair expression value
            # E.g. proteinID\ttranscriptID\texpression\n
            #=================================================================== 

            if self.lowMemory == 0:
                Logger.get_instance().info("dump_filter_PRI_expression : writing expression file. %s lines." % ( len( interactionsExpression)) )               

                outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.DUMP_EXPRESSION )

                # write all interactions to file
                for pair in interactionsExpression:
                    transcriptID,proteinID = pair.split( "|")
                    text = "%s\t%s\t%s\n" % ( proteinID, transcriptID, interactionsExpression[ pair] )
                    outHandler.write( text)
      
                outHandler.close()

            #===================================================================    
            # Store interaction information 
            #===================================================================    
            # update selectedInteractions object, adding only the ones that pass the filter

            Logger.get_instance().info("dump_filter_PRI_expression : storing interactions. " )               

            newSelectedInteractions = []
            for inter in selectedInteractions:
                pair = inter.transcriptID + "|" + inter.proteinID
                if pair in expressedInteractionsTissues:
                    newSelectedInteractions.append( inter)

            selectedInteractions = newSelectedInteractions[:]

            DataManager.get_instance().store_data( AnalysisStrategy.PROT_TISSUES_KW, proteinExpressionTissues) 
            DataManager.get_instance().store_data( AnalysisStrategy.RNA_TISSUES_KW, rnaExpressionTissues) 
            DataManager.get_instance().store_data( AnalysisStrategy.PRI_TISSUES_KW, expressedInteractionsTissues)
            DataManager.get_instance().store_data( AnalysisStrategy.PRI_FILTER_KW, selectedInteractions)

            del expressedInteractionsTissues
            del newSelectedInteractions

        else:
            Logger.get_instance().info( "dump_filter_PRI_expression : Expression filtering not active" )

        #===================================================================    
        # Store / update information
        #===================================================================            
        # Keep RNAs and Proteins that will be used for analysis / report

        RNAObjects = DataManager.get_instance().get_data( AnalysisStrategy.RNA_FILTER_KEY_KW)
        ProtObjects = DataManager.get_instance().get_data( AnalysisStrategy.PROT_FILTER_KEY_KW)
 
        interRNAs = { RNAObjects[ str( inter.transcriptID)] for inter in selectedInteractions }
        interProts = { ProtObjects[ str( inter.proteinID)] for inter in selectedInteractions }

        DataManager.get_instance().store_data( AnalysisStrategy.FINAL_RNA_KW, interRNAs)
        DataManager.get_instance().store_data( AnalysisStrategy.FINAL_PRO_KW, interProts)

    
    # #
    # Write output file with the parameters used
    def write_parameter_log(self):
                
        #===================================================================    
        # Write log of parameters used
        #=================================================================== 

        outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.PARAMETERS_LOG )
        
        Logger.get_instance().info( "\nARGUMENTS USED:" )

        outHandler.write( "Argument\tValue\n")
        for argName in sorted( self.arguments):
            argValue = self.arguments[ argName]
            Logger.get_instance().info( "%s:\t%s" % ( argName, argValue) ) 
            outHandler.write( "%s:\t%s\n" % ( argName, argValue) )
        outHandler.close()


    # #
    # Retrieve statistics before and after the filtering steps.
    # Produce output files that will be used for a pdf report
    def after_filter_report(self):

        #===================================================================    
        # RNA numbers report
        #
        # 'Before filtering' = before any RNA, protein or interactions filtering
        # 'After filtering' = after RNA filter, but before interactions filter
        #=================================================================== 

        #===================================================================    
        # File with number of RNAs types and lncRNA subtypes, before and after filter
        #=================================================================== 

        Timer.get_instance().step( "after_filter_report : producing RNA numbers files" )   

        outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_RNA_NUMBERS )
        
        # Write header
        outHandler.write( "Data\t" +
                          "Total_Genes\t" +
                          "Total_RNAs\t" +
                           "\t".join( DataConstants.RNA_BROAD_TYPES) + "\t" +
                           "\t".join( OptionConstants.RNA_BIOTYPES) + "\n")

        # #
        # Get / initialise data

        # Get filtered and unfiltered RNAs
        filteredRNAs = DataManager.get_instance().get_data( AnalysisStrategy.FINAL_RNA_KW)
        allRNAs = DataManager.get_instance().get_data( AnalysisStrategy.RNA_ALL_KW)

        # Get RNA broad types
        allRNABroadTypes = [ rna.type for rna in allRNAs]
        filteredRNABroadTypes = [ rna.type for rna in filteredRNAs]

        # Get RNA biotypes 
        allRNABiotypes = [ rna.transcriptBiotype for rna in allRNAs if rna.transcriptBiotype in OptionConstants.RNA_BIOTYPES]
        filteredRNABiotypes = [ rna.transcriptBiotype for rna in filteredRNAs if rna.transcriptBiotype in OptionConstants.RNA_BIOTYPES]

        # Get numbers of genes
        allGenes = { rna.geneID for rna in allRNAs}
        filteredGenes = { rna.geneID for rna in filteredRNAs}

        # #
        # Report numbers before and after filtering        
        beforeFilterText = "Before_RNA_filter"
        afterFilterText = "After_RNA_filter"

        # Total number of unique gene IDs
        beforeFilterText+= "\t%i" % len( allGenes)
        afterFilterText+= "\t%i" % len( filteredGenes)      

        # Total number of RNAs (of any type)
        beforeFilterText+= "\t%i" % len( allRNAs)
        afterFilterText+= "\t%i" % len( filteredRNAs)
        
        # Numbers of broad RNA types
        for rnaType in DataConstants.RNA_BROAD_TYPES:
                beforeFilterText+= "\t%i" % allRNABroadTypes.count( rnaType)
                afterFilterText+= "\t%i" % filteredRNABroadTypes.count( rnaType)
        
        # RNA biotypes
        for biotype in OptionConstants.RNA_BIOTYPES:
            beforeFilterText+=  "\t%i" % allRNABiotypes.count( biotype)
            afterFilterText+=  "\t%i" % filteredRNABiotypes.count( biotype)

        outHandler.write( beforeFilterText+"\n"+afterFilterText+"\n")
        outHandler.close()

        #===================================================================    
        # Interactions numbers report
        #
        # Note1: interactions filtering is applied after RNA and protein filtering
        #        Therefore, 'filtering'-named objects refer to the interaction filter
        #
        # Note2: the protein-RNA interactions are a 'natural filter' of RNAs/Proteins, even without score filter,
        #        since not all RNA's / proteins will be interacting (e.g. they lack interaction data)
        #
        # Note3: reporting only for the argument-selected RNA biotypes
        #
        # Note4:
        #        'Before filtering' = before interactions filtering, but after RNA and protein filters
        #        'After filtering' = after interactions filtering AND after RNA and protein filters
        #=================================================================== 

        Timer.get_instance().step( "after_filter_report : producing interaction numbers files" )   

        #===================================================================    
        # File with number of interactions and numbers of proteins and RNAs involved, before and after INTERACTION filter
        #=================================================================== 

        outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_INTERACTION_NUMBERS )

        # Write header
        outHandler.write( "Data\t" +
                          "Total_interactions\t" +
                          "Total_proteins\t" +
                          "Total_RNAs\t" +
                           "\t".join( self.RNABiotypes) + "\n")

        # #
        # Get / initialise data

        # Get filtered interactions
        filteredInteractions = DataManager.get_instance().get_data( AnalysisStrategy.PRI_FILTER_KW)
        filteredRNAs = DataManager.get_instance().get_data( AnalysisStrategy.FINAL_RNA_KW)
        filteredProts = DataManager.get_instance().get_data( AnalysisStrategy.FINAL_PRO_KW)

        # Get count of filtered and unfiltered interactions
        # Note: opposed to filtered interactions, it may not be possible to retrieve all interaction objects due to computational constraints
        # disregard the meaning of "transcriptID" this is simply to speed-up query
        allInteractionsCount = self.sql_session.query( ProteinRNAInteractionCatRAPID.transcriptID ).count() 
        filteredInteractionsCount = len( filteredInteractions)
        
        # Counts for proteins and RNAs, before interaction filtering
        allDistinctTxCount = len( filteredRNAs)
        allDistinctProtCount = len( filteredProts)

        # Counts for proteins and RNAs, after filtering (i.e. with interactions)
        # Lists of IDs for the filtered interactions
        interactingRNAs = {inter.transcriptID for inter in filteredInteractions}
        interactingProteins = {inter.proteinID for inter in filteredInteractions}

        filteredDistinctTxCount = len( interactingRNAs)
        filteredDistinctProtCount = len( interactingProteins)

        # Get numbers of RNAs in interactions by biotype
        filteredRNABioypesCounts = {} # key -> transcriptBiotype, value -> number of interacting RNAs with that transcriptBiotype
        filteredInteractingRNAs = {} # key -> transcriptID of interacting RNA, value -> RNA object
        # Get values for filtered interactions
        for rna in filteredRNAs: # filtered RNAs is list of RNAs after RNA filter (not related to interactions filter)
            # if the RNA is in the set of interacting RNAs
            if rna.transcriptID in interactingRNAs:
                if rna.transcriptBiotype not in filteredRNABioypesCounts:
                    filteredRNABioypesCounts[ rna.transcriptBiotype] = 0
                filteredRNABioypesCounts[ rna.transcriptBiotype]+= 1

                # if interacting RNA biotype is in list wanted biotypes
                if rna.transcriptBiotype in self.RNABiotypes: 
                    if rna.transcriptID not in filteredInteractingRNAs:
                        filteredInteractingRNAs[ rna.transcriptID] = rna
                    else:
                        RainetException( "AnalysisStrategy.after_filter_report : abnormal duplicate transcript ID: " +  rna.transcriptID)

        # #
        # Report numbers before and after filtering        
        beforeFilterText = "Before_interactions_filter"
        afterFilterText = "After_interactions_filter"

        # Total number of interactions
        beforeFilterText+= "\t%i" % allInteractionsCount
        afterFilterText+= "\t%i" % filteredInteractionsCount   

        # numbers of proteins in interactions
        beforeFilterText+= "\t%i" % allDistinctProtCount
        afterFilterText+= "\t%i" % filteredDistinctProtCount
        
        # numbers of RNAs in interactions
        beforeFilterText+= "\t%i" % allDistinctTxCount
        afterFilterText+= "\t%i" % filteredDistinctTxCount

        # numbers for each biotype of RNAs
        for biotype in self.RNABiotypes:
            # before filter
            allRNACount = filteredRNABiotypes.count( biotype)

            # after filter
            # if biotype was not initialised in the counts item, attribute value 0
            if biotype in filteredRNABioypesCounts:
                filteredRNACount = filteredRNABioypesCounts[ biotype]
            else:
                filteredRNACount = 0

            beforeFilterText+= "\t%i" % allRNACount
            afterFilterText+= "\t%i" % filteredRNACount

        outHandler.write( beforeFilterText + "\n" + afterFilterText + "\n")
        outHandler.close()


    # #
    # Retrieve statistics for the interaction data after filtering.
    # Produce output files that will be used for a pdf report
    def interaction_report(self):

        #===================================================================    
        # Initialization
        #=================================================================== 

        # Get filtered interactions
        filteredInteractions = DataManager.get_instance().get_data( AnalysisStrategy.PRI_FILTER_KW)
        
        # Get filtered RNAs
        filteredRNAs = DataManager.get_instance().get_data( AnalysisStrategy.FINAL_RNA_KW)
        # Make dictionary of filtered RNAs for quicker access
        filteredRNAsDict = { str( rna.transcriptID) : rna for rna in filteredRNAs }

        # Store interaction and RNA information for each interaction
        interactionsPerBiotype = {} # Key -> biotype, value -> dict: Key -> transcript ID, value -> dict: Key -> protein ID, value -> interaction score
        for inter in filteredInteractions:
            txID = str( inter.transcriptID)
            protID = str( inter.proteinID)
            interScore = float( inter.interactionScore)

            if txID not in filteredRNAsDict:
                raise RainetException( "AnalysisStrategy.interaction_report : interacting RNA not in filtered RNA list.")
            
            biotype = str( filteredRNAsDict[ txID].transcriptBiotype)
            
            if biotype not in interactionsPerBiotype:
                interactionsPerBiotype[ biotype] = {}
            if txID not in interactionsPerBiotype[ biotype]:
                interactionsPerBiotype[ biotype][ txID] = {}
            
            interactionsPerBiotype[ biotype][ txID][ protID] = interScore       

        #===================================================================    
        # File with interaction scores for each subclass of lncRNAs
        # File number of interaction partners for each subclass of lncRNAs
        #        
        # E.g. biotype\tlist_of_with_scores
        #=================================================================== 

        outHandlerScore = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_INTERACTION_SCORES_BIOTYPE )
        outHandlerPartners = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_INTERACTION_PARTNERS_BIOTYPE )
                
        # Get biotypes of lncRNAs plus mRNA
        wantedBiotypes = DataConstants.RNA_LNCRNA_BIOTYPE[:]
        for item in DataConstants.RNA_MRNA_BIOTYPE:
            mRNABiotype = item
        wantedBiotypes.append( mRNABiotype)

        # Data for lncRNAs subtypes and mRNA
        # Note: this excludes biotypes such as misc_RNA and others, therefore some interactions will be excluded in this step.
        for biotype in sorted( wantedBiotypes):
            
            textScore = biotype
            textPartners = biotype
            
            if biotype in interactionsPerBiotype and len( interactionsPerBiotype[ biotype]) > 0:
                for txID in interactionsPerBiotype[ biotype]:
                    textPartners+= "," + str( len(interactionsPerBiotype[ biotype][ txID]) )
                    for protID in interactionsPerBiotype[ biotype][ txID]:
                        score = interactionsPerBiotype[ biotype][ txID][ protID]
                        textScore+= "," + str( score)
                        # print (biotype, txID, protID, score)
            else:
                textScore+= ",NA"
                textPartners+= ",NA"
                        
            outHandlerScore.write( textScore + "\n")
            outHandlerPartners.write( textPartners + "\n")

        outHandlerScore.close()
        outHandlerPartners.close()

        #=================================================================== 
        # File with interaction scores for each protein-RNA pair, matrix format
        #=================================================================== 
        # E.g.
        # RNAs Prot1 Prot2
        # RNA1 10.4    NA
        # RNA2 32.6    -34.5

        outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_INTERACTIONS_SCORE_MATRIX )

        # create data structures with all proteins, RNAs and scores of pairs 
        setInteractingRNAs = set()
        setInteractingProts = set()
        dictPairs = {}
        for inter in filteredInteractions:
            txID = str( inter.transcriptID)
            protID = str( inter.proteinID)
            interScore = float( inter.interactionScore)
            pair = txID + "|" + protID
            if pair not in dictPairs:
                dictPairs[pair] = interScore
            else:
                raise RainetException("interaction_report: duplicate interaction", pair)

            setInteractingRNAs.add( txID)
            setInteractingProts.add( protID)

        # use sorting to keep headers in place
        sortedSetInteractingProts = sorted( setInteractingProts)
        sortedSetInteractingRNAs = sorted( setInteractingRNAs)

        # write header with protein IDs
        outHandler.write( "RNAs")
        for prot in sortedSetInteractingProts:
            outHandler.write( "\t%s" % prot )
        outHandler.write( "\n")
            
        # write bulk of file, one row per rna, one column per protein
        for rna in sortedSetInteractingRNAs:
            text = rna
            for prot in sortedSetInteractingProts:
                tag = rna + "|" + prot
                if tag in dictPairs:
                    score = dictPairs[tag]
                else:
                    score = "NA"
                text+= "\t%s" % score 
            text+= "\n"
            outHandler.write( text)

        outHandler.close()
        

    # #
    # Retrieve statistics for the expression data used.
    # Produce output files that will be used for a pdf report
    def expression_report(self):
        
        #===================================================================    
        # File with average expression (among tissues) for each transcript, discrimination of RNA types and lncRNA subtypes
        #=================================================================== 
 
        filteredRNAs = DataManager.get_instance().get_data( AnalysisStrategy.FINAL_RNA_KW)
 
        outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_RNA_EXPRESSION )
         
        # Write header
        outHandler.write("transcriptID\ttype\ttranscriptBiotype\tmeanExpression\n") 
 
        expressionDataCounts = {} # stores counts of RNAs with or without expression data per RNA subtype
        for rna in filteredRNAs:
            # Get expression values on the several tissues for filtered transcript
            queryResult = self.sql_session.query( RNATissueExpression.expressionValue).filter( RNATissueExpression.transcriptID == rna.transcriptID).all()
 
            # Initialise dict to store existence/absence of data
            if rna.transcriptBiotype not in expressionDataCounts:
                expressionDataCounts[ rna.transcriptBiotype] = {}
                expressionDataCounts[ rna.transcriptBiotype]["with"] = 0
                expressionDataCounts[ rna.transcriptBiotype]["without"] = 0
 
            # if there is expression data for this transcript
            if queryResult != None and len(queryResult) > 0:
                expressionDataCounts[ rna.transcriptBiotype]["with"]+= 1
 
                # Array with the actual expression values
                expressionValues = [ result[0] for result in queryResult]        
                # Write into file the average expression value between tissues
                outHandler.write( "%s\t%s\t%s\t%.2f\n" % (rna.transcriptID, rna.type, rna.transcriptBiotype, sum(expressionValues)/len(expressionValues)) )
            else:
                # If is possible to have transcripts (from RNA table) that are not present in the "RNATissueExpression" table,
                # since we and GTEx are using different Ensembl/GENCODE releases and some transcripts were deprecated or are new.
                expressionDataCounts[ rna.transcriptBiotype]["without"]+= 1
 
        outHandler.close()
 
        #===================================================================    
        # File with percentage of transcript with expression data, discrimination of RNA types and lncRNA subtypes
        #=================================================================== 
 
        outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_RNA_EXPRESSION_DATA_PRESENCE )
 
        # Write header
        outHandler.write("subtype\ttx_with_expression_data\ttx_without_expression_data\tperc_tx_with_expression_data\n") 
 
        for subtype in expressionDataCounts:
            withExpression = expressionDataCounts[subtype]["with"]
            withoutExpression = expressionDataCounts[subtype]["without"]
            if withExpression > 0:
                perc = "%.2f%%" % (withExpression*100.0 / (withoutExpression+withExpression) )
            else:
                perc = "%.2f%%" % (0.0)
            outHandler.write("%s\t%i\t%i\t%s\n" % ( subtype, withExpression, withoutExpression, perc) )
         
        outHandler.close()

        #===================================================================    
        # File with numbers of proteins expressed per tissue
        #=================================================================== 
 
        try:
            protTissues = DataManager.get_instance().get_data( AnalysisStrategy.PROT_TISSUES_KW)
  
            outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_PROTEINS_EXPRESSED_PER_TISSUE )
       
            # Write header
            outHandler.write("tissue\tnumber_expressed\n") 
       
            proteinPot = set() # combine all proteins
       
            for tissue in protTissues:
                proteinPot = proteinPot.union( protTissues[ tissue])
                nProts = len( protTissues[ tissue])
                outHandler.write("%s\t%i\n" % ( tissue, nProts) )

            outHandler.write("# total %s proteins with expression data\n" % ( len( proteinPot)) )

            outHandler.close()

        # if there is no PROT_TISSUES_KW data
        except RainetException as e:
            Logger.get_instance().info( "expression_report : report on number of proteins expressed per tissue not performed. " + str( e))

        #===================================================================    
        # File with numbers of RNAs expressed per tissue
        #=================================================================== 

        try:
            rnaTissues = DataManager.get_instance().get_data( AnalysisStrategy.RNA_TISSUES_KW)
    
            outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_RNAS_EXPRESSED_PER_TISSUE )
       
            # Write header
            outHandler.write("tissue\tnumber_expressed\n") 
       
            rnaPot = set() # combine all proteins
       
            for tissue in rnaTissues:
                rnaPot = rnaPot.union( rnaTissues[ tissue])
                nRNAs = len( rnaTissues[ tissue])
                outHandler.write("%s\t%i\n" % ( tissue, nRNAs) )

            outHandler.write("# total %s rnas with expression data\n" % ( len( rnaPot)) )

            outHandler.close()

        # if there is no RNA_TISSUES_KW data
        except RainetException as e:
            Logger.get_instance().info( "expression_report : report on number of RNAs expressed per tissue not performed. " + str( e))

        #=================================================================== 
        # File with number of tissues where both partners of pair expressed
        # 
        # E.g. transcriptID_proteinID\tnumber_tissues\tlist_of_tissues
        #=================================================================== 
 
        try:
            interactionTissues = DataManager.get_instance().get_data( AnalysisStrategy.PRI_TISSUES_KW)
            outHandler = FileUtils.open_text_w( self.outputFolderReport + "/" + AnalysisStrategy.REPORT_TISSUES_WHERE_EXPRESSED )
    
            outHandler.write("interaction\tnumber_of_tissues\tlist_of_tissues\n")
     
            for inter in interactionTissues:
                outHandler.write("%s\t%s\t%s\n" % (str(inter) , len(interactionTissues[ inter]), ",".join( interactionTissues[ inter]) ) )
     
            outHandler.close()

            DataManager.get_instance().delete_data(AnalysisStrategy.PRI_TISSUES_KW)

        # if there is not such data
        except RainetException as e:
            Logger.get_instance().info( "expression_report : report on number of tissues where interaction expressed. " + str( e))

    # #
    # Run Rscript to produce Sweave file and consequent pdf report, using the data written by this script
    def write_report(self):
        
        # At this point all files should be written to file and R job can use large amounts of memory
        # Here we can delete the data manager python objects to save memory
        DataManager.get_instance().delete_data(AnalysisStrategy.RNA_ALL_KW)
        DataManager.get_instance().delete_data(AnalysisStrategy.RNA_FILTER_KW)
        DataManager.get_instance().delete_data(AnalysisStrategy.PROT_FILTER_KW)
        DataManager.get_instance().delete_data(AnalysisStrategy.PRI_FILTER_KW)

        # launch the analysis
        command = "cd " + AnalysisStrategy.R_WORKING_DIR + \
                 "; Rscript %s %s %s %s %s %s %s %s %s %s %s %s" % \
                 ( 
                     AnalysisStrategy.R_MAIN_SCRIPT, 
                     AnalysisStrategy.R_WORKING_DIR, 
                     AnalysisStrategy.R_SWEAVE_FILE, 
                     self.outputFolderReport,
                     AnalysisStrategy.PARAMETERS_LOG, 
                     AnalysisStrategy.REPORT_RNA_NUMBERS,
                     AnalysisStrategy.REPORT_RNA_EXPRESSION,
                     AnalysisStrategy.REPORT_RNA_EXPRESSION_DATA_PRESENCE,
                     AnalysisStrategy.REPORT_TISSUES_WHERE_EXPRESSED,
                     AnalysisStrategy.REPORT_INTERACTION_NUMBERS,                     
                     AnalysisStrategy.REPORT_INTERACTION_SCORES_BIOTYPE,
                     AnalysisStrategy.REPORT_INTERACTION_PARTNERS_BIOTYPE
                     )
                #--max-mem-size=2000M
    
        returnCode = SubprocessUtil.run_command( command)
        if returnCode:
            raise RainetException(" AnalysisStrategy.write_report : external command with return code:" + str( returnCode) )
        else:
            # copy pdf report to output folder
            # the filename of the produce report file using R's knit2pdf is always the same name but pdf extension
            reportFile = AnalysisStrategy.R_SWEAVE_FILE.replace(".Rnw",".pdf")
            shutil.copy( reportFile, self.outputFolderReport)


