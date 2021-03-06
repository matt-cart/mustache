import warnings
warnings.filterwarnings("ignore")
import click

from mustache.findflanks import _findflanks
from mustache.pairflanks import _pairflanks
from mustache.extendpairs import _extendpairs
from mustache.inferseqassembly import _inferseq_assembly
from mustache.inferseqoverlap import _inferseq_overlap
from mustache.inferseqreference import _inferseq_reference
from mustache.inferseqdatabase import _inferseq_database
from mustache.formatbam import _formatbam
from mustache.recall import _recall
from mustache.help import CustomHelp

import pygogo as gogo
from os.path import isfile
from os.path import basename, dirname
from os import makedirs

verbose=True
logger = gogo.Gogo(__name__, verbose=verbose).logger


@click.group(cls=CustomHelp)
def cli():
    """Command-line tools to identify mobile element insertions from short-read sequencing data."""
    pass

@cli.command(short_help='Find insertion sites and reconstruct flanks of inserted sequence', help_priority=1)
@click.argument('bamfile', type=click.Path(exists=True))
@click.option('--output_file', '-o', default='mustache.findflanks.tsv', help="The output file to save the results. default=mustache.findflanks.tsv")
@click.option('--min_softclip_count', '-mincount', default=4, help="For a softclipped site to be considered, there must be at least this many softclipped reads at the site. default=4")
@click.option('--min_alignment_quality', '-minq', default=20, help="For a read to be considered, it must meet this alignment quality cutoff. default=20")
@click.option('--min_alignment_inner_length', '-minial', default=21, help="If a read is softclipped on both ends, the aligned portion must be at least this long. Ideally, set this equal to 1 + max_direct_repeat_length. default=21")
@click.option('--min_distance_to_mate', '-mindist', default=22, help="A minimum distance to a potential nearby mate, filters out sites that have no pairs. default=22")
@click.option('--min_softclip_ratio', '-minratio', default=0.15, help="For a softclipped site to be considered, the proportion of softclipped sites must not fall below this value. default=0.15")
@click.option('--max_indel_ratio', '-maxir', default=0.03, help="For a softclipped site to be considered, the proportion of small insertions/deletions at this site must not be above this value. default=0.03")
@click.option('--min_count_consensus', '-mcc', default=2, help="When building the consensus sequence, stop building consensus if read count drops below this cutoff. default=2")
@click.option('--min_softclip_length', '-minlen', default=8, help="For a softclipped site to be considered, there must be at least one softclipped read of this length. default=8")
def findflanks(bamfile, min_softclip_length, min_softclip_count, min_alignment_quality, min_alignment_inner_length,
               min_distance_to_mate, min_softclip_ratio, max_indel_ratio, min_count_consensus, output_file):
    """A click access point for the findflanks module. This is used for creating the command line interface."""

    _findflanks(bamfile, min_softclip_length, min_softclip_count, min_alignment_quality, min_alignment_inner_length,
                min_distance_to_mate, min_softclip_ratio, max_indel_ratio, min_count_consensus, output_file)


@cli.command(short_help="Pair identified flanks with each other to represent 5' and 3' ends of inserted sequence.", help_priority=2)
@click.argument('flanksfile', type=click.Path(exists=True))
@click.argument('bamfile', type=click.Path(exists=True))
@click.argument('genome', type=click.Path(exists=True))
@click.option('--max_direct_repeat_length', '-maxdr', default=20, help="The maximum length of a direct repeat to consider a pair. default=20")
@click.option('--min_alignment_quality', '-minq', default=20, help="For a read to be considered, it must meet this alignment quality cutoff. default=20")
@click.option('--min_alignment_inner_length', '-minial', default=21, help="If a read is softclipped on both ends, the aligned portion must be at least this long. Ideally, set this equal to 1 + maximum direct repeat length. default=21")
@click.option('--max_junction_spanning_prop', '-maxjsp', default=0.15, help="Removes pairs where this proportion of readsextend across both insertion junctions without softclipping, an indication that the site is a duplicated region. default=0.15")
@click.option('--output_file', '-o', default='mustache.pairflanks.tsv', help="The output file to save the results. default=mustache.pairflanks.tsv")
def pairflanks(flanksfile, bamfile, genome, max_direct_repeat_length, min_alignment_quality,
               min_alignment_inner_length, max_junction_spanning_prop, output_file=None):
    _pairflanks(flanksfile, bamfile, genome, max_direct_repeat_length, min_alignment_quality,
                min_alignment_inner_length, max_junction_spanning_prop, output_file)


