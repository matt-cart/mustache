import warnings
warnings.filterwarnings("ignore")
from mustache.sctools import *

def get_softclipped_seqs_qualities(bam_file, contig, pos, orient, min_alignment_quality):
    softclip_count = 0
    softclipped_seqs = []
    softclipped_qualities = []

    if orient == 'R':
        start, end = pos - 1, pos
        if start < 0:
            start = 0

    if orient == 'L':
        start, end = pos + 1, pos + 2

        if end > contig_length(bam_file, contig):
            end = contig_length(bam_file, contig)

    for pu in bam_file.pileup(contig, start, end, truncate=True):
        for pr in pu.pileups:
            read = pr.alignment

            if read.mapping_quality < min_alignment_quality:
                continue

            if orient == 'L':
                if is_left_softclipped_lenient_at_site(read, contig, pos):
                    softclip_count += 1
                    softclipped_seqs.append(left_softclipped_sequence(read))
                    softclipped_qualities.append(left_softclip_qualities(read))

            elif orient == 'R':
                if is_right_softclipped_lenient_at_site(read, contig, pos):
                    softclip_count += 1
                    softclipped_seqs.append(right_softclipped_sequence(read))
                    softclipped_qualities.append(right_softclip_qualities(read))

    if orient == 'L':
        softclipped_seqs = [seq[::-1] for seq in softclipped_seqs]
        softclipped_qualities = [qual[::-1] for qual in softclipped_qualities]

    return softclipped_seqs, softclipped_qualities

def get_left_softclipped_reads_at_site(bam_file, contig, left_site, softclip_only=False):
    left_softclipped_reads = []

    start = left_site + 1
    end = left_site + 2

    contig_len = contig_length(bam_file, contig)
    if end > contig_len:
        end = contig_len

    for pu in bam_file.pileup(contig, start, end, truncate=True):

        for pr in pu.pileups:
            read = pr.alignment
            if is_left_softclipped_lenient_at_site(read, contig, left_site):

                if softclip_only:
                    keep_seq = left_softclipped_sequence(read)
                else:
                    keep_seq = read.query_sequence
                left_softclipped_reads.append(keep_seq)

    return left_softclipped_reads


def get_right_softclipped_reads_at_site(bam_file, contig, right_site, softclip_only=False):
    right_softclipped_reads = []

    start = right_site - 1
    end = right_site

    if start < 0:
        start = 0

    for pu in bam_file.pileup(contig, start, end, truncate=True):

        for pr in pu.pileups:
            read = pr.alignment
            if is_right_softclipped_lenient_at_site(read, contig, right_site):
                if softclip_only:
                    keep_seq = right_softclipped_sequence(read)
                else:
                    keep_seq = read.query_sequence
                right_softclipped_reads.append(keep_seq)

    return right_softclipped_reads


def get_right_unmapped_reads(bam_file, contig, right_site, search_region_length=500):
    right_unmapped_reads = []

    start = right_site - search_region_length
    end = right_site

    if start < 0:
        start = 0

    for read in bam_file.fetch(contig, start, end):

        if (not read.is_reverse) and read.mate_is_unmapped:
            right_unmapped_reads.append(read.get_tag('MT'))

    return right_unmapped_reads


def get_left_unmapped_reads(bam_file, contig, left_site, search_region_length=500):
    left_unmapped_reads = []

    start = left_site + 1
    end = left_site + 1 + search_region_length

    contig_len = contig_length(bam_file, contig)
    if end > contig_len:
        end = contig_len

    for read in bam_file.fetch(contig, start, end):

        if read.is_reverse and read.mate_is_unmapped:
            left_unmapped_reads.append(read.get_tag('MT'))

    return left_unmapped_reads

def contig_length(bam, contig):
    return dict(zip(bam.references, bam.lengths))[contig]

def count_runthrough_reads(bam, contig, site):

    if site  < 0 or site >= contig_length(bam, contig):
        return 0
    else:
        count = 0
        for read in bam.fetch(contig, site, site+1):
            count += 1
        return count