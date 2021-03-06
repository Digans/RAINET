import sys
import os
import argparse
import glob
import numpy as np
import random 
import pandas as pd
from scipy import stats

from fr.tagc.rainet.core.util.file.FileUtils import FileUtils
from fr.tagc.rainet.core.util.exception.RainetException import RainetException
from fr.tagc.rainet.core.util.log.Logger import Logger
from fr.tagc.rainet.core.util.time.Timer import Timer
from fr.tagc.rainet.core.util.subprocess.SubprocessUtil import SubprocessUtil

from sqlalchemy import or_,and_
from fr.tagc.rainet.core.util.sql.SQLManager import SQLManager
from fr.tagc.rainet.core.data.Protein import Protein
from fr.tagc.rainet.core.data.ProteinInteraction import ProteinInteraction
from fr.tagc.rainet.core.data.ProteinCrossReference import ProteinCrossReference
from fr.tagc.rainet.core.data.RNACrossReference import RNACrossReference
from fr.tagc.rainet.core.util.data.DataManager import DataManager

#===============================================================================
# Started 06-May-2016 
# Diogo Ribeiro
# Variant of NPInterPredictionValidation for dumping interactions
# Purpose is to have list of NPInter transcripts that interact with proteins in catRAPID library, 
# so that I can have new list of transcripts on where to run catRAPID omics anew
#===============================================================================

