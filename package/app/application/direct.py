from babelfish import Language
from configobj import ConfigObj
from datetime import timedelta
from db import *
from pyextdirect.configuration import (create_configuration, expose, LOAD,
    STORE_READ, STORE_CUD, SUBMIT)
from validate import Validator
import os
import shutil
import subliminal
import subprocess
import tempfile
import logging
from subliminal.cli import MutexLock
from subliminal import (__version__, region, provider_manager, Video, Episode, Movie, scan_videos,
    download_best_subtitles, save_subtitles)
    
__all__ = ['Base', 'Directories', 'Subliminal']

base_path = '/var/packages/subliminal/target'
config_path = base_path + '/var/config.ini'
scanner_file = base_path + '/app/scanner.py'
configspec_file = base_path + '/app/application/config.spec'
cachefile_file = base_path + '/cache/cachefile.dbm'

Base = create_configuration()


class Directories(Base):
    def __init__(self):
        self.session = Session()

    @expose(kind=STORE_CUD)
    def create(self, data):
        results = []
        for record in data:
            directory = Directory(name=record['name'], path=record['path'])
            self.session.add(directory)
            self.session.commit()
            results.append({'id': directory.id, 'name': directory.name, 'path': directory.path})
        return results

    @expose(kind=STORE_READ)
    def read(self):
        results = []
        for directory in self.session.query(Directory).all():
            results.append({'id': directory.id, 'name': directory.name, 'path': directory.path})
        return results

    @expose(kind=STORE_CUD)
    def update(self, data):
        results = []
        for record in data:
            directory = self.session.query(Directory).get(record['id'])
            directory.name = record['name']
            directory.path = record['path']
            results.append({'id': directory.id, 'name': directory.name, 'path': directory.path})
        self.session.commit()
        return results

    @expose(kind=STORE_CUD)
    def destroy(self, data):
        results = []
        for directory_id in data:
            directory = self.session.query(Directory).get(directory_id)
            self.session.delete(directory)
            results.append(directory.id)
        self.session.commit()
        return results

    @expose
    def scan(self, directory_id):
        with open(os.devnull, 'w') as devnull:
            subprocess.call([scanner_file, str(directory_id)], stdin=devnull, stdout=devnull, stderr=devnull)


class Subliminal(Base):

    def __init__(self):
        self.session = Session()
        self.config = ConfigObj(config_path, configspec=configspec_file, encoding='utf-8', stringify=True, write_empty_values=True)
        self.config_validator = Validator()
        self.config.validate(self.config_validator)

    def setup(self):
        self.config.validate(self.config_validator, copy=True)
        self.config.write()

    @expose(kind=LOAD)
    def load(self):
        result = {'languages': self.config['General']['languages'], 'providers': self.config['General']['providers'],
                  'single': self.config['General']['single'], 'hearing_impaired': self.config['General']['hearing_impaired'],
                  'min_score': self.config['General']['min_score'], 'dsm_notifications': self.config['General']['dsm_notifications'],
				  'opensubtitles_user': self.config['opensubtitles']['username'],'opensubtitles_pass': self.config['opensubtitles']['password'],
				  'addic7ed_user': self.config['addic7ed']['username'],'addic7ed_pass': self.config['addic7ed']['password'],
				  'legendastv_user': self.config['legendastv']['username'],'legendastv_pass': self.config['legendastv']['password'],
				  'subscenter_user': self.config['subscenter']['username'],'subscenter_pass': self.config['subscenter']['password'],
                  'task': self.config['Task']['enable'], 'age': self.config['Task']['age'],
                  'hour': self.config['Task']['hour'], 'minute': self.config['Task']['minute']}
        return result

    @expose(kind=SUBMIT)
    def save(self, languages=None, providers=None, single=None, hearing_impaired=None, min_score=None, dsm_notifications=None, task=None, age=None, hour=None, minute=None,
			 opensubtitles_user=None, opensubtitles_pass=None, addic7ed_user=None, addic7ed_pass=None, legendastv_user=None, legendastv_pass=None,
			 subscenter_user=None, subscenter_pass=None):
        self.config['General']['languages'] = languages if isinstance(languages, list) else [languages]
        self.config['General']['providers'] = providers if isinstance(providers, list) else [providers]
        self.config['General']['single'] = bool(single)
        self.config['General']['hearing_impaired'] = bool(hearing_impaired)
        self.config['General']['min_score'] = int(min_score)
        self.config['General']['dsm_notifications'] = bool(dsm_notifications)
        self.config['opensubtitles']['username'] = opensubtitles_user
        self.config['opensubtitles']['password'] = opensubtitles_pass
        self.config['addic7ed']['username'] = addic7ed_user
        self.config['addic7ed']['password'] = addic7ed_pass
        self.config['legendastv']['username'] = legendastv_user
        self.config['legendastv']['password'] = legendastv_pass
        self.config['subscenter']['username'] = subscenter_user
        self.config['subscenter']['password'] = subscenter_pass
        self.config['Task']['enable'] = bool(task)
        self.config['Task']['age'] = int(age)
        self.config['Task']['hour'] = int(hour)
        self.config['Task']['minute'] = int(minute)
        if not self.config.validate(self.config_validator):
            return
        self.config.write()

    def scan(self):
        logging.debug('Direct scan')
        paths = [directory.path for directory in self.session.query(Directory).all() if os.path.exists(directory.path)]
        if not paths:
            return
        logging.debug(paths)
        results = []
        for path in paths:
            results.append(scan(path, self.config))
    
        if self.config['General']['dsm_notifications']:
            notify('Downloaded %d subtitle(s) for %d video(s) in all directories' % (sum([len(s) for s in results.itervalues()]), len(results)))
        return results

