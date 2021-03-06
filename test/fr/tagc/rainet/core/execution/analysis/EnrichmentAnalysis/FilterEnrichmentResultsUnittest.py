

import unittest
import os
import pandas as pd
import glob

from fr.tagc.rainet.core.Rainet import Rainet
from fr.tagc.rainet.core.util.log.Logger import Logger
from fr.tagc.rainet.core.util.option.OptionManager import OptionManager
from fr.tagc.rainet.core.util.data.DataManager import DataManager
from fr.tagc.rainet.core.util.sql.SQLManager import SQLManager
from fr.tagc.rainet.core.util.option import OptionConstants

from fr.tagc.rainet.core.execution.analysis.EnrichmentAnalysis.FilterEnrichmentResults import FilterEnrichmentResults

# #
# Unittesting. 
#
class FilterEnrichmentResultsUnittest(unittest.TestCase):

    # Constants with default paramters        
        
    # #
    # Runs before each test
    # name of this function needs forcely to be 'setUp'
    def setUp(self):

        # Set the options

        self.enrichmentPerRNAFile = "/home/diogo/workspace/tagc-rainet-RNA/test/fr/tagc/rainet/core/test_input/EnrichmentAnalysis/enrichment_per_rna.tsv"
        self.enrichmentResultsFile = "/home/diogo/workspace/tagc-rainet-RNA/test/fr/tagc/rainet/core/test_input/EnrichmentAnalysis/enrichment_results.tsv"
        self.outputFolder = "/home/diogo/workspace/tagc-rainet-RNA/test/fr/tagc/rainet/core/test_results/enrichmentAnalysis/FilterEnrichmentResults"
        self.matrixValueColumn = 7
        self.filterWarningColumn = 1
        self.filterWarningValue = "1.0"
        self.minimumRatio = "OFF"
        self.rowAnnotationFile = ""
        self.colAnnotationFile = ""
        self.maskMultiple = 1
        self.noAnnotationTag = "Other"
        self.noAnnotationFilter = 0
        self.annotSpecificityFilter = -1
        self.transcriptSpecificityFilter = -1
        self.minimumProteinInteraction = -1
        self.topEnrichmentsPerComplex = -1
        
        self.run = FilterEnrichmentResults( self.enrichmentPerRNAFile, self.enrichmentResultsFile, self.outputFolder, self.matrixValueColumn, self.filterWarningColumn, \
                                                          self.filterWarningValue, self.minimumRatio, self.rowAnnotationFile, self.colAnnotationFile, \
                                                          self.maskMultiple, self.noAnnotationTag, self.noAnnotationFilter, self.annotSpecificityFilter, \
                                                          self.transcriptSpecificityFilter, self.minimumProteinInteraction, self.topEnrichmentsPerComplex)

        
        self.expectedFolder = "/home/diogo/workspace/tagc-rainet-RNA/test/fr/tagc/rainet/core/test_expected/enrichmentAnalysis/FilterEnrichmentResults"
        
        
    def test_read_enrichment_per_rna_file(self):

        print "| test_read_enrichment_per_rna_file | "
                
        listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments = self.run.read_enrichment_per_rna_file()

        self.assertTrue( len( listRNASignificantEnrich) == 128, "assert that correct number of RNAs is read")
        
        self.assertTrue( countRealEnrichments == 41302, "assert that correct number of real enrichments is read")

        self.assertTrue( countRandomEnrichments - 37770.9 < 0.1, "assert that correct number of random enrichments is read")
        

    def test_read_enrichment_per_rna_file_two(self):

        print "| test_read_enrichment_per_rna_file_two | "
    
        self.run.minimumRatio = 2
    
        listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments = self.run.read_enrichment_per_rna_file()

        self.assertTrue( len( listRNASignificantEnrich) == 63, "assert correct number of significant RNAs after filter")
        

    def test_read_enrichment_results_file(self):
 
        print "| test_read_enrichment_results_file | "
         
        listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments = self.run.read_enrichment_per_rna_file()
 
        dictPairs, filteredEnrichmentResults = self.run.read_enrichment_results_file( listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments)
 
        testCount = 0       
        for line in filteredEnrichmentResults[1:]:
            
            spl = line.split("\t")
            if spl[0] == "ENST00000609548":
                testCount += 1
            
            self.assertTrue( spl[8] == "1")

        self.assertTrue( testCount == 71)


        # Same test but with ratio cutoff, which should exclude testing transcript
        self.run.minimumRatio = 2
        listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments = self.run.read_enrichment_per_rna_file()
        dictPairs, filteredEnrichmentResults = self.run.read_enrichment_results_file( listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments)

        testCount = 0       
        for line in filteredEnrichmentResults[1:]:
            spl = line.split("\t")
            if spl[0] == "ENST00000609548":
                testCount += 1
        self.assertTrue( testCount == 0)


    def test_read_enrichment_results_file_two(self):
 
        print "| test_read_enrichment_results_file_two | "
 
        # test minimum protein interaction optional parameter
        self.run.minimumProteinInteraction = 3
        
        listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments = self.run.read_enrichment_per_rna_file()
 
        dictPairs, filteredEnrichmentResults = self.run.read_enrichment_results_file( listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments)
 
        testCount = 0       
        for line in filteredEnrichmentResults[1:]:
            
            spl = line.split("\t")
            if spl[0] == "ENST00000609548":
                testCount += 1
            
            self.assertTrue( spl[8] == "1")

        self.assertTrue( testCount == 36)


    def test_filter_by_observed_interactions(self):
 
        print "| test_filter_by_observed_interactions | "
        
        self.run.topEnrichmentsPerComplex = 5
        
        listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments = self.run.read_enrichment_per_rna_file()
 
        dictPairs, filteredEnrichmentResults = self.run.read_enrichment_results_file( listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments)

        complexEnrichments, observedFilteredResults = self.run.filter_by_observed_interactions( filteredEnrichmentResults)

        # TEST1
        # Complex 26c only has enrichments with observed interactions = 2, therefore all enrichments should be picked
        # e.g. awk '$2=="26c"' enrichment_results.tsv | awk '$9=="1"'| awk '$3=="2"' | grep -f passing_rnas.txt | wc -l33
        self.assertTrue( len( complexEnrichments["26c"]) == 1)       
        self.assertTrue( len( complexEnrichments["26c"][2]) == 33, "number of enrichments from this complex from RNAs that pass enrichment_per_rna, no observed interations filter applied in this case")

        # TEST2
        # Complex 4a has 30 enrichments (after enrichment_per_rna filter) and 15 different values for observed interactions, therefore some enrichments should be filtered out
        # e.g. awk '$2=="4a"' enrichment_results.tsv | awk '$9=="1"' | awk '$6=="0"' | grep -f passing_rnas.txt | wc -l 30
        self.assertTrue( len( complexEnrichments["4a"]) == 15)
        # picking 5% top, we should have at least 6 enrichments picked. From 26, 25 and 24 observed interactions. Since 24 bin has 5 enrichments, all will be picked
        self.assertTrue( len( complexEnrichments["4a"][26]) == 2)
        self.assertTrue( len( complexEnrichments["4a"][25]) == 2)
        self.assertTrue( len( complexEnrichments["4a"][24]) == 5)

        countEnrich = 0
        enrichText = ""
        for enrich in observedFilteredResults:
            spl = enrich.split("\t")
            annotID = spl[1]
            if annotID == "4a":
                countEnrich += 1
                self.assertTrue( int( spl[2]) >= 24, "asserting that all observed interaction values are >= 24")
                enrichText += enrich

        self.assertTrue( "ENST00000594590" in enrichText)
        self.assertTrue( countEnrich == 2, "asserting correct number of enrichments after filtering")
        
        # TEST3
        # test combination of minimumProteinInteraction and topEnrichmentsPerComplex

        self.run.topEnrichmentsPerComplex = 5
        self.run.minimumProteinInteraction = 10
        
        listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments = self.run.read_enrichment_per_rna_file()
        dictPairs, filteredEnrichmentResults = self.run.read_enrichment_results_file( listRNASignificantEnrich, countRealEnrichments, countRandomEnrichments)
        complexEnrichments, observedFilteredResults = self.run.filter_by_observed_interactions( filteredEnrichmentResults)

        # all enrichments of complex 26c should be filtered out since they all have <5 observed interactions
        self.assertTrue( "26c" not in complexEnrichments)

        # complex 4c
        self.assertTrue( len( complexEnrichments["4a"]) == 15 - 2, "assert that some observed interactions bins have been lost" )
        
        
    def test_run(self):
  
        print "| test_run | "        
  
        self.run.minimumRatio = 2.0 
        self.run.matrixValueColumn = 8 
        self.run.filterWarningValue = 0
  
        self.run.run()

        ## expected files

        # check if output files are correct
        with open(self.outputFolder + FilterEnrichmentResults.REPORT_LIST_RNA_SIGN_ENRICH, "r") as out:                
            with open(self.expectedFolder + FilterEnrichmentResults.REPORT_LIST_RNA_SIGN_ENRICH, "r") as exp:
                self.assertTrue(out.read() == exp.read(), "assert if report file is correct, by expected content comparison" )
         
        # check if output files are correct
        with open(self.outputFolder + FilterEnrichmentResults.REPORT_FILTERED_RNA_ANNOT_RESULTS, "r") as out:                
            with open(self.expectedFolder + FilterEnrichmentResults.REPORT_FILTERED_RNA_ANNOT_RESULTS, "r") as exp:
                self.assertTrue(out.read() == exp.read(), "assert if report file is correct, by expected content comparison" )


        # check if output files are correct
        with open(self.outputFolder + FilterEnrichmentResults.REPORT_RNA_ANNOT_RESULTS_MATRIX, "r") as out:                
            with open(self.expectedFolder + FilterEnrichmentResults.REPORT_RNA_ANNOT_RESULTS_MATRIX, "r") as exp:
                self.assertTrue(out.read() == exp.read(), "assert if report file is correct, by expected content comparison" )

        # check if output files are correct
        with open(self.outputFolder + FilterEnrichmentResults.REPORT_SPECIFICITY_RANK, "r") as out:                
            with open(self.expectedFolder + FilterEnrichmentResults.REPORT_SPECIFICITY_RANK, "r") as exp:
                self.assertTrue(out.read() == exp.read(), "assert if report file is correct, by expected content comparison" )