class NPInterPredictionValidation( object ):

    # Class constants
    SPECIES = "Homo sapiens"
    TAG = "ncRNA-protein binding"
    INTERACTION_LEVEL = "RNA-Protein"
    MOLECULEADATABASE = "NONCODE"
    DISTRIBUTION_SCRIPT = "/home/diogo/workspace/tagc-rainet-RNA/src/fr/tagc/rainet/core/execution/processing/knownScaffoldExamples/NPInter_stats.R"
    
    def __init__(self, catrapidFile, npinterFile, noncodeTx2noncodeGene, noncode2ensembl, rainetDB, outputFolder):

        self.catrapidFile = catrapidFile
        self.npinterFile = npinterFile
        self.noncodeTx2noncodeGene = noncodeTx2noncodeGene
        self.noncode2Ensembl = noncode2ensembl
        self.rainetDB = rainetDB
        self.outputFolder = outputFolder
    
        # Build a SQL session to DB
        SQLManager.get_instance().set_DBpath(self.rainetDB)
        self.sql_session = SQLManager.get_instance().get_session()


    # #
    # Use RAINET DB to retrieve Protein cross references
    def proteins_in_rainet(self):
        
        # Query all UniProtAC in database
        query = self.sql_session.query( Protein.uniprotAC ).all()        
        uniprotACs = { str(prot[0]) for prot in query}

        # # Get external references
        # produce dictionary where key is xref ID and value the uniprotAC
        # Note: an external ID can point to several uniprot IDs        
        query = self.sql_session.query( ProteinCrossReference.protein_id, ProteinCrossReference.crossReferenceID ).all()

        protCrossReference = {} # key -> external ID, val -> set of uniprotACs        
        for uniprotID, externalID in query:     
            # There is a significant amount of RefSeq IDs being used in our input file, however these have to be processed       
            if externalID.startswith("NM_"):
                externalID = externalID.split(".")[0] # NM_001244871.1 to NM_001244871

            if externalID not in protCrossReference:
                protCrossReference[ externalID] = set()
                
            protCrossReference[ externalID].add( str( uniprotID))

        return uniprotACs, protCrossReference


    # #
    # Use RAINET DB to retrieve RNA cross references
    def rna_cross_references(self):
        
        # RNA Cross reference query, using refseq_ncrna as database
        query = self.sql_session.query( RNACrossReference.transcriptID, RNACrossReference.crossReferenceID ).filter( RNACrossReference.sourceDB == 'refseq_ncrna').all()
        
        rnaCrossReference = {} # key -> refseq ID, val -> ensembl ID
        # Note: an external ID can point to several ensembl IDs        
        
        for ensemblID, refseqID in query:
            if refseqID not in rnaCrossReference:
                rnaCrossReference[ refseqID] = []
                
            rnaCrossReference[ refseqID].append( ensemblID)

        return rnaCrossReference

              
    # #
    # Read the NONCODE ID conversion files
    def read_noncode_conversion_file( self):

        # Notes:
        # - The NPInter file contains NONCODE Gene IDs
        # - NONCODE provides conversion of NONCODE Transcript IDs (not gene IDs) to Ensembl transcript IDs
        # - NONCODE provides conversion of NONCODE Transcript IDs to NONCODE Gene IDs
        # What I need is, for each NPInter NONCODE Gene ID, a list of Ensembl transcript IDs

        #===================================================================        
        ## 1) Read NONCODE transcript to NONCODE Gene ID
        # e.g. NONHSAT000019.2 NONHSAG000008.2
        #===================================================================

        transcript2GeneDict = {} # key -> noncode tx ID, val -> gene ID
        with open( self.noncodeTx2noncodeGene, "r") as f:
            for line in f:
                line = line.strip()
                spl = line.split("\t")
                
                txID = spl[0]
                geneID = spl[1] #e.g. NONHSAG016453.1
                
                # to match against the IDs in the NPInter file, I need to remove the Gene "isoform" tag
                geneID = geneID.split(".")[0] # e.g. NONHSAG016453

                # there are duplicate lines
                if txID not in transcript2GeneDict:
                    transcript2GeneDict[ txID] = geneID
                else:
                    # if duplicate lines point to different IDs
                    if not transcript2GeneDict[ txID] == geneID:
                        raise RainetException( "Conflicting ID matching, duplicate tx ID: " + line)
           
        #===================================================================
        ## 2) Read NONCODE transcript ID to Ensembl transcript ID        
        # e.g. NONHSAT000012.1 ensembl ENST00000469289
        #===================================================================

        conversionDict = {} # key -> NONCODE Gene ID, val -> list of Ensembl IDs

        with open( self.noncode2Ensembl, "r") as f:
            for line in f:
                line = line.strip()
                spl = line.split("\t")

                noncodeID = spl[0]                
                sourceDB = spl[ 1]
                externalID = spl[ 2]

                # We only want Human IDs
                if not noncodeID.startswith( "NONHSAT"):
                    continue

                # We can only use IDs that have an associated gene
                if noncodeID in transcript2GeneDict:
                    geneID = transcript2GeneDict[ noncodeID]
                else:
                    continue
                    # raise RainetException( "NONCODE transcript ID lacking gene information: " + line)
                
                if sourceDB == "ensembl":                    
                    # sometimes there is two Ensembl IDs in same line, for same NONCODE ID
                    # sometimes there is two Ensembl IDs for same NONCODE ID, in separate lines
                    ensIDs = externalID.split(",")
                    for ensID in ensIDs:
                        if not ensID.startswith( "ENST"):
                            raise RainetException( "Provided ID does not start with ENST: " + line)
                elif sourceDB == "refseq":
                    # one refseq ID can correspond to several Ensembl IDs
                     
                    if len(externalID.split(",")) > 1:
                        raise RainetException( "RefSeq with unknown format ", externalID)
 
                    if externalID in self.rnaXrefDict:
                        ids = self.rnaXrefDict[ externalID]
                    else:
                        # these are refseq transcripts with no associated Ensembl ID. Cannot map them
                        # print "NOT FOUND", externalID    
                        continue
 
                    ensIDs = set()
 
                    for i in ids:
                        if not i.startswith( "ENST"):
                            raise RainetException( "Provided ID does not start with ENST: " + line)
                        else:
                            ensIDs.add( str(i))
                else:
                    # We only use Ensembl or refseq as cross reference
                    continue


                if geneID not in conversionDict:
                    conversionDict[ geneID] = set()

                # add any ensemblID associated to gene
                conversionDict[ geneID].update( set( ensIDs) )
                # conversionDict[ geneID].extend( ensIDs)

        print "Number of NONCODE genes: ",len(conversionDict)

        self.conversionDict = conversionDict

        
    # #
    # Read NPInter file and retrieve list of proteins interacting with wanted RNA
    def read_NPInter_file(self):
        
        # Note: NPInter uses NONCODE database for transcript IDs, but in fact uses their Gene IDs, not the transcript IDs
           
        #===================================================================
        # Read NPInter file using header line 
        #===================================================================
        table = pd.read_table( self.npinterFile, header = 0, sep = "\t", skip_blank_lines = True)

        print "read_NPInter_file: Number interactions before any filter:",len(table)
 
        filteredTable = table.copy()
          
        #===================================================================
        # Field filtering on NPInter data
        #===================================================================
        # Note: assuming that moleculeB is always the molecule interacting with the RNA
          
        # filter by interaction class / type # interactions should be direct / physical
        # filteredTable = filteredTable.loc[filteredTable["tag"].str.contains( NPInterPredictionValidation.TAG)]
        filteredTable = filteredTable.loc[filteredTable["tag"] == NPInterPredictionValidation.TAG]
          
        # species must be "Homo sapiens"
        # Note: the species tag seems to be respective of the RNA (or moleculeA), the moleculeB may still be from other species
        filteredTable = filteredTable.loc[filteredTable["species"] == NPInterPredictionValidation.SPECIES] 
 
        # InteractionLevel must be "RNA-Protein" # this will be present in all cases where tag is ncRNA-Protein binding
        filteredTable = filteredTable.loc[filteredTable["InteractionLevel"] == NPInterPredictionValidation.INTERACTION_LEVEL] 
 
        # moleculeAdatabase must be "NONCODE"
        filteredTable = filteredTable.loc[filteredTable["moleculeAdatabase"] == NPInterPredictionValidation.MOLECULEADATABASE] 
 
        print "read_NPInter_file: Number interactions after molecule database, type and species filter:",len(filteredTable)

        #===================================================================
        # Retrieve set of wanted interactions, by RNA identifiers
        #===================================================================        

        wantedLines = []

        for index, row in filteredTable.iterrows(): # 06-Mai-2016 this was: for index, row in table.iterrows():
            noncodeID = str(row["moleculeAID"])
                    
            if noncodeID in self.conversionDict:            
                protDB = row["moleculeBdatabase"]
                protID = row["moleculeBID"]
                experiment = row["experiment"]
                
                for ensemblID in self.conversionDict[ noncodeID]:
                    wantedLines.append( [ensemblID, protDB, protID, experiment])
                #print row["moleculeAID"]
            else:
                # some IDs are not found in mapping file.
                # in fact, always that NPInter file uses NONCODE transcript ID (instead of NONCODE gene ID), these are not present in NONCODE mapping file.
                pass
