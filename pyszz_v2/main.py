# Modified by The Authors on July 2026 to adapt for the replication package.

import argparse
import json
import logging as log
import os
from time import time as ts

import dateparser
import yaml
from typing import Dict
from szz.ag_szz import AGSZZ
from szz.aszz.a_szz import ASZZ
from szz.b_szz import BaseSZZ
from szz.util.check_requirements import check_requirements
from szz.dfszz.df_szz import DFSZZ
from szz.l_szz import LSZZ
from szz.ma_szz import MASZZ, DetectLineMoved
from szz.r_szz import RSZZ
from szz.ra_szz import RASZZ
from szz.pd_szz import PyDrillerSZZ
from szz.common.issue_date import parse_issue_date
from pathlib import Path
import random

log.basicConfig(level=log.INFO, format='%(asctime)s :: %(funcName)s - %(levelname)s :: %(message)s')
log.getLogger('pydriller').setLevel(log.WARNING)


TIME_LIMIT = 5 * 3600 + 20 * 60  # 5 hours + 20 minutes

def is_empty_or_dash(value):
    if value is None or value == "-":
        return True
    if isinstance(value, (list, set, tuple, dict)) and len(value) == 0:
        return True
    return False

def normalize_szz_result(result):
    if result == '-':
        return '-'
    if result is None:
        return None

    try:
        return [bic.hexsha for bic in result if bic]
    except Exception:
        return result

def define_bic(rszz, pdszz):
    if not is_empty_or_dash(rszz):
        method_type = "rszz"
        bic = rszz
    elif not is_empty_or_dash(pdszz):
        method_type = "pdszz"
        bic = pdszz
    else:
        method_type = "none"
        bic = []

    return bic, method_type

