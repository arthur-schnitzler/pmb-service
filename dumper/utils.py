import os
from django.conf import settings
from github import Github
from github import InputGitTreeElement


DOMAIN_MAPPING = [
    ("d-nb.info/gnd", "gnd"),
    ("geonames", "geonames"),
    ("wikidata", "wikidata"),
    ("fackel.oeaw.ac.at", "fackel"),
    ("schnitzler-tagebuch", "schnitzler-tagebuch"),
    ("schnitzler-bahr", "schnitzler-bahr"),
    ("schnitzler-briefe", "schnitzler-briefe"),
    ("schnitzler-lektueren", "schnitzler-lektueren"),
    ("doi.org/10.1553", "doi.org/10.1553"),
    ("kraus.wienbibliothek.at", "legalkraus"),
    ("kraus1933", "dritte-walpurgisnacht"),
    ("pmb.acdh.oeaw.ac.at", "pmb"),
]


def push_to_gh(
    files,
    ghpat=settings.GHPAT,
    repo_name=settings.GHREPO,
    branch="main",
    commit_message="some message"
):
    g = Github(ghpat)
    repo = g.get_repo(repo_name)
    master_ref = repo.get_git_ref(f'heads/{branch}')
    master_sha = master_ref.object.sha
    base_tree = repo.get_git_tree(master_sha)
    element_list = list()
    for entry in files:
        _, file_name = os.path.split(entry)
        with open(entry) as input_file:
            data = input_file.read()
        element = InputGitTreeElement(f"indices/{file_name}", '100644', 'blob', data)
        element_list.append(element)
    tree = repo.create_git_tree(element_list, base_tree)
    parent = repo.get_git_commit(master_sha)
    commit = repo.create_git_commit(commit_message, tree, [parent])
    master_ref.edit(commit.sha)