@cli.command(help_priority=3)
@click.argument('pairsfile', type=click.Path(exists=True))
@click.argument('bamfile', type=click.Path(exists=True))
@click.option('--threads', '-t', default=1, help="The number of processors to run while finding flank extensions. default=1")
@click.option('--output_file', '-o', default='mustache.extendpairs.tsv', help="The output file to save the results. default=mustache.extendpairs.tsv")
def extendpairs(pairsfile, bamfile, threads, output_file=None):
    """
    Experimental. Extends the consensus flanks using a local assembly of paired end reads.
    BAM file must be processed using the 'formatbam' command first.
    Requires an installation of the AMOS sequence assembly software: http://amos.sourceforge.net/wiki/index.php/AMOS
    """
    _extendpairs(pairsfile, bamfile, threads, output_file)


@cli.command(short_help='Infers the identity of an inserted sequence by aligning flank pairs to an assembled genome.', help_priority=4)
@click.argument('pairsfile', type=click.Path(exists=True))
@click.argument('bamfile', type=click.Path(exists=True))
@click.argument('inferseq_assembly', type=click.Path(exists=True))
@click.argument('inferseq_reference', type=click.Path(exists=True))
@click.option('--min_perc_identity', '-minident', default=0.95, help="Only consider matches with a percentage identity above this threshold. default=0.95")
@click.option('--max_internal_softclip_prop', '-maxclip', default=0.05, help="Do not consider matches with internal softclipped ends exceeding this proportion of the total read. default=0.05")
@click.option('--max_inferseq_size', '-maxsize', default=500000, help="Do not consider inferred sequences over this size. default=500000")
@click.option('--min_inferseq_size', '-minsize', default=1, help="Do not consider inferred sequences below this size. default=1")
@click.option('--keep-intermediate/--no-keep-intermediate', default=False, help="Keep intermediate files. default=False")
@click.option('--output_file', '-o', default='mustache.inferseq_assembly.tsv', help="The output file to save the results. default=mustache.inferseq_assembly.tsv")
def inferseq_assembly(pairsfile, bamfile, inferseq_assembly, inferseq_reference, min_perc_identity,
                      max_internal_softclip_prop, max_inferseq_size, min_inferseq_size, keep_intermediate, output_file=None):
    """Infers the identity of an inserted sequence by aligning flank pairs to an assembled genome."""

    _inferseq_assembly(pairsfile, bamfile, inferseq_assembly, inferseq_reference, min_perc_identity,
                       max_internal_softclip_prop, max_inferseq_size, min_inferseq_size, keep_intermediate, output_file)


@cli.command(short_help='Infers the identity of an inserted sequence by aligning flank pairs to a reference genome. Ideal for re-sequencing experiments where evolved strains are closely related to the reference genome used.',
             help_priority = 5)
@click.argument('pairsfile', type=click.Path(exists=True))
@click.argument('inferseq_reference', type=click.Path(exists=True))
@click.option('--min_perc_identity', '-minident', default=0.95, help="Only consider matches with a percentage identity above this threshold. default=0.95")
@click.option('--max_internal_softclip_prop', '-maxclip', default=0.05, help="Do not consider matches with internal softclipped ends exceeding this proportion of the total read. default=0.05")
@click.option('--max_inferseq_size', '-maxsize', default=500000, help="Do not consider inferred sequences over this size. default=500000")
@click.option('--min_inferseq_size', '-minsize', default=1, help="Do not consider inferred sequences below this size. default=1")
@click.option('--output_file', '-o', default='mustache.inferseq_database.tsv', help="The output file to save the results. default=mustache.inferseq_database.tsv")
@click.option('--keep-intermediate/--no-keep-intermediate', default=False, help="Keep intermediate files. default=False")
@click.option('--output_file', '-o', default='mustache.inferseq_reference.tsv', help="The output file to save the results. default=mustache.inferseq_reference.tsv")
def inferseq_reference(pairsfile, inferseq_reference, min_perc_identity, max_internal_softclip_prop,
                       max_inferseq_size, min_inferseq_size, keep_intermediate, output_file=None):
    """
    Infers the identity of an inserted sequence by aligning flank pairs to a reference genome.
    Ideal for re-sequencing experiments where evolved strains are closely related to the reference genome used.
    """

    _inferseq_reference(pairsfile, inferseq_reference, min_perc_identity, max_internal_softclip_prop,
                        max_inferseq_size, min_inferseq_size, keep_intermediate, output_file)


