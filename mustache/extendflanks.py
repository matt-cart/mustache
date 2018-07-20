import sys
import click
import pysam
import pygogo as gogo
import pandas as pd
import numpy as np
from snakemake import shell
from random import randint
from mustache import fastatools, embosstools, sctools, pysamtools, minimustools
from mustache.misc import revcomp

verbose=True
logger = gogo.Gogo(__name__, verbose=verbose).logger

def extend(bam, contig, pos, orient, seq):


    reads = get_reads_to_assemble(bam, contig, pos, orient)
    if len(reads) == 0:
        return None

    assembler = minimustools.MinimusAssembler(reads)
    assembler.assemble()

    if assembler.count_assembled_seqs() == 0:
        return None

    assembler.align_seq_to_assembly(seq)
    extended_seq = assembler.retrieve_extended_sequence(orient)
    assembler.delete_files()
    return extended_seq

def get_reads_to_assemble(bam, contig, pos, orient):

    if orient == 'R':
        softclipped_reads = pysamtools.get_right_softclipped_reads_at_site(bam, contig, pos)
        unmapped_reads = pysamtools.get_right_unmapped_reads(bam, contig, pos)
    elif orient == 'L':
        softclipped_reads = pysamtools.get_left_softclipped_reads_at_site(bam, contig, pos)
        unmapped_reads = pysamtools.get_left_unmapped_reads(bam, contig, pos)

    return softclipped_reads + unmapped_reads


def _extendflanks(flanksfile, bamfile, output_file):


    flanks = pd.read_csv(flanksfile, sep='\t')
    bam = pysam.AlignmentFile(bamfile, 'rb')

    sequences = list(flanks['consensus_seq'])
    did_extend = [False]*len(sequences)

    logger.info("Running extendflanks algorithm on %d total flanks..." % flanks.shape[0])

    count = 0
    for index, row in flanks.iterrows():

        count += 1
        if count % 100 == 0:
            logger.info("\tProcessed %d flanks so far, and extended %d total flanks..." % (count, sum(did_extend)))

        contig, pos, orient, seq = row[['contig', 'pos', 'orient', 'consensus_seq']]

        print(contig, pos, orient)

        extension = extend(bam, contig, pos, orient, seq)
        if extension:
            sequences[index] = str(extension)
            did_extend[index] = True

    flanks['consensus_seq'] = pd.DataFrame(sequences)
    flanks['extended'] = pd.DataFrame(did_extend)

    cols = flanks.columns.tolist()
    cols = cols[:-2] + [cols[-1]] + [cols[-2]]
    flanks = flanks[cols]

    logger.info("Extended %d flanks using local assembly..." % sum(did_extend))
    if output_file:
        logger.info("Saving results to file %s" % output_file)
        flanks.to_csv(output_file, sep='\t', index=False)

    return flanks


@click.command()
@click.argument('flanksfile', type=click.Path(exists=True))
@click.argument('bamfile', type=click.Path(exists=True))
@click.option('--output_file', '-o', default='mustache.extendflanks.tsv', help="The output file to save the results.")
def extendflanks(flanksfile, bamfile, output_file=None):
    _extendflanks(flanksfile, bamfile, output_file)


if __name__ == '__main__':
    extendflanks()
    #seqs = ['ACGCA', 'ACG', 'ACGC', 'ACGT', 'ACGTC', 'ACGTCA', 'ACGTCAT', 'ACGTCAG', 'ACGTCAT']
    #clusters = get_sequence_clusters(seqs)

    #mytrie = flanktrie.Trie()
    #for s in seqs:
    #    mytrie.add(s)

    #print(mytrie.traverse())
    #print(mytrie.calc_total_shared_words('ACGTCAG', 'ACGTCAT'))
    #print(mytrie.calc_total_unique_shared_words('ACGTCAG', 'ACGTCAT'))
    #print()

    #print(mytrie.traverse())
    #print("DELETING ACGTCAG")
    #mytrie.delete_word('ACG')
    #print(mytrie.traverse())