def main(input_json: str, out_json: str, conf: Dict, repos_dir: str):

    start_time = ts()

    with open(input_json, 'r') as in_file:
        bugfix_commits = json.loads(in_file.read())

    def run_szz(szz_name, repo_name, repo_url, fix_commit, conf, issue_date, repos_dir):
        # returns '-' for skipped, None for not found, or a list/iterable of commit objects/strings
        if szz_name == 'b':
            b_szz = BaseSZZ(repo_full_name=repo_name, repo_url=repo_url, repos_dir=repos_dir)
            imp_files = b_szz.get_impacted_files(fix_commit_hash=fix_commit, file_ext_to_parse=conf.get('file_ext_to_parse'), only_deleted_lines=True)
            return b_szz.find_bic(fix_commit_hash=fix_commit,
                                        impacted_files=imp_files,
                                        issue_date_filter=conf.get('issue_date_filter'),
                                        issue_date=issue_date)
        elif szz_name == 'ag':
            ag_szz = AGSZZ(repo_full_name=repo_name, repo_url=repo_url, repos_dir=repos_dir)
            imp_files = ag_szz.get_impacted_files(fix_commit_hash=fix_commit, file_ext_to_parse=conf.get('file_ext_to_parse'), only_deleted_lines=True)
            return ag_szz.find_bic(fix_commit_hash=fix_commit,
                                        impacted_files=imp_files,
                                        max_change_size=conf.get('max_change_size'),
                                        issue_date_filter=conf.get('issue_date_filter'),
                                        issue_date=issue_date)
        elif szz_name == 'ma':
            ma_szz = MASZZ(repo_full_name=repo_name, repo_url=repo_url, repos_dir=repos_dir)
            imp_files = ma_szz.get_impacted_files(fix_commit_hash=fix_commit, file_ext_to_parse=conf.get('file_ext_to_parse'), only_deleted_lines=True)
            return ma_szz.find_bic(fix_commit_hash=fix_commit,
                                        impacted_files=imp_files,
                                        max_change_size=conf.get('max_change_size'),
                                        detect_move_from_other_files=DetectLineMoved(conf.get('detect_move_from_other_files')),
                                        issue_date_filter=conf.get('issue_date_filter'),
                                        issue_date=issue_date,
                                        filter_revert_commits=conf.get('filter_revert_commits', False))
        elif szz_name == 'r':
            r_szz = RSZZ(repo_full_name=repo_name, repo_url=repo_url, repos_dir=repos_dir)
            imp_files = r_szz.get_impacted_files(fix_commit_hash=fix_commit, file_ext_to_parse=conf.get('file_ext_to_parse'), only_deleted_lines=True)
            if imp_files == "-":
                return '-'
            else:
                return r_szz.find_bic(fix_commit_hash=fix_commit,
                                        impacted_files=imp_files,
                                        max_change_size=conf.get('max_change_size'),
                                        detect_move_from_other_files=DetectLineMoved(conf.get('detect_move_from_other_files')),
                                        issue_date_filter=conf.get('issue_date_filter'),
                                        issue_date=issue_date,
                                        filter_revert_commits=conf.get('filter_revert_commits', False))
        elif szz_name == 'l':
            l_szz = LSZZ(repo_full_name=repo_name, repo_url=repo_url, repos_dir=repos_dir)
            imp_files = l_szz.get_impacted_files(fix_commit_hash=fix_commit, file_ext_to_parse=conf.get('file_ext_to_parse'), only_deleted_lines=True)
            return l_szz.find_bic(fix_commit_hash=fix_commit,
                                        impacted_files=imp_files,
                                        max_change_size=conf.get('max_change_size'),
                                        detect_move_from_other_files=DetectLineMoved(conf.get('detect_move_from_other_files')),
                                        issue_date_filter=conf.get('issue_date_filter'),
                                        issue_date=issue_date,
                                        filter_revert_commits=conf.get('filter_revert_commits', False))
        elif szz_name == 'ra':
            ra_szz = RASZZ(repo_full_name=repo_name, repo_url=repo_url, repos_dir=repos_dir)
            imp_files = ra_szz.get_impacted_files(fix_commit_hash=fix_commit, file_ext_to_parse=conf.get('file_ext_to_parse'), only_deleted_lines=True)
            return ra_szz.find_bic(fix_commit_hash=fix_commit,
                                        impacted_files=imp_files,
                                        max_change_size=conf.get('max_change_size'),
                                        detect_move_from_other_files=DetectLineMoved(conf.get('detect_move_from_other_files')),
                                        issue_date_filter=conf.get('issue_date_filter'),
                                        issue_date=issue_date,
                                        filter_revert_commits=conf.get('filter_revert_commits', False))
        elif szz_name == 'pd':
            pd_szz = PyDrillerSZZ(repo_full_name=repo_name, repo_url=repo_url, repos_dir=repos_dir)
            imp_files = pd_szz.get_impacted_files(fix_commit_hash=fix_commit, file_ext_to_parse=conf.get('file_ext_to_parse'), only_deleted_lines=True)
            return pd_szz.find_bic(fix_commit_hash=fix_commit,
                                                   impacted_files=imp_files,
                                                   issue_date_filter=conf.get('issue_date_filter'),
                                                   issue_date=issue_date)
        elif szz_name == 'a':
            a_szz = ASZZ(repo_full_name=repo_name, repo_url=repo_url, repos_dir=repos_dir)
            return a_szz.start(fix_commit_hash=fix_commit, commit_issue_date=issue_date, **conf)
        elif szz_name == 'df':
            df_szz = DFSZZ(repo_full_name=repo_name, repo_url=repo_url, repos_dir=repos_dir)
            return df_szz.start(fix_commit_hash=fix_commit, commit_issue_date=issue_date, **conf)
        else:
            log.info(f'SZZ implementation not found: {szz_name}')
            return None

    tot = len(bugfix_commits)
    for i, commit in enumerate(bugfix_commits):

        # if ts() - start_time > TIME_LIMIT:
        #     break

        bug_inducing_commits = set()
        repo_name = commit['repo_name'].split('/')[-1]
        repo_url = f'https://test:test@github.com/{repo_name}.git'  # using test:test as git login to skip private repos during clone
        fix_commit = commit['fix_commit_hash']

        log.info(f'{i + 1} of {tot}: {repo_name} {fix_commit}')
        
        issue_date = None
        if conf.get('issue_date_filter', None):
            issue_date = parse_issue_date(commit)
        
        szz_names = conf.get('szz_name')
        r_result = run_szz('r', repo_name, repo_url, fix_commit, conf, issue_date, repos_dir)
        log.info(f"result (r): {r_result}")
        r_bic = normalize_szz_result(r_result)
        if not is_empty_or_dash(r_bic):
            bugfix_commits[i]["bic"] = r_bic
            bugfix_commits[i]["method_type"] = "rszz"
        else:
            pd_result = run_szz('pd', repo_name, repo_url, fix_commit, conf, issue_date, repos_dir)
            log.info(f"result (pd): {pd_result}")
            pd_bic = normalize_szz_result(pd_result)
            if not is_empty_or_dash(pd_bic):
                bugfix_commits[i]["bic"] = pd_bic
                bugfix_commits[i]["method_type"] = "pdszz"
            else:
                bugfix_commits[i]["bic"] = []
                bugfix_commits[i]["method_type"] = "none"


    with open(out_json, 'w') as out:
        json.dump(bugfix_commits, out, indent=4)

    log.info(f"results saved in {out_json}")
    log.info("+++ DONE +++")

    current_time = ts()
    elapsed_time = current_time - start_time
    log.info(f"Elapsed time: {elapsed_time/60:.2f} minutes") 


if __name__ == "__main__":
    check_requirements()

    parser = argparse.ArgumentParser(description='USAGE: python main.py <bugfix_commits.json> <conf_file path> <repos_directory(optional)>\n* If <repos_directory> is not set, pyszz will download each repository')
    parser.add_argument('input_json', type=str, help='/path/to/bug-fixes.json')
    parser.add_argument('conf_file', type=str, help='/path/to/configuration-file.yml')
    parser.add_argument('repos_dir', type=str, nargs='?', help='/path/to/repo-directory')
    
    args = parser.parse_args()

    if not os.path.isfile(args.input_json):
        print(args.input_json)
        os.system("pwd")
        log.error('invalid input json')
        exit(-2)
    if not os.path.isfile(args.conf_file):
        log.error('invalid conf file')
        exit(-2)

    with open(args.conf_file, 'r') as f:
        conf = yaml.safe_load(f)

    log.info(f"parsed conf yml '{args.conf_file}': {conf}")
    log.info(f"Arguments: {args}")
    szz_name = conf['szz_name']

    out_dir = 'out'
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    conf_file_name = Path(args.conf_file).name.split('.')[0]
    out_json = os.path.join(out_dir, args.input_json.split('/')[-1])

    if not szz_name:
        log.error('The configuration file does not define the SZZ name. Please, fix.')
        exit(-3)

    log.info(f'Launching {szz_name}-szz')

    main(args.input_json, out_json, conf, args.repos_dir)