@cli.command(short_help='Infers the identity of an inserted sequence by checking if they overlap with one another. Only identifies an inserted sequence if the consensus flanks are long enough to span the entire insertion.',
             help_priority=6)
@click.argument('pairsfile', type=click.Path(exists=True))
@click.option('--min_overlap_score', '-minscore', default=10, help="The minimum overlap score to keep inferred sequence. default=10")
@click.option('--min_overlap_perc_identity', '-minopi', default=0.9, help="The minimum overlap percent identity to keep inferred sequence. default=0.9")
@click.option('--output_file', '-o', default='mustache.inferseq_overlap.tsv', help="The output file to save the results. default=mustache.inferseq_overlap.tsv")
def inferseq_overlap(pairsfile, min_overlap_score, min_overlap_perc_identity, output_file=None):
    """
    Infers the identity of an inserted sequence by checking if they overlap with one another.
    Only identifies an inserted sequence if the consensus flanks are long enough to span the entire insertion.
    """

    _inferseq_overlap(pairsfile, min_overlap_score, min_overlap_perc_identity, output_file)


@cli.command(short_help='Infers the identity of an inserted sequence by aligning flank pairs to an database of known inserted elements.', help_priority=7)
@click.argument('pairsfile', type=click.Path(exists=True))
@click.argument('inferseq_database', type=click.Path(exists=True))
@click.option('--min_perc_identity', '-minident', default=0.90, help="Only consider matches with a percentage identity above this threshold. default=0.90")
@click.option('--max_internal_softclip_prop', '-maxclip', default=0.05, help="Do not consider matches with internal softclipped ends exceeding this proportion of the total read. default=0.05")
@click.option('--max_edge_distance', '-maxedgedist', default=10, help="Reads must align within this number of bases from the edge of an element to be considered. default=10")
@click.option('--output_file', '-o', default='mustache.inferseq_database.tsv', help="The output file to save the results. default=mustache.inferseq_database.tsv")
@click.option('--keep-intermediate/--no-keep-intermediate', default=False, help="Keep intermediate files. default=False")
def inferseq_database(pairsfile, inferseq_database, min_perc_identity,  max_internal_softclip_prop, max_edge_distance, output_file=None, keep_intermediate=False):
    """Infers the identity of an inserted sequence by aligning flank pairs to an database of known inserted elements."""

    _inferseq_database(pairsfile, inferseq_database, min_perc_identity, max_internal_softclip_prop, max_edge_distance, output_file, keep_intermediate)


@cli.command(short_help="Formats a BAM file for use with mustache. Usually not necessary, unless using the experiment extendpairs command.", help_priority=8)
@click.argument('in_sam', type=click.Path(exists=True))
@click.argument('out_bam')
@click.option('--single-end', is_flag=True, default=False, help="Add this flag for single-end files. default=False")
@click.option('--keep-tmp-files', is_flag=True, default=False, help="Add this flag if you want to keep intermediate temporary files. default=False")
def formatbam(in_sam, out_bam, single_end, keep_tmp_files):

    _formatbam(in_sam, out_bam, single_end, keep_tmp_files)



@cli.command(short_help='Recall softclip counts and runthrough counts from BAM file at specified pairflank insertions.', help_priority=9)
@click.argument('pairsfile', type=click.Path(exists=True))
@click.argument('bamfile', type=click.Path(exists=True))
@click.option('--min_alignment_quality', '-minq', default=20, help="For a read to be considered, it must meet this alignment quality cutoff. default=20")
@click.option('--min_alignment_inner_length', '-minial', default=21, help="If a read is softclipped on both ends, the aligned portion must be at least this long. Ideally, set this equal to 1 + maximum direct repeat length. default=21")
@click.option('--output_file', '-o', default='mustache.recall.tsv', help="The output file to save results to. default=mustache.recall.tsv")
def recall(pairsfile, bamfile, min_alignment_quality, min_alignment_inner_length, output_file):
    _recall(pairsfile, bamfile, min_alignment_quality, min_alignment_inner_length, output_file)


if __name__ == '__main__':

    cli()