#                 if "HSAT" in noncodeID:
#                     print noncodeID

        print "read_NPInter_file: Number of interactions after RNA processing: ", len(wantedLines)

        
        #===================================================================
        # Retrieve set of interacting proteins
        #===================================================================        
        # Note: checking if protein is in RAINET database, to be sure protein is Human, 
        # and to be coherent/fair between catRAPID and NPInter predictions
 
        interactingPairs = {} # key -> pair of transcriptID and proteinID, val -> count of interactions
        setOfRNAs = set()
        setOfProts = set()
 
        for tup in wantedLines: #[noncodeID, protDB, protID]
            ensemblID = tup[0]
            proteinDB = tup[1]
            proteinID = tup[2]

            # Get experiment/ method type used
            try:
                experiments = set(tup[3].split(";") ) #e.g. RIP;PAR-CLIP;RNA interference
                # exclude entries where there is several methods for same interaction (for simplicity)
                if len( experiments) > 1:
                    experiments = set(["NULL"])
            except AttributeError:
                experiments = set(["NULL"])

            if type( proteinID) == float:
                # numpy nan
                continue

            # map protein ID             
            if proteinDB == "UniProt":
                if proteinID not in self.uniprotACs:
                    # for example this can be protein that belongs to mouse. The previous species filter was relative to the RNA
                    # print "read_NPInter_file: ProteinID not found in RAINET database. Using original proteinID: ", proteinID
                    pass
                pair = ensemblID + "|" + proteinID
                if pair not in interactingPairs:
                    interactingPairs[ pair] = set()
                interactingPairs[ pair].update( experiments )
                setOfRNAs.add( ensemblID)
                setOfProts.add( proteinID)
            else:
                # If database is different than Uniprot, try find uniprotAC using CrossReferences table                
                # lookup ID in crossreferences table and switch to uniprotAC
                if proteinID in self.xrefDict:
                    proteinIDs = self.xrefDict[ proteinID]
                    # proteinID can be a set of IDs if using cross references
                    for protID in proteinIDs:
                        pair = ensemblID + "|" + protID
                        if pair not in interactingPairs:
                            interactingPairs[ pair] = set()
                        interactingPairs[ pair].update( experiments )
                        setOfRNAs.add( ensemblID)
                        setOfProts.add( protID)
 
        print "read_NPInter_file: Total number of interacting pairs:",len(interactingPairs)
        print "read_NPInter_file: Total number of interacting RNAs:",len(setOfRNAs)
        print "read_NPInter_file: Total number of interacting proteins:",len(setOfProts)
  
        return interactingPairs


    # #
    # Read catRAPID file, match peptide IDs to protein IDs, retrieve scores.
    def read_catrapid_file(self):


        interactingPairs = {} # key -> pair of transcriptID and proteinID, val -> maximum interaction score
        
        #e.g. 1       1       ENSP00000269701_ENST00000456726 -266.23 0.986

        peptideIDNotFound = set()
        proteinSet = set()
        transcriptSet = set()
        
        with open( self.catrapidFile, "r") as f:
            for line in f:
                spl = line.split( "\t")
                
                splIDs = spl[2].split("_")
                peptideID = splIDs[0]
                transcriptID = splIDs[1]
                intScore = float( spl[3] )

                if peptideID in self.xrefDict:
                    proteinID = self.xrefDict[ peptideID]
                    if len( proteinID) == 1:
                        #proteinID = next( iter( proteinID))
                        proteinID, = proteinID # unpacking set
                    else:
                        raise RainetException( "ENSP should point to a single UniProtID: " + line)                        
                else:
                    #print "read_catrapid_file: PeptideID not found in RAINET database: ", peptideID 
                    peptideIDNotFound.add( peptideID)
                    continue

                pair = transcriptID + "|" + proteinID

                proteinSet.add( proteinID)
                transcriptSet.add( transcriptID)

                # add pair to interacting pairs and keep the maximum interaction score
                if pair not in interactingPairs:
                    interactingPairs[ pair] = float("-inf")
                if intScore > interactingPairs[ pair]:
                    interactingPairs[ pair] = intScore

        print "read_catrapid_file: Number of peptideIDs not found in RAINET DB: ", len( peptideIDNotFound) # for old catRAPID dataset, 243 is expected
        print "read_catrapid_file: Number of proteins: ", len( proteinSet)
        print "read_catrapid_file: Number of transcripts: ", len( transcriptSet)
        print "read_catrapid_file: Number of protein-RNA pairs in catRAPID: ", len( interactingPairs)

        return interactingPairs, proteinSet, transcriptSet


