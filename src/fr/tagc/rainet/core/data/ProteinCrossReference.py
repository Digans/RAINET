
from sqlalchemy import Column, String, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy import or_

from fr.tagc.rainet.core.util.sql.Base import Base
from fr.tagc.rainet.core.util.sql.SQLManager import SQLManager
from fr.tagc.rainet.core.util.exception.RainetException import RainetException
from fr.tagc.rainet.core.util.exception.NotRequiredInstantiationException import NotRequiredInstantiationException

# #
# This class describes a cross reference of a protein i.e. the association of the protein identification
# in a specific database to the protein Uniprot Accession Number
#
class ProteinCrossReference( Base ):
    __tablename__ = 'ProteinCrossReference'
    
    # The base Protein
    protein_id = Column( String, ForeignKey( 'Protein.uniprotAC' ) )
    # The database the information was obtained from
    sourceDB = Column( String )
    # The cross reference
    crossReferenceID = Column( String )
    # Define the Composite PrimaryKey
    __table_args__ = (
        PrimaryKeyConstraint('protein_id', 'sourceDB', "crossReferenceID"),
    )
    
    #
    # The constructor of the class
    #
    # @param protein_acc : string - The ID of the domain
    # @param db_source : string - The database name from which the domain was retrieved
    # @param cross_reference : string - The cross reference ID
    def __init__(self, protein_acc, db_source, cross_reference):
        
        # Get a SQLalchemy session
        sql_session = SQLManager.get_instance().get_session()

        # Control if protein ACC contains a isoform code (like for instance P31496-1 instead of P31496)
        # If so, keep only the root name (the part before the "-") as protein ACC
        try:
            index_dash = protein_acc.index("-")
            protein_acc = protein_acc[0:index_dash]
        except ValueError:
            pass
        
        # Retrieve the list of Protein corresponding to the provided accession number
        from fr.tagc.rainet.core.data.Protein import Protein
        protein_list = sql_session.query( Protein).filter( or_( Protein.uniprotAC == protein_acc, Protein.uniprotID == protein_acc)).all()

        # If a single protein exists with the given accession number, check if a similar
        # cross reference exists in the database (may be true due to protein isoform uniprotACC which is cut) 
        # If the cross reference does not exist, a new ProteinCrossReferenceObject with the right value and add it to the Protein
        # cross reference list
        if protein_list != None and len( protein_list) == 1 :
            protein = protein_list[0]
            cross_reference_list = sql_session.query( ProteinCrossReference).filter( ProteinCrossReference.protein_id == protein.uniprotAC,
                                                                                     ProteinCrossReference.sourceDB == db_source,
                                                                                     ProteinCrossReference.crossReferenceID == cross_reference).all()
            if cross_reference_list != None and len( cross_reference_list) > 0:
                raise NotRequiredInstantiationException( "ProteinCrossReference.init : Cross Reference already present in database.")
            self.sourceDB = db_source
            self.crossReferenceID = cross_reference
            protein.add_cross_reference( self)
            sql_session.add( protein)
        # If several proteins are found with the accession number raise an issue
        # If no protein are found, raise a NotRequiredInstantiationException to indicate
        # the new ProteinCrossReference object do not have to be inserted in DB.
        else:
            if len( protein_list) > 1:
                raise RainetException( "ProteinCrossReference.init : Abnormal number of Protein found for accession number '" + protein_acc + "' : " + str( len( protein_list)) + " proteins found.")
            else:
                raise NotRequiredInstantiationException( "ProteinCrossReference.init : No Corresponding protein found in Database." )
    
    ##
    # Add the object to SQLAlchemy session if it is linked to a protein
    def add_to_session(self):
    
        if self.protein_id != None and self.protein_id != "":
            sql_session = SQLManager.get_instance().get_session()
            sql_session.add( self)
    
