# RAINET project

RAINET: Towards the understanding of RNA-protein Interaction NETworks.

This project aims at identifying human long non-coding RNAs likely to scaffold protein complexes.

This github page contains the source code associated to the Ribeiro et al. 2017 Nucleic Acids Research publication entitled "Protein complex scaffolding predicted as a prevalent function of long non-coding RNAs".


## Description:

The main scripts for this project were coded in an object-oriented environment, creating and using a SQLite database to contain and associate information. Analysis leading to publication involved many separate analysis scripts, the main ones will be described here.

## Folder description:

- The 'src' directory contains our Python and R scripts. (main analysis scripts are on: /src/fr/tagc/rainet/core/execution)
- The 'test' directory contains Python unittests of main scripts.
- The 'resources' directory contains paths to input files used for main scripts.
- The 'documentation' directory contains the doxygen script documentation and the RAINET database schema.

## Pipeline description:

RAINET DB preparation:
- ReadCatrapid.py (process catRAPID software data (licenced))
- InsertionStrategy.py (for creating a RAINET database)
- AnalysisStrategy.py (for filtering / stats of RAINET database)
 
Enrichment analysis:
- EnrichmentAnalysisStategy.py (produces main RNA-complex enrichment results)
- FilterEnrichmentResults.py (for filtering / stats Enrichment analysis results)
- CommonLncRNAProteinDisease.py (for matching lncRNA and protein disease)

Other post-analysis:
- PrioritizeCandidates.py (for selecting enrichments with known interactions)
- LncRNAGroupOddsRatio.py (for evaluating overlap of groups of lncRNAs against functional lncRNAs)

## Supported OS and required software:

- Linux
- catRAPID omics (licenced software: http://s.tartaglialab.com/page/catrapid_group)
- Bash 4.3
- SQLite 2.8
- R v3.0.2
- Python 2.7
- python packages: sqlalchemy, pandas, numpy, igraph, pickle