if __name__ == "__main__":
    
    try:
        # Create Logger instance by using the first log action.
        Logger.get_instance().info( "NPInterPredictionValidation : Starting..." )

        #===============================================================================
        # Get input arguments, initialise class
        #===============================================================================
        parser = argparse.ArgumentParser(description='# Script to see if catRAPID predictions distinguish NPInter interactions from non-NPInter interactions ') 

        # positional args
        parser.add_argument('catRAPIDFile', metavar='catRAPIDFile', type=str,
                             help='File path of CatRAPID omics/fragments results from the webserver.')
        parser.add_argument('NPInterFile', metavar='NPInterFile', type=str,
                             help='File path of NPInter file. E.g. golden_set_NPInter[v3.0].txt')
        parser.add_argument('noncodeTx2noncodeGene', metavar='noncodeTx2noncodeGene', type=str,
                             help='File path for TSV file with conversion between NONCODE transcript ID (column 0) and Ensembl transcript ID (column 2).')    
        parser.add_argument('noncode2Ensembl', metavar='noncode2Ensembl', type=str,
                             help='File path for TSV file with conversion between NONCODE transcript ID (column 0) and Ensembl transcript ID (column 2).')    
        parser.add_argument('rainetDB', metavar='rainetDB', type=str, help='Path to RAINET database to be used.')
        parser.add_argument('outputFolder', metavar='outputFolder', type=str,
                             help='Folder where to write output files.')
        
        #gets the arguments
        args = parser.parse_args( ) 

        # Initialise class
        run = NPInterPredictionValidation( args.catRAPIDFile, args.NPInterFile, args.noncodeTx2noncodeGene, args.noncode2Ensembl, args.rainetDB, args.outputFolder)

        #===============================================================================
        # Run analysis / processing
        #===============================================================================
         
        # Start chrono
        Timer.get_instance().start_chrono()
 
        Timer.get_instance().step( "reading RAINET DB file..")    

        # Build RNA cross references
        run.rnaXrefDict = run.rna_cross_references()

        # Build Protein cross references
        run.uniprotACs, run.xrefDict = run.proteins_in_rainet()

        Timer.get_instance().step( "reading NONCODE file..")    

        run.read_noncode_conversion_file()

        Timer.get_instance().step( "reading NPInter file..")    

        npinterPairs = run.read_NPInter_file()

        Timer.get_instance().step( "reading catRAPID file..")    

        catrapidPairs, catrapidProteinSet, catrapidTranscriptSet = run.read_catrapid_file()

        outFile = open( run.outputFolder + "/interacting_pairs.txt", "w" )

        for pair in npinterPairs:
            transcript, protein = pair.split("|")

            if protein in catrapidProteinSet:
                if transcript not in catrapidTranscriptSet:
                    outFile.write( "%s\t%s\n" % ( transcript, protein))

        outFile.close()

    # Use RainetException to catch errors
    except RainetException as rainet:
        Logger.get_instance().error( "Error during execution of NPInterPredictionValidation. Aborting :\n" + rainet.to_string())

    # Stop the chrono      
    Timer.get_instance().stop_chrono( "NPInterPredictionValidation : Finished" )

