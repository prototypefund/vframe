"""
Parallel rsync media_records between drives
For parallel rsync with media records, use vframe/commands/rsync
"""

import click

from vframe.settings import types
from vframe.utils import click_utils
from vframe.settings import vframe_cfg as cfg

@click.command()
@click.option('-i', '--input', 'dir_in', required=True,
  help='Input directory')
@click.option('-o', '--output', 'dir_out', required=True,
  help='Output directory')
@click.option('-t', '--threads', 'opt_threads', default=8,
  help='Number of threads')
@click.option('--validate/--no-validate', 'opt_validate', is_flag=True, default=False,
  help='Validate files after copy')
@click.option('--extract/--no-extract', 'opt_extract', is_flag=True, default=False,
  help='Extract files after copy')
@click.pass_context
def cli(ctx, dir_in, dir_out, opt_threads, opt_validate, opt_extract):
  """rsync folders"""
  
  import os
  from os.path import join
  from pathlib import Path

  # NB deactivate logger in imported module
  import logging
  logging.getLogger().addHandler(logging.NullHandler())
  from parallel_sync import rsync
  
  from vframe.settings.paths import Paths
  from vframe.utils import logger_utils, file_utils
  
  # -------------------------------------------------
  # process here

  log = logger_utils.Logger.getLogger()
  log.info('RSYNC from {} to {}'.format(dir_in, dir_out))  
  log.info('opt_extract: {}'.format(opt_extract))
  log.info('opt_validate: {}'.format(opt_validate))
  log.info('opt_threads: {}'.format(opt_validate))
  
  file_utils.mkdirs(dir_out)

  rsync.copy(dir_in, dir_out, parallelism=opt_threads, 
    validate=opt_validate, extract=opt_extract)

  log.info('done rsyncing')


  # ---------------------------------------------------------------



  # if dir_in:
  #   # use input filepath as source
  #   if not Path(dir_in).is_dir():
  #     log.error('{} is not a directory'.format(dir_in))
  #     ctx.exit()
  #   if not Path(dir_out).is_dir():
  #     ctx.log.error('{} is not a directory'.format(dir_out))
  #     return

  #   log.info('RSYNC from {} to {}'.format(dir_in, dir_out))
  #   log.debug('opt_validate: {}'.format(opt_validate))
  #   log.debug('opt_extract: {}'.format(opt_extract))
  #   #  local_copy(paths, parallelism=10, extract=False, validate=False):
  #   file_utils.mkdirs(dir_out)
  #   rsync.copy(dir_in, dir_out, parallelism=opt_threads, 
  #     validate=opt_validate, extract=opt_extract)
  # else:
  #   log.debug('get paths')
  #   # use source mappings as rsync source
  #   if not opt_media_format:
  #     ctx.log.error('--media format not supplied for source mappings')
  #     return

  #   # ensure FILEPATH metadata exists
  #   #  parallel-rsync accepts a list of tupes (src, dst)
  #   file_routes = []
  #   for chair_item in chair_items:
  #     item = chair_item.item
  #     sha256 = chair_item.item.sha256
  #     filepath_metadata = item.get_metadata(types.Metadata.FILEPATH)
  #     if not filepath_metadata:
  #       ctx.log.error('no FILEPATH metadata')
  #       return
  #     fp_media = 
  #     src = join('')
  #     dir_media = Paths.media_dir(opt_media_format, data_store=opt_disk, verified=ctx.opts['verified'])
  #     dst = join('')
  #     file_routes.append((src, dst))

  #   ctx.log.debug('dir_media: {}'.format(dir_media))
  #   return
    
  # # -------------------------------------------------

  # # send back to sink
  # for chair_item in chair_items:
  #   sink.send(chair_item)