#         # check if output files are correct
#         with open(self.outputFolder + FilterEnrichmentResults.REPORT_SPECIFICITY_FILTERED_RNA_ANNOT_RESULTS, "r") as out:                
#             with open(self.expectedFolder + FilterEnrichmentResults.REPORT_SPECIFICITY_FILTERED_RNA_ANNOT_RESULTS, "r") as exp:
#                 self.assertTrue(out.read() == exp.read(), "assert if report file is correct, by expected content comparison" )

        # check if output files are correct
        with open(self.outputFolder + FilterEnrichmentResults.REPORT_ENRICHMENT_SUMMARY, "r") as out:                
            with open(self.expectedFolder + FilterEnrichmentResults.REPORT_ENRICHMENT_SUMMARY, "r") as exp:
                self.assertTrue(out.read() == exp.read(), "assert if report file is correct, by expected content comparison" )


    def test_write_enrichment_results(self):
  
        print "| test_write_enrichment_results | "        
  
        ## ADD SPECIFICITY AND TOP SCAFFOLD FILTERS AND SEE IF OUTPUT CHANGES
        # Note: the filters themselves are not being tested here, just that output file formats look correct 

        self.expectedFolder = "/home/diogo/workspace/tagc-rainet-RNA/test/fr/tagc/rainet/core/test_expected/enrichmentAnalysis/FilterEnrichmentResults/with_parameters"

  
        self.run.minimumRatio = 2.0 
        self.run.matrixValueColumn = 8 
        self.run.filterWarningValue = 0

        self.run.annotSpecificityFilter = 10
        self.run.transcriptSpecificityFilter = 10
        self.run.minimumProteinInteraction = 10
        self.run.topEnrichmentsPerComplex = 10
  
        self.run.run()

        ## expected files

        # check if output files are correct
        with open(self.outputFolder + FilterEnrichmentResults.REPORT_LIST_RNA_SIGN_ENRICH, "r") as out:                
            with open(self.expectedFolder + FilterEnrichmentResults.REPORT_LIST_RNA_SIGN_ENRICH, "r") as exp:
                self.assertTrue(out.read() == exp.read(), "assert if report file is correct, by expected content comparison" )
         
        with open(self.outputFolder + FilterEnrichmentResults.REPORT_FILTERED_RNA_ANNOT_RESULTS, "r") as out:                
            with open(self.expectedFolder + FilterEnrichmentResults.REPORT_FILTERED_RNA_ANNOT_RESULTS, "r") as exp:
                self.assertTrue(out.read() == exp.read(), "assert if report file is correct, by expected content comparison" )

        with open(self.outputFolder + FilterEnrichmentResults.REPORT_RNA_ANNOT_RESULTS_MATRIX, "r") as out:                
            with open(self.expectedFolder + FilterEnrichmentResults.REPORT_RNA_ANNOT_RESULTS_MATRIX, "r") as exp:
                self.assertTrue(out.read() == exp.read(), "assert if report file is correct, by expected content comparison" )

        with open(self.outputFolder + FilterEnrichmentResults.REPORT_SPECIFICITY_RANK, "r") as out:                
            with open(self.expectedFolder + FilterEnrichmentResults.REPORT_SPECIFICITY_RANK, "r") as exp:
                self.assertTrue(out.read() == exp.read(), "assert if report file is correct, by expected content comparison" )

        with open(self.outputFolder + FilterEnrichmentResults.REPORT_ENRICHMENT_SUMMARY, "r") as out:                
            with open(self.expectedFolder + FilterEnrichmentResults.REPORT_ENRICHMENT_SUMMARY, "r") as exp:
                self.assertTrue(out.read() == exp.read(), "assert if report file is correct, by expected content comparison" )


#     def test_extra(self):
#   
#         self.run.catrapidFile = "/home/diogo/Documents/RAINET_data/TAGC/rainetDatabase/results/ReadCatrapid/Ensembl82/lncrna/cutoff50/Corum_Havugimana/storedInteractions.tsv"
#         self.run.numberRandomizations = 1
#         self.run.topPartners = 50
#         self.run.run()


     
#     # #
#     # Runs after each test
#     def tearDown(self):
#                                  
#         # Wipe output folder
#         cmd = "rm %s/*" % self.outputFolder
#         os.system(cmd)
             
       



