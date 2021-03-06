from sqlalchemy import Column, String
from sqlalchemy.sql.schema import ForeignKey, PrimaryKeyConstraint

from fr.tagc.rainet.core.util.sql.Base import Base


##
# This class describes a Network Module (a group of interacting proteins)
# as produced by a network partition analysis like OCG
class NetworkModuleAnnotation ( Base ):
    __tablename__ = "NetworkModuleAnnotation"
    
    # The module ID
    networkModule_id = Column( String, ForeignKey('NetworkModule.moduleID') )
    # The annotation GOID
    annotationID = Column( String )
    # The annotation name
    annotationTerm = Column( String )

    # Define the Composite PrimaryKey
    __table_args__ = (
        PrimaryKeyConstraint('networkModule_id', 'annotationID'),
    )
    
    #
    ## The constructor
    def __init__(self, annotation_term, annotation_id):
        
        self.annotationName = annotation_term
        self.annotationID = annotation_id
