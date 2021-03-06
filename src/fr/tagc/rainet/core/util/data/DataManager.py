
import inspect

from fr.tagc.rainet.core.util.log.Logger import Logger
from fr.tagc.rainet.core.util.exception.RainetException import RainetException
from fr.tagc.rainet.core.util.sql.SQLManager import SQLManager
from fr.tagc.rainet.core.data import DataConstants

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
from fr.tagc.rainet.core.data.RNACrossReference import RNACrossReference
from fr.tagc.rainet.core.data.MRNA import MRNA
from fr.tagc.rainet.core.data.LncRNA import LncRNA
from fr.tagc.rainet.core.data.OtherRNA import OtherRNA
from fr.tagc.rainet.core.data.ProteinRNAInteractionCatRAPID import ProteinRNAInteractionCatRAPID
from fr.tagc.rainet.core.data.ProteinCrossReference import ProteinCrossReference
from fr.tagc.rainet.core.data.InteractingRNA import InteractingRNA
from fr.tagc.rainet.core.data.InteractingProtein import InteractingProtein

from sqlalchemy.inspection import inspect
import types



# #
# This class is a singleton aiming to manage the data retrieve from internal database queries.
# e.g. storing in memory a list of RNAs for easier accession.
class DataManager( object ) :

    __instance = None
    
    # #
    # Constructor of the Factory
    #
    def __init__( self ):

        #keys of dictionary, given by user, will point to query / data result
        self.data = {} 
        

    # #
    # Make SQL query to database and store query results.
    #
    # @param query_string: string - The query string
    #
    # @raise RainetException if the query failed to execute
    def perform_query(self, keyword, query_string):

        sql_session = SQLManager.get_instance().get_session()

        full_query = 'sql_session.' + query_string
        
        Logger.get_instance().info( "DataManager.init : query is '" + full_query + "'")

        try:
            query_result = eval( full_query)
        except Exception as ex:
            raise RainetException( "DataManager.init : Exception occurred during query on DB",ex  )

        self.data[keyword] = query_result

    # #
    # Process previously stored results into a key-value dictionary of lists
    #
    # @param keyword : String - the data dictionary keyword to access the data
    # @param col1 : Int - 0-based column index to be used as key in the dict
    # @param col2 : Int - 0-based column index to be used as value in the dict
    #
    # @raise RainetException if the keyword is not present
    def query_to_dict(self, keyword, col1, col2):

        outDict = {}
        
        if keyword in self.data:
            data = self.data[keyword]
        else:
            raise RainetException("DataManager.query_to_dict : Data keyword does not exist: "+keyword)            
        
        try:
            for entry in data:
                if col1 > len(entry) or col2 > len(entry):
                    raise RainetException("DataManager.query_to_dict : requested columns out of boundaries of query result: "+entry)            
                
                keyItem = str(entry[col1])
                valueItem = str(entry[col2])
    
                if keyItem not in outDict:
                    outDict[keyItem] = []
                outDict[keyItem].append(valueItem)
        except:
            raise RainetException("DataManager.query_to_dict : query result is not iterable: "+keyword)            


        self.data[keyword] = outDict


    # #
    # Process previously stored results into a dictionary,
    # where key to use is given in the parameter (but should be unique identifier / primary key),
    # and the value is the object with that key.
    #
    # Assuming unique identifiers for each object, throws warning if not, keeps first found.
    #
    # @param keyword : String - the data dictionary keyword to access the data, the data should be a result 
    #                  from a SQL query which returns SQL alchemy class objects and be iterable.
    # @param identifier : String - entry identifier / attribute to be used as key in the dict
    #
    # @raise RainetException if the keyword is not present, if data is not iterable, other issues.
    def query_to_object_dict(self, keyword, identifier):

        outDict = {}
        
        if keyword in self.data:
            data = self.data[ keyword]
        else:
            raise RainetException( "DataManager.query_to_object_dict : Data keyword does not exist: " + keyword)            

        if not hasattr( data, '__iter__'):
            raise RainetException( "DataManager.query_to_object_dict : query result is not iterable: " + keyword)   
        
        for entry in data:            
            if not hasattr(entry, '__class__'):
                raise RainetException( "DataManager.query_to_object_dict : provided keyword does not point to a container of class objects : " + keyword)
                            
            if identifier not in vars( entry):
                raise RainetException( "DataManager.query_to_object_dict : requested identifier keyword not found as object attribute: " + str( identifier) )            
            
            keyItem = str( eval( "entry."+ identifier ))
            valueItem = entry

            if keyItem not in outDict:
                outDict[ keyItem] = valueItem
            else:
                Logger.get_instance().warning( "DataManager.query_to_object_dict : Duplicated dictionary key : " + keyItem)

        self.data[keyword] = outDict


    # #
    # Process previously stored results into a key-value dictionary of lists
    #
    # @param keyword : String - the data dictionary keyword to access the data
    # @param col : Int - 0-based column index to be used as key in the set
    #
    # @raise RainetException if the keyword is not present or incorrect format
    def query_to_set(self, keyword, col):

        outSet = set()

        if keyword in self.data:
            data = self.data[keyword]
        else:
            raise RainetException("DataManager.query_to_set : Data keyword does not exist: "+keyword)            

        try:
            int(col)
        except TypeError:
            raise RainetException("DataManager.query_to_set : Column index needs to be integer: "+col)
                    

        try:
            for entry in data:
                if col > len(entry):
                    raise RainetException("DataManager.query_to_set : requested columns out of boundaries of query result: "+entry)            
                
                keyItem = str(entry[col])
    
                if keyItem in outSet:
                    Logger.get_instance().debug("DataManager.query_to_set : duplicate key in set: "+keyItem)

                outSet.add(keyItem)

        except:
            raise RainetException("DataManager.query_to_set : query result is not iterable: "+keyword)            

        self.data[keyword] = outSet


    # #
    # Store any type of data (object) on DataManager.data into provided a dictionary keyword
    #
    # @param keyword: the data dictionary keyword to access the data
    #
    def store_data(self, keyword, data):
        
        try:
            keyword = str(keyword)
        except:
            raise RainetException("DataManager.get_data : keyword must be a string.")
        
        self.data[keyword] = data


    # #
    # Get previously stored results
    #
    # @param keyword: the data dictionary keyword to access the data
    #
    # @raise RainetException if the keyword is not present
    def get_data(self, keyword):
        
        try:
            keyword = str(keyword)
        except:
            raise RainetException("DataManager.get_data : keyword must be a string.")
        
        if keyword not in self.data:
            raise RainetException("DataManager.get_data : Data keyword does not exist: "+keyword)
            
        return self.data[keyword]

    # #
    # Delete previously stored results
    #
    # @param keyword: the data dictionary keyword to access the data
    #
    # @raise RainetException if the keyword is not present
    def delete_data(self, keyword):
        
        try:
            keyword = str(keyword)
        except:
            raise RainetException("DataManager.delete_data : keyword must be a string.")
        
        if keyword in self.data:
            del self.data[keyword]
        else:
            raise RainetException("DataManager.delete_data : Data keyword does not exist: "+keyword)
            

    # #
    # Returns the singleton instance
    #
    # @return the singleton instance        
    @staticmethod
    def get_instance():

        if DataManager.__instance == None:
            DataManager.__instance = DataManager()
        return DataManager.__instance

