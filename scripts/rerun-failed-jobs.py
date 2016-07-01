#!/usr/bin/env python2

import click
import csv
import subprocess
import tempfile


@click.command()
@click.option('--dry-run', default=False, is_flag=True, help='Set this flag to safely try out a set of parameters without actually re-running the jobs')
@click.option('--list-only', default=False, is_flag=True, help='Only fetch the list of filesets on which the job failed and save it to a temporary file.')
@click.option('--job')
def main(dry_run, job, list_only):
    """
    This script fetches a list of filesets, on which the given job failed,
    from a local bagbunker instance and re-runs the job on them.
    It needs to be run from within the bagbunker docker container.
    """
    # fetch the list of failed filesets and safe it to a file
    tmp_filename = tempfile._get_default_tempdir() + '/' + next(tempfile._get_candidate_names())
    print 'getting the list of filesets where the job "%s" failed; writing the results to %s' % (job, tmp_filename)
    subprocess.check_call(['psql', '-c', "\copy (SELECT fileset.md5,fileset.name from fileset,jobrun where fileset.id=jobrun.fileset_id and jobrun.failed=true and jobrun.name='%s') to %s with CSV" % (job, tmp_filename)])
    if list_only:
        return
    # parse results
    with open(tmp_filename, 'r') as input_file:
        infile_csv = csv.reader(input_file, delimiter=',')
        rows = list(infile_csv)
    row_count = len(rows)
    if row_count == 0:
        print 'No failed jobruns found for job %s' % job
        return
    # re-run jobs
    for (i, row) in list(enumerate(rows)):
        md5sum = row[0]
        print '%i/%i running %s for %s' % (i, row_count - 1, job, md5sum)
        cmd = ['bagbunker', 'run-jobs', '--fileset', md5sum,
               '--job', job, '--force']
        print 'running command: %s', cmd
        if not dry_run:
            subprocess.check_call(cmd)


if __name__ == '__main__':
    main()