def scanme(paths, config):
    logging.info('scanme: %s' % paths)
    # configure cache
    region.configure('dogpile.cache.dbm', expiration_time=timedelta(days=30),  # @UndefinedVariable
                           arguments={'filename': cachefile_file, 'lock_factory': MutexLock})

    # scan videos
    #videos = scan_videos([p for p in paths if os.path.exists(p)],# subtitles=True,
    #                     embedded_subtitles=True, age=timedelta(days=config.get('Task').as_int('age')))
    videos = scan_videos(paths, age=timedelta(days=config.get('Task').as_int('age')))

    logging.info(videos)
    # guess videos
    videos.extend([Video.fromname(p) for p in paths  if not os.path.exists(p)])
    logging.info(videos)

    # download best subtitles
    languageset=set(Language(language) for language in config['General']['languages'])
    single=True
    if not config.get('General').as_bool('single') or len(languageset) > 1:
        single=False
    hearing_impaired=False
    if config.get('General').as_bool('hearing_impaired'):
        hearing_impaired=True
    providers = config['General']['providers']
    rv = {}
    for provider in providers:
        sec = config.get(provider)
        if sec != None:
            rv[provider] = {k: v for k, v in config.get(provider).items()}
    
    subtitles = download_best_subtitles(videos, languageset, min_score=config.get('General').as_int('min_score'),
                                        providers=providers, provider_configs=rv,
                                        hearing_impaired=hearing_impaired, only_one=single)

    # save them to disk, next to the video
    for v in videos:
        save_subtitles(v, subtitles[v])

    logging.debug(subtitles)
    logging.info('Scan Done!')  
    return subtitles

def scan(path, config):
    # configure cache
    region.configure('dogpile.cache.dbm', expiration_time=timedelta(days=30),  # @UndefinedVariable
			replace_existing_backend=True,
			arguments={'filename': cachefile_file, 'lock_factory': MutexLock})

    # scan videos
    #videos = scan_videos([p for p in [ paths ] if os.path.exists(p)], age=timedelta(days=config.get('Task').as_int('age')))
    videos = scan_videos(path, age=timedelta(days=config.get('Task').as_int('age')))

    # guess videos
    #videos.extend(Video.fromname(path) if not os.path.exists(p))

    # download best subtitles
    languageset=set(Language(language) for language in config['General']['languages'])
    single=True
    if not config.get('General').as_bool('single') or len(languageset) > 1:
        single=False
    hearing_impaired=False
    if config.get('General').as_bool('hearing_impaired'):
        hearing_impaired=True
    providers = config['General']['providers']
    rv = {}
    for provider in providers:
        sec = config.get(provider)
        if sec != None:
            rv[provider] = {k: v for k, v in config.get(provider).items()}

    subtitles = download_best_subtitles(videos, languageset, min_score=config.get('General').as_int('min_score'),
                                        providers=providers, provider_configs=rv,
                                        hearing_impaired=hearing_impaired, only_one=single)

    # save them to disk, next to the video
    for v in videos:
        save_subtitles(v, subtitles[v])

    logging.debug(subtitles)
    logging.info('Scan Done!')  
    return subtitles

def notify(message):
    with open(os.devnull, 'w') as devnull:
        subprocess.call(['synodsmnotify', '@administrators', 'Subliminal', message], stdin=devnull, stdout=devnull, stderr=devnull